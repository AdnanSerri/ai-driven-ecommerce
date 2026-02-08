import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { ListProductsDto } from './dto/list-products.dto';
import { paginate } from '../common/dto/pagination.dto';
import { Prisma } from '../../generated/prisma/client';

@Injectable()
export class ProductsService {
  constructor(private prisma: PrismaService) {}

  async findAll(dto: ListProductsDto) {
    const page = dto.page || 1;
    const perPage = dto.per_page || 15;

    const where: Prisma.ProductWhereInput = {};

    // Search — Laravel uses MATCH AGAINST (MySQL), we use ILIKE since it's PostgreSQL
    if (dto.search) {
      where.OR = [
        { name: { contains: dto.search, mode: 'insensitive' } },
        { description: { contains: dto.search, mode: 'insensitive' } },
      ];
    }

    // Category filter — include products from child categories
    if (dto.category) {
      const categoryId = BigInt(dto.category);
      // Get child category IDs
      const childCategories = await this.prisma.category.findMany({
        where: { parentId: categoryId },
        select: { id: true },
      });
      const categoryIds = [categoryId, ...childCategories.map((c) => c.id)];
      where.categoryId = { in: categoryIds };
    }

    // Price range
    if (dto.min_price !== undefined || dto.max_price !== undefined) {
      where.price = {};
      if (dto.min_price !== undefined) {
        where.price.gte = dto.min_price;
      }
      if (dto.max_price !== undefined) {
        where.price.lte = dto.max_price;
      }
    }

    // In-stock filter — Laravel: where('track_stock', false)->orWhere('stock', '>', 0)
    if (dto.in_stock === 'true' || dto.in_stock === '1') {
      where.OR = [
        ...(where.OR || []),
        { trackStock: false },
        { stock: { gt: 0 } },
      ];
      // If there's already an OR from search, we need to restructure
      if (dto.search) {
        const searchOr = [
          { name: { contains: dto.search, mode: 'insensitive' as const } },
          {
            description: {
              contains: dto.search,
              mode: 'insensitive' as const,
            },
          },
        ];
        delete where.OR;
        where.AND = [
          { OR: searchOr },
          { OR: [{ trackStock: false }, { stock: { gt: 0 } }] },
        ];
      }
    }

    // Sort — Laravel: orderBy($sortBy, $sortDir)
    const sortFieldMap: Record<string, string> = {
      created_at: 'createdAt',
      price: 'price',
      name: 'name',
      stock: 'stock',
    };
    const sortField = sortFieldMap[dto.sort_by || 'created_at'] || 'createdAt';
    const sortOrder = dto.sort_dir || 'desc';

    // min_rating filtering: Laravel uses whereHas('reviews') with havingRaw('AVG(rating) >= ?')
    // Prisma doesn't support HAVING, so we use raw SQL for this filter
    if (dto.min_rating !== undefined) {
      // Get product IDs that meet the min_rating threshold
      const qualifyingProducts = await this.prisma.$queryRaw<
        { product_id: bigint }[]
      >`
        SELECT product_id
        FROM reviews
        GROUP BY product_id
        HAVING AVG(rating) >= ${dto.min_rating}
      `;
      const productIds = qualifyingProducts.map((r) => r.product_id);
      if (productIds.length === 0) {
        return paginate([], 0, page, perPage);
      }
      where.id = { in: productIds };
    }

    const [products, total] = await Promise.all([
      this.prisma.product.findMany({
        where,
        include: {
          category: { select: { id: true, name: true } },
          images: { orderBy: { sortOrder: 'asc' } },
          _count: { select: { reviews: true } },
        },
        orderBy: { [sortField]: sortOrder },
        skip: (page - 1) * perPage,
        take: perPage,
      }),
      this.prisma.product.count({ where }),
    ]);

    // Get average ratings for all products in one query
    const productIds = products.map((p) => p.id);
    const ratingsMap = new Map<string, number>();

    if (productIds.length > 0) {
      const ratings = await this.prisma.$queryRaw<
        { product_id: bigint; avg_rating: number }[]
      >`
        SELECT product_id, AVG(rating)::float as avg_rating
        FROM reviews
        WHERE product_id = ANY(${productIds})
        GROUP BY product_id
      `;
      ratings.forEach((r) => {
        ratingsMap.set(r.product_id.toString(), r.avg_rating);
      });
    }

    // Serialize matching ProductFormula::List
    const serialized = products.map((p) => ({
      id: Number(p.id),
      name: p.name,
      sku: p.sku || `SKU-${p.id}`,
      description: p.description,
      price: parseFloat(p.price.toString()),
      stock: p.stock,
      stock_quantity: p.stock,
      image_url: p.imageUrl,
      images: p.images.map((img) => ({
        id: Number(img.id),
        url: img.url,
        alt_text: img.altText,
        is_primary: img.isPrimary,
        sort_order: img.sortOrder,
        created_at: img.createdAt.toISOString(),
      })),
      category: p.category
        ? { id: Number(p.category.id), name: p.category.name }
        : null,
      average_rating: ratingsMap.get(p.id.toString()) || null,
      reviews_count: p._count.reviews,
      created_at: p.createdAt.toISOString(),
    }));

    return paginate(serialized, total, page, perPage);
  }

  async findOne(id: number) {
    const product = await this.prisma.product.findUnique({
      where: { id: BigInt(id) },
      include: {
        category: { select: { id: true, name: true } },
        reviews: {
          include: {
            user: { select: { id: true, name: true, email: true } },
          },
          orderBy: { createdAt: 'desc' },
        },
        images: {
          orderBy: { sortOrder: 'asc' },
        },
        _count: { select: { reviews: true } },
      },
    });

    if (!product) {
      throw new NotFoundException('Product not found');
    }

    // Calculate average rating
    const avgRating =
      product.reviews.length > 0
        ? product.reviews.reduce((sum, r) => sum + r.rating, 0) /
          product.reviews.length
        : null;

    // Serialize matching ProductFormula::Detail
    const data = {
      id: Number(product.id),
      name: product.name,
      sku: product.sku || `SKU-${product.id}`,
      description: product.description,
      price: parseFloat(product.price.toString()),
      stock: product.stock,
      stock_quantity: product.stock,
      low_stock_threshold: product.lowStockThreshold,
      track_stock: product.trackStock,
      image_url: product.imageUrl,
      category: product.category
        ? { id: Number(product.category.id), name: product.category.name }
        : null,
      average_rating: avgRating,
      reviews_count: product._count.reviews,
      reviews: product.reviews.map((r) => ({
        id: Number(r.id),
        rating: r.rating,
        comment: r.comment,
        created_at: r.createdAt.toISOString(),
        user: r.user
          ? {
              id: Number(r.user.id),
              name: r.user.name,
              email: r.user.email,
            }
          : null,
      })),
      images: product.images.map((img) => ({
        id: Number(img.id),
        url: img.url,
        alt_text: img.altText,
        is_primary: img.isPrimary,
        sort_order: img.sortOrder,
        created_at: img.createdAt.toISOString(),
      })),
      created_at: product.createdAt.toISOString(),
    };

    return { data };
  }
}
