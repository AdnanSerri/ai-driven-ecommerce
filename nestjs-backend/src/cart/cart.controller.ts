import {
  Controller,
  Get,
  Post,
  Put,
  Delete,
  Body,
  Param,
  ParseIntPipe,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import { CartService } from './cart.service';
import { AddCartItemDto } from './dto/add-cart-item.dto';
import { UpdateCartItemDto } from './dto/update-cart-item.dto';
import { CurrentUser } from '../common/decorators';

@Controller('cart')
export class CartController {
  constructor(private cartService: CartService) {}

  @Get()
  show(@CurrentUser('id') userId: number) {
    return this.cartService.show(userId);
  }

  @Post('items')
  @HttpCode(HttpStatus.CREATED)
  addItem(
    @CurrentUser('id') userId: number,
    @Body() dto: AddCartItemDto,
  ) {
    return this.cartService.addItem(userId, dto);
  }

  @Put('items/:id')
  updateItem(
    @CurrentUser('id') userId: number,
    @Param('id', ParseIntPipe) cartItemId: number,
    @Body() dto: UpdateCartItemDto,
  ) {
    return this.cartService.updateItem(userId, cartItemId, dto);
  }

  @Delete('items/:id')
  removeItem(
    @CurrentUser('id') userId: number,
    @Param('id', ParseIntPipe) cartItemId: number,
  ) {
    return this.cartService.removeItem(userId, cartItemId);
  }

  @Delete()
  clear(@CurrentUser('id') userId: number) {
    return this.cartService.clear(userId);
  }
}
