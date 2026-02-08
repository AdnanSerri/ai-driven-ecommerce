import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateAddressDto } from './dto/create-address.dto';
import { UpdateAddressDto } from './dto/update-address.dto';

@Injectable()
export class AddressesService {
  constructor(private prisma: PrismaService) {}

  private serializeAddress(addr: any) {
    return {
      id: Number(addr.id),
      label: addr.label,
      type: addr.type,
      first_name: addr.firstName,
      last_name: addr.lastName,
      phone: addr.phone,
      address_line_1: addr.addressLine1,
      address_line_2: addr.addressLine2,
      city: addr.city,
      state: addr.state,
      postal_code: addr.postalCode,
      country: addr.country,
      is_default: addr.isDefault,
      created_at: addr.createdAt.toISOString(),
    };
  }

  async findAll(userId: number) {
    const addresses = await this.prisma.address.findMany({
      where: { userId: BigInt(userId) },
      orderBy: { createdAt: 'desc' },
    });
    return { data: addresses.map(this.serializeAddress) };
  }

  async findOne(userId: number, id: number) {
    const address = await this.prisma.address.findUnique({
      where: { id: BigInt(id) },
    });
    if (!address || Number(address.userId) !== userId) {
      throw new NotFoundException('Address not found');
    }
    return { data: this.serializeAddress(address) };
  }

  async create(userId: number, dto: CreateAddressDto) {
    // If setting as default, unset others of same type
    if (dto.is_default) {
      await this.prisma.address.updateMany({
        where: { userId: BigInt(userId), type: dto.type, isDefault: true },
        data: { isDefault: false },
      });
    }

    const address = await this.prisma.address.create({
      data: {
        userId: BigInt(userId),
        label: dto.label || null,
        type: dto.type,
        firstName: dto.first_name,
        lastName: dto.last_name,
        phone: dto.phone || null,
        addressLine1: dto.address_line_1,
        addressLine2: dto.address_line_2 || null,
        city: dto.city,
        state: dto.state || null,
        postalCode: dto.postal_code,
        country: dto.country,
        isDefault: dto.is_default || false,
        createdAt: new Date(),
      },
    });

    return {
      message: 'Address created successfully',
      data: this.serializeAddress(address),
    };
  }

  async update(userId: number, id: number, dto: UpdateAddressDto) {
    const address = await this.prisma.address.findUnique({
      where: { id: BigInt(id) },
    });
    if (!address || Number(address.userId) !== userId) {
      throw new NotFoundException('Address not found');
    }

    const type = dto.type || address.type;
    if (dto.is_default) {
      await this.prisma.address.updateMany({
        where: { userId: BigInt(userId), type, isDefault: true, id: { not: BigInt(id) } },
        data: { isDefault: false },
      });
    }

    const updated = await this.prisma.address.update({
      where: { id: BigInt(id) },
      data: {
        ...(dto.label !== undefined && { label: dto.label }),
        ...(dto.type !== undefined && { type: dto.type }),
        ...(dto.first_name !== undefined && { firstName: dto.first_name }),
        ...(dto.last_name !== undefined && { lastName: dto.last_name }),
        ...(dto.phone !== undefined && { phone: dto.phone }),
        ...(dto.address_line_1 !== undefined && { addressLine1: dto.address_line_1 }),
        ...(dto.address_line_2 !== undefined && { addressLine2: dto.address_line_2 }),
        ...(dto.city !== undefined && { city: dto.city }),
        ...(dto.state !== undefined && { state: dto.state }),
        ...(dto.postal_code !== undefined && { postalCode: dto.postal_code }),
        ...(dto.country !== undefined && { country: dto.country }),
        ...(dto.is_default !== undefined && { isDefault: dto.is_default }),
      },
    });

    return {
      message: 'Address updated successfully',
      data: this.serializeAddress(updated),
    };
  }

  async remove(userId: number, id: number) {
    const address = await this.prisma.address.findUnique({
      where: { id: BigInt(id) },
    });
    if (!address || Number(address.userId) !== userId) {
      throw new NotFoundException('Address not found');
    }

    await this.prisma.address.delete({ where: { id: BigInt(id) } });
    return { message: 'Address deleted successfully' };
  }

  async setDefault(userId: number, id: number) {
    const address = await this.prisma.address.findUnique({
      where: { id: BigInt(id) },
    });
    if (!address || Number(address.userId) !== userId) {
      throw new NotFoundException('Address not found');
    }

    // Unset other defaults of same type
    await this.prisma.address.updateMany({
      where: { userId: BigInt(userId), type: address.type, isDefault: true },
      data: { isDefault: false },
    });

    const updated = await this.prisma.address.update({
      where: { id: BigInt(id) },
      data: { isDefault: true },
    });

    return {
      message: 'Default address updated',
      data: this.serializeAddress(updated),
    };
  }
}
