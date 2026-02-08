import {
  Controller,
  Get,
  Post,
  Param,
  Query,
  ParseIntPipe,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import { OrdersService } from './orders.service';
import { CurrentUser } from '../common/decorators';
import { PaginationDto } from '../common/dto/pagination.dto';

@Controller('orders')
export class OrdersController {
  constructor(private ordersService: OrdersService) {}

  @Get()
  findAll(
    @CurrentUser('id') userId: number,
    @Query() query: PaginationDto,
  ) {
    return this.ordersService.findAll(userId, query.page, query.per_page);
  }

  @Get(':id')
  findOne(
    @CurrentUser('id') userId: number,
    @Param('id', ParseIntPipe) id: number,
  ) {
    return this.ordersService.findOne(userId, id);
  }

  @Post(':id/cancel')
  @HttpCode(HttpStatus.OK)
  cancel(
    @CurrentUser('id') userId: number,
    @Param('id', ParseIntPipe) id: number,
  ) {
    return this.ordersService.cancel(userId, id);
  }
}
