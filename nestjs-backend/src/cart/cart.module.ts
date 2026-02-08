import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bullmq';
import { CartController } from './cart.controller';
import { CartService } from './cart.service';

@Module({
  imports: [BullModule.registerQueue({ name: 'kafka-events' })],
  controllers: [CartController],
  providers: [CartService],
  exports: [CartService],
})
export class CartModule {}
