import {
  Injectable,
  UnauthorizedException,
  ConflictException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';
import { PrismaService } from '../prisma/prisma.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { serialize, pick } from '../common/helpers/serializer';

@Injectable()
export class AuthService {
  constructor(
    private prisma: PrismaService,
    private jwtService: JwtService,
  ) {}

  /**
   * Laravel uses $2y$ prefix, Node bcrypt uses $2a$/$2b$.
   * They are algorithmically identical — only the prefix differs.
   * Normalize to $2a$ so Node bcrypt can verify Laravel-hashed passwords.
   */
  private normalizeHashForVerify(hash: string): string {
    return hash.replace(/^\$2y\$/, '$2a$');
  }

  /**
   * After hashing in Node, convert $2b$ → $2y$ so Laravel/Filament
   * can still verify passwords created by NestJS.
   */
  private normalizeHashForStore(hash: string): string {
    return hash.replace(/^\$2b\$/, '$2y$');
  }

  async register(dto: RegisterDto) {
    const existing = await this.prisma.user.findUnique({
      where: { email: dto.email },
    });
    if (existing) {
      throw new ConflictException('Email already registered');
    }

    const rawHash = await bcrypt.hash(dto.password, 10);
    const hashedPassword = this.normalizeHashForStore(rawHash);
    const user = await this.prisma.user.create({
      data: {
        name: dto.name,
        email: dto.email,
        password: hashedPassword,
        createdAt: new Date(),
        updatedAt: new Date(),
      },
    });

    const token = this.jwtService.sign({ sub: Number(user.id), email: user.email });

    return {
      message: 'User registered successfully',
      user: pick(user, ['id', 'name', 'email']),
      token,
    };
  }

  async login(dto: LoginDto) {
    const user = await this.prisma.user.findUnique({
      where: { email: dto.email },
    });
    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }

    const normalizedHash = this.normalizeHashForVerify(user.password);
    const valid = await bcrypt.compare(dto.password, normalizedHash);
    if (!valid) {
      throw new UnauthorizedException('Invalid credentials');
    }

    const token = this.jwtService.sign({ sub: Number(user.id), email: user.email });

    return {
      message: 'Login successful',
      user: pick(user, ['id', 'name', 'email']),
      token,
    };
  }

  async logout() {
    // JWT is stateless — client discards the token
    return { message: 'Logged out successfully' };
  }
}
