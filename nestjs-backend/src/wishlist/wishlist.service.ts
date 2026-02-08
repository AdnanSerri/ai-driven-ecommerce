import {
  Injectable,
  NotFoundException,
  ConflictException,
} from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { AddToWishlistDto } from './dto/add-to-wishlist.dto';
import { paginate } from '../common/dto/pagination.dto';

@Injectable()
export class WishlistService {
  constructor(private prisma: PrismaService) {}

  async findAll(userId: number, page = 1, perPage = 15) {
    const where = { userId: BigInt(userId) };

    const [items, total] = await Promise.all([
      this.prisma.wishlist.findMany({
        where,
        include: {
          product: {
            select: {
              id: true,
              name: true,
              description: true,
              price: true,
              stock: true,
              imageUrl: true,
              createdAt: true,
              category: { select: { id: true, name: true } },
              images: {
                select: {
                  id: true,
                  productId: true,
                  url: true,
                  altText: true,
                  isPrimary: true,
                  sortOrder: true,
                },
                orderBy: [{ isPrimary: 'desc' }, { sortOrder: 'asc' }],
              },
            },
          },
        },
        orderBy: { addedAt: 'desc' },
        skip: (page - 1) * perPage,
        take: perPage,
      }),
      this.prisma.wishlist.count({ where }),
    ]);

    const serialized = items.map((w) => ({
      id: Number(w.id),
      user_id: Number(w.userId),
      product_id: Number(w.productId),
      created_at: w.addedAt.toISOString(),
      product: w.product
        ? {
            id: Number(w.product.id),
            name: w.product.name,
            description: w.product.description,
            price: parseFloat(w.product.price.toString()),
            stock_quantity: w.product.stock,
            category: w.product.category
              ? { id: Number(w.product.category.id), name: w.product.category.name }
              : null,
            created_at: w.product.createdAt.toISOString(),
            images: w.product.images.map((img) => ({
              id: Number(img.id),
              product_id: Number(img.productId),
              url: img.url,
              alt_text: img.altText,
              sort_order: img.sortOrder,
              is_primary: img.isPrimary,
            })),
          }
        : null,
    }));

    return paginate(serialized, total, page, perPage);
  }

  async create(userId: number, dto: AddToWishlistDto) {
    const product = await this.prisma.product.findUnique({
      where: { id: BigInt(dto.product_id) },
    });
    if (!product) throw new NotFoundException('Product not found');

    const existing = await this.prisma.wishlist.findUnique({
      where: {
        userId_productId: {
          userId: BigInt(userId),
          productId: BigInt(dto.product_id),
        },
      },
    });
    if (existing) {
      throw new ConflictException('Product already in wishlist');
    }

    const wishlist = await this.prisma.wishlist.create({
      data: {
        userId: BigInt(userId),
        productId: BigInt(dto.product_id),
        addedAt: new Date(),
      },
      include: {
        product: {
          select: { id: true, name: true, price: true, imageUrl: true },
        },
      },
    });

    return {
      message: 'Product added to wishlist',
      data: {
        id: Number(wishlist.id),
        product: wishlist.product
          ? {
              id: Number(wishlist.product.id),
              name: wishlist.product.name,
              price: parseFloat(wishlist.product.price.toString()),
              image_url: wishlist.product.imageUrl,
            }
          : null,
        added_at: wishlist.addedAt.toISOString(),
      },
    };
  }

  async remove(userId: number, productId: number) {
    const wishlist = await this.prisma.wishlist.findUnique({
      where: {
        userId_productId: {
          userId: BigInt(userId),
          productId: BigInt(productId),
        },
      },
    });

    if (!wishlist) {
      throw new NotFoundException('Product not found in wishlist');
    }

    await this.prisma.wishlist.delete({
      where: { id: wishlist.id },
    });

    return { message: 'Product removed from wishlist' };
  }
}
