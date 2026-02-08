import {
  Controller,
  Get,
  Post,
  Delete,
  Body,
  Param,
  Query,
  ParseIntPipe,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import { WishlistService } from './wishlist.service';
import { AddToWishlistDto } from './dto/add-to-wishlist.dto';
import { CurrentUser } from '../common/decorators';
import { PaginationDto } from '../common/dto/pagination.dto';

@Controller('wishlist')
export class WishlistController {
  constructor(private wishlistService: WishlistService) {}

  @Get()
  findAll(
    @CurrentUser('id') userId: number,
    @Query() query: PaginationDto,
  ) {
    return this.wishlistService.findAll(userId, query.page, query.per_page);
  }

  @Post()
  @HttpCode(HttpStatus.CREATED)
  create(
    @CurrentUser('id') userId: number,
    @Body() dto: AddToWishlistDto,
  ) {
    return this.wishlistService.create(userId, dto);
  }

  @Delete(':productId')
  remove(
    @CurrentUser('id') userId: number,
    @Param('productId', ParseIntPipe) productId: number,
  ) {
    return this.wishlistService.remove(userId, productId);
  }
}
