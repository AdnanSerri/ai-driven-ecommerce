import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bullmq';
import { OrdersController } from './orders.controller';
import { CheckoutController } from './checkout.controller';
import { OrdersService } from './orders.service';
import { CheckoutService } from './checkout.service';

@Module({
  imports: [BullModule.registerQueue({ name: 'kafka-events' })],
  controllers: [OrdersController, CheckoutController],
  providers: [OrdersService, CheckoutService],
})
export class OrdersModule {}
