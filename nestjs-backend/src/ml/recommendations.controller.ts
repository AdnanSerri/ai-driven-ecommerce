import {
  Controller,
  Get,
  Post,
  Delete,
  Body,
  Param,
  Query,
  ParseIntPipe,
  HttpStatus,
  HttpCode,
  HttpException,
  Header,
} from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { MlService } from './ml.service';
import { PrismaService } from '../prisma/prisma.service';
import { CurrentUser } from '../common/decorators';
import { Public } from '../common/decorators';
import { IsInt, IsIn, IsOptional, IsString, Min, Max } from 'class-validator';
import { Transform } from 'class-transformer';

class RecommendationQueryDto {
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(50)
  limit?: number = 10;

  @IsOptional()
  @IsString()
  session_product_ids?: string;
}

class SimilarQueryDto {
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(20)
  limit?: number = 10;
}

class BoughtTogetherQueryDto {
  @IsOptional()
  @Transform(({ value }) => parseInt(value))
  @IsInt()
  @Min(1)
  @Max(20)
  limit?: number = 5;
}

class TrendingQueryDto {
  @IsOptional()
  @Transform(({ value }) => parseInt(value))
  @IsInt()
  @Min(1)
  @Max(50)
  limit?: number = 10;

  @IsOptional()
  @Transform(({ value }) => parseInt(value))
  @IsInt()
  category_id?: number;
}

class FeedbackDto {
  @IsInt()
  product_id: number;

  @IsIn(['clicked', 'purchased', 'dismissed', 'viewed', 'not_interested'])
  action: string;

  @IsOptional()
  @IsString()
  reason?: string;
}

class NotInterestedDto {
  @IsInt()
  product_id: number;

  @IsOptional()
  @IsString()
  reason?: string;
}

@Controller()
export class RecommendationsController {
  constructor(
    private mlService: MlService,
    private prisma: PrismaService,
    @InjectQueue('recommendation-feedback') private feedbackQueue: Queue,
  ) {}

  @Get('recommendations')
  @Header('Cache-Control', 'no-store, no-cache, must-revalidate')
  async index(
    @CurrentUser('id') userId: number,
    @Query() query: RecommendationQueryDto,
  ) {
    // Parse session product IDs if provided
    let sessionProductIds: number[] | undefined;
    if (query.session_product_ids) {
      sessionProductIds = query.session_product_ids
        .split(',')
        .map((id) => parseInt(id.trim()))
        .filter((id) => !isNaN(id));
    }

    const result = await this.mlService.getRecommendationsWithSession(
      userId,
      query.limit,
      sessionProductIds,
    );
    if (!result) {
      throw new HttpException(
        {
          message: 'Unable to fetch recommendations at this time',
          data: [],
        },
        HttpStatus.SERVICE_UNAVAILABLE,
      );
    }

    // Extract product IDs from ML response
    const recs: any[] = result.recommendations ?? [];
    const productIds = recs.map((r: any) => BigInt(r.product_id));

    // Fetch actual product data from PostgreSQL
    const products = await this.prisma.product.findMany({
      where: { id: { in: productIds } },
      include: {
        category: { select: { id: true, name: true } },
        images: { orderBy: { sortOrder: 'asc' } },
        _count: { select: { reviews: true } },
      },
    });
    const productsMap = new Map(products.map((p) => [Number(p.id), p]));

    // Get average ratings for all products in one query
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

    // Build response matching Laravel's shape
    const data = recs
      .map((rec: any) => {
        const product = productsMap.get(rec.product_id);
        if (!product) return null;

        const primaryImage = product.images.find((img) => img.isPrimary) || product.images[0];

        return {
          product: {
            id: Number(product.id),
            name: product.name,
            price: parseFloat(product.price.toString()),
            stock_quantity: product.stock,
            category: product.category
              ? { id: Number(product.category.id), name: product.category.name }
              : null,
            images: product.images.map((img) => ({
              id: Number(img.id),
              product_id: Number(img.productId),
              url: img.url,
              alt_text: img.altText,
              sort_order: img.sortOrder,
              is_primary: img.isPrimary,
            })),
            average_rating: ratingsMap.get(product.id.toString()) || null,
            reviews_count: product._count.reviews,
          },
          score: rec.score ?? null,
          reason: rec.reason ?? null,
        };
      })
      .filter(Boolean);

    return {
      data,
      meta: {
        user_id: userId,
        personality_type: result.personality_type ?? null,
      },
    };
  }

  @Public()
  @Get('products/:id/similar')
  async similar(
    @Param('id', ParseIntPipe) productId: number,
    @Query() query: SimilarQueryDto,
  ) {
    const sourceProduct = await this.prisma.product.findUnique({
      where: { id: BigInt(productId) },
      select: { id: true, name: true },
    });

    const result = await this.mlService.getSimilarProducts(
      productId,
      query.limit,
    );
    if (!result) {
      throw new HttpException(
        {
          message: 'Unable to fetch similar products at this time',
          data: [],
        },
        HttpStatus.SERVICE_UNAVAILABLE,
      );
    }

    // Extract product IDs from ML response
    const similarItems: any[] = result.similar_products ?? [];
    const similarProductIds = similarItems.map((r: any) => BigInt(r.product_id));

    // Fetch actual product data from PostgreSQL
    const products = await this.prisma.product.findMany({
      where: { id: { in: similarProductIds } },
      include: {
        category: { select: { id: true, name: true } },
        images: { orderBy: { sortOrder: 'asc' } },
      },
    });
    const productsMap = new Map(products.map((p) => [Number(p.id), p]));

    const data = similarItems
      .map((rec: any) => {
        const product = productsMap.get(rec.product_id);
        if (!product) return null;

        const primaryImage = product.images.find((img) => img.isPrimary) || product.images[0];

        return {
          product: {
            id: Number(product.id),
            name: product.name,
            price: parseFloat(product.price.toString()),
            image_url: primaryImage?.url ?? product.imageUrl,
            category: product.category?.name ?? null,
            in_stock: product.stock > 0,
          },
          similarity_score: rec.similarity_score ?? null,
        };
      })
      .filter(Boolean);

    return {
      data,
      meta: {
        source_product_id: productId,
        source_product_name: sourceProduct?.name ?? null,
      },
    };
  }

  @Post('recommendations/feedback')
  @HttpCode(HttpStatus.OK)
  async feedback(
    @CurrentUser('id') userId: number,
    @Body() dto: FeedbackDto,
  ) {
    // Handle "not_interested" action specially
    if (dto.action === 'not_interested') {
      await this.mlService.markNotInterested(userId, dto.product_id, dto.reason);
      return { message: 'Product marked as not interested' };
    }

    await this.feedbackQueue.add(
      'process',
      { userId, productId: dto.product_id, action: dto.action },
      { attempts: 3, backoff: { type: 'fixed', delay: 5000 } },
    );

    return { message: 'Feedback recorded successfully' };
  }

  @Public()
  @Get('recommendations/bought-together/:productId')
  async boughtTogether(
    @Param('productId', ParseIntPipe) productId: number,
    @Query() query: BoughtTogetherQueryDto,
  ) {
    const result = await this.mlService.getFrequentlyBoughtTogether(
      productId,
      query.limit,
    );

    if (!result) {
      return {
        success: true,
        product_id: productId,
        products: [],
        total: 0,
        bundle_total: null,
      };
    }

    // Fetch full product data for co-purchased items
    const productIds = result.products?.map((p: any) => BigInt(p.product_id)) ?? [];
    if (productIds.length === 0) {
      return {
        success: true,
        product_id: productId,
        products: [],
        total: 0,
        bundle_total: null,
      };
    }

    const products = await this.prisma.product.findMany({
      where: { id: { in: productIds } },
      include: {
        category: { select: { id: true, name: true } },
        images: { orderBy: { sortOrder: 'asc' } },
      },
    });
    const productsMap = new Map(products.map((p) => [Number(p.id), p]));

    const enrichedProducts = result.products
      .map((item: any) => {
        const product = productsMap.get(item.product_id);
        if (!product) return null;

        const primaryImage =
          product.images.find((img) => img.isPrimary) || product.images[0];

        return {
          product_id: Number(product.id),
          name: product.name,
          price: parseFloat(product.price.toString()),
          image_url: primaryImage?.url ?? product.imageUrl,
          category_id: product.category?.id ? Number(product.category.id) : null,
          category_name: product.category?.name ?? null,
          co_occurrence_count: item.co_occurrence_count,
          in_stock: product.stock > 0,
        };
      })
      .filter(Boolean);

    const bundleTotal = enrichedProducts.reduce(
      (sum: number, p: any) => sum + (p.price || 0),
      0,
    );

    return {
      success: true,
      product_id: productId,
      products: enrichedProducts,
      total: enrichedProducts.length,
      bundle_total: bundleTotal > 0 ? bundleTotal : null,
    };
  }

  @Public()
  @Get('recommendations/trending')
  async trending(@Query() query: TrendingQueryDto) {
    const result = await this.mlService.getTrendingProducts(
      query.limit,
      query.category_id,
    );

    if (!result) {
      return {
        success: true,
        products: [],
        total: 0,
        category_id: query.category_id ?? null,
        period_days: 7,
      };
    }

    // Fetch full product data for trending items
    const productIds = result.products?.map((p: any) => BigInt(p.product_id)) ?? [];
    if (productIds.length === 0) {
      return {
        success: true,
        products: [],
        total: 0,
        category_id: query.category_id ?? null,
        period_days: result.period_days ?? 7,
      };
    }

    const products = await this.prisma.product.findMany({
      where: { id: { in: productIds } },
      include: {
        category: { select: { id: true, name: true } },
        images: { orderBy: { sortOrder: 'asc' } },
      },
    });
    const productsMap = new Map(products.map((p) => [Number(p.id), p]));

    const enrichedProducts = result.products
      .map((item: any) => {
        const product = productsMap.get(item.product_id);
        if (!product) return null;

        const primaryImage =
          product.images.find((img) => img.isPrimary) || product.images[0];

        return {
          product_id: Number(product.id),
          name: product.name,
          price: parseFloat(product.price.toString()),
          image_url: primaryImage?.url ?? product.imageUrl,
          category_id: product.category?.id ? Number(product.category.id) : null,
          category_name: product.category?.name ?? null,
          trending_score: item.trending_score,
          recent_orders: item.recent_orders ?? 0,
          recent_views: item.recent_views ?? 0,
          growth_rate: item.growth_rate ?? null,
          in_stock: product.stock > 0,
        };
      })
      .filter(Boolean);

    return {
      success: true,
      products: enrichedProducts,
      total: enrichedProducts.length,
      category_id: query.category_id ?? null,
      period_days: result.period_days ?? 7,
    };
  }

  @Post('recommendations/not-interested')
  @HttpCode(HttpStatus.OK)
  async markNotInterested(
    @CurrentUser('id') userId: number,
    @Query('product_id', ParseIntPipe) productId: number,
    @Query('reason') reason?: string,
  ) {
    await this.mlService.markNotInterested(userId, productId, reason);
    return { message: 'Product marked as not interested' };
  }

  @Delete('recommendations/not-interested')
  @HttpCode(HttpStatus.OK)
  async removeNotInterested(
    @CurrentUser('id') userId: number,
    @Query('product_id', ParseIntPipe) productId: number,
  ) {
    await this.mlService.removeNotInterested(userId, productId);
    return { message: 'Product removed from not interested list' };
  }
}
