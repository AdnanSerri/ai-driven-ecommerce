import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { PrismaService } from '../prisma/prisma.service';
import { CreateReviewDto } from './dto/create-review.dto';
import { paginate } from '../common/dto/pagination.dto';

@Injectable()
export class ReviewsService {
  constructor(
    private prisma: PrismaService,
    @InjectQueue('sentiment-analysis') private sentimentQueue: Queue,
    @InjectQueue('kafka-events') private kafkaQueue: Queue,
  ) {}

  async userReviews(userId: number, page = 1, perPage = 15) {
    const where = { userId: BigInt(userId) };

    const [reviews, total] = await Promise.all([
      this.prisma.review.findMany({
        where,
        include: {
          product: {
            select: { id: true, name: true, price: true, imageUrl: true },
          },
        },
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * perPage,
        take: perPage,
      }),
      this.prisma.review.count({ where }),
    ]);

    const serialized = reviews.map((r) => ({
      id: Number(r.id),
      user_id: Number(r.userId),
      product_id: Number(r.productId),
      rating: r.rating,
      comment: r.comment,
      created_at: r.createdAt.toISOString(),
      updated_at: r.createdAt.toISOString(),
      product: r.product
        ? {
            id: Number(r.product.id),
            name: r.product.name,
            price: parseFloat(r.product.price.toString()),
            image_url: r.product.imageUrl,
          }
        : null,
    }));

    return paginate(serialized, total, page, perPage);
  }

  async productReviews(productId: number, page = 1, perPage = 15) {
    const product = await this.prisma.product.findUnique({
      where: { id: BigInt(productId) },
    });
    if (!product) throw new NotFoundException('Product not found');

    const where = { productId: BigInt(productId) };

    const [reviews, total] = await Promise.all([
      this.prisma.review.findMany({
        where,
        include: {
          user: { select: { id: true, name: true, email: true } },
        },
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * perPage,
        take: perPage,
      }),
      this.prisma.review.count({ where }),
    ]);

    const serialized = reviews.map((r) => ({
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
    }));

    return paginate(serialized, total, page, perPage);
  }

  async create(userId: number, dto: CreateReviewDto) {
    const product = await this.prisma.product.findUnique({
      where: { id: BigInt(dto.product_id) },
    });
    if (!product) throw new NotFoundException('Product not found');

    const review = await this.prisma.review.create({
      data: {
        userId: BigInt(userId),
        productId: BigInt(dto.product_id),
        rating: dto.rating,
        comment: dto.comment,
        createdAt: new Date(),
      },
      include: {
        product: {
          select: { id: true, name: true, price: true, imageUrl: true },
        },
      },
    });

    // Dispatch sentiment analysis job (matches Laravel ReviewObserver)
    if (review.comment) {
      await this.sentimentQueue.add(
        'analyze',
        {
          reviewId: Number(review.id),
          text: review.comment,
          userId,
        },
        { attempts: 3, backoff: { type: 'fixed', delay: 5000 } },
      );
    }

    // Dispatch review.created Kafka event (matches Laravel ReviewObserver)
    await this.kafkaQueue.add(
      'publish',
      {
        topic: 'review.created',
        data: {
          event_type: 'review.created',
          review_id: Number(review.id),
          user_id: userId,
          product_id: dto.product_id,
          rating: dto.rating,
          comment: dto.comment,
          timestamp: new Date().toISOString(),
        },
      },
      { attempts: 3, backoff: { type: 'fixed', delay: 5000 } },
    );

    return {
      message: 'Review submitted successfully',
      data: {
        id: Number(review.id),
        rating: review.rating,
        comment: review.comment,
        created_at: review.createdAt.toISOString(),
        product: review.product
          ? {
              id: Number(review.product.id),
              name: review.product.name,
              price: parseFloat(review.product.price.toString()),
              image_url: review.product.imageUrl,
            }
          : null,
      },
    };
  }
}
