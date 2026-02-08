import {
  Controller,
  Get,
  Post,
  Body,
  Param,
  Query,
  ParseIntPipe,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import { ReviewsService } from './reviews.service';
import { CreateReviewDto } from './dto/create-review.dto';
import { CurrentUser, Public } from '../common/decorators';
import { PaginationDto } from '../common/dto/pagination.dto';

@Controller()
export class ReviewsController {
  constructor(private reviewsService: ReviewsService) {}

  @Get('user/reviews')
  userReviews(
    @CurrentUser('id') userId: number,
    @Query() query: PaginationDto,
  ) {
    return this.reviewsService.userReviews(userId, query.page, query.per_page);
  }

  @Public()
  @Get('products/:id/reviews')
  productReviews(
    @Param('id', ParseIntPipe) productId: number,
    @Query() query: PaginationDto,
  ) {
    return this.reviewsService.productReviews(
      productId,
      query.page,
      query.per_page,
    );
  }

  @Post('reviews')
  @HttpCode(HttpStatus.CREATED)
  create(
    @CurrentUser('id') userId: number,
    @Body() dto: CreateReviewDto,
  ) {
    return this.reviewsService.create(userId, dto);
  }
}
