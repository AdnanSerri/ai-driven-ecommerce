import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { serialize } from '../common/helpers/serializer';

@Injectable()
export class CategoriesService {
  constructor(private prisma: PrismaService) {}

  async findAll() {
    const categories = await this.prisma.category.findMany({
      where: { parentId: null },
      select: {
        id: true,
        name: true,
        _count: {
          select: { products: true },
        },
        children: {
          select: {
            id: true,
            name: true,
            _count: {
              select: { products: true },
            },
          },
        },
      },
    });

    // Transform to include products_count at top level
    const serialized = categories.map((cat) => ({
      id: Number(cat.id),
      name: cat.name,
      products_count: cat._count.products,
      children: cat.children.map((child) => ({
        id: Number(child.id),
        name: child.name,
        products_count: child._count.products,
      })),
    }));

    return { data: serialized };
  }
}
