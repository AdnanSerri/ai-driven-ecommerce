import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { UpdateProfileDto } from './dto/update-profile.dto';

@Injectable()
export class UsersService {
  constructor(private prisma: PrismaService) {}

  private serializeProfile(user: any) {
    return {
      id: Number(user.id),
      name: user.name,
      email: user.email,
      phone: user.phone,
      avatar_url: user.avatarUrl,
      date_of_birth: user.dateOfBirth
        ? user.dateOfBirth.toISOString().split('T')[0]
        : null,
      preferences: user.preferences,
      created_at: user.createdAt?.toISOString() || null,
    };
  }

  async getProfile(userId: number) {
    const user = await this.prisma.user.findUnique({
      where: { id: BigInt(userId) },
      select: {
        id: true,
        name: true,
        email: true,
        phone: true,
        avatarUrl: true,
        dateOfBirth: true,
        preferences: true,
        createdAt: true,
      },
    });
    return { data: this.serializeProfile(user) };
  }

  async updateProfile(userId: number, dto: UpdateProfileDto) {
    const user = await this.prisma.user.update({
      where: { id: BigInt(userId) },
      data: {
        ...(dto.name !== undefined && { name: dto.name }),
        ...(dto.phone !== undefined && { phone: dto.phone }),
        ...(dto.avatar_url !== undefined && { avatarUrl: dto.avatar_url }),
        ...(dto.date_of_birth !== undefined && {
          dateOfBirth: dto.date_of_birth ? new Date(dto.date_of_birth) : null,
        }),
        ...(dto.preferences !== undefined && { preferences: dto.preferences }),
        updatedAt: new Date(),
      },
      select: {
        id: true,
        name: true,
        email: true,
        phone: true,
        avatarUrl: true,
        dateOfBirth: true,
        preferences: true,
        createdAt: true,
      },
    });
    return {
      message: 'Profile updated successfully',
      data: this.serializeProfile(user),
    };
  }
}
