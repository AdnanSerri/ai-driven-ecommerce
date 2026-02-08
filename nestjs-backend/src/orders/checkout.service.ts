import {
  Injectable,
  UnprocessableEntityException,
} from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { PrismaService } from '../prisma/prisma.service';
import { CheckoutDto } from './dto/checkout.dto';
import { OrderStatus } from '../common/enums';

@Injectable()
export class CheckoutService {
  constructor(
    private prisma: PrismaService,
    @InjectQueue('kafka-events') private kafkaQueue: Queue,
  ) {}

  /**
   * Generate order number matching Laravel's Order::generateOrderNumber()
   * Format: ORD-YYYYMMDDHHmmss-XXXX
   */
  private generateOrderNumber(): string {
    const now = new Date();
    const pad = (n: number, len = 2) => n.toString().padStart(len, '0');
    const timestamp = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `ORD-${timestamp}-${random}`;
  }

  async checkout(userId: number, dto: CheckoutDto) {
    // Load cart with items
    const cart = await this.prisma.cart.findFirst({
      where: { userId: BigInt(userId) },
      include: {
        items: {
          include: {
            product: true,
          },
        },
      },
    });

    if (!cart || cart.items.length === 0) {
      throw new UnprocessableEntityException('Cart is empty');
    }

    // Validate stock for all items
    for (const item of cart.items) {
      if (item.product.trackStock && item.product.stock < item.quantity) {
        throw new UnprocessableEntityException(
          `Insufficient stock for product: ${item.product.name}. Available: ${item.product.stock}, Requested: ${item.quantity}`,
        );
      }
    }

    // Resolve addresses — use provided or fall back to defaults
    let shippingAddressId = dto.shipping_address_id
      ? BigInt(dto.shipping_address_id)
      : null;
    let billingAddressId = dto.billing_address_id
      ? BigInt(dto.billing_address_id)
      : null;

    if (!shippingAddressId) {
      const defaultShipping = await this.prisma.address.findFirst({
        where: { userId: BigInt(userId), type: 'shipping', isDefault: true },
      });
      shippingAddressId = defaultShipping?.id || null;
    }
    if (!billingAddressId) {
      const defaultBilling = await this.prisma.address.findFirst({
        where: { userId: BigInt(userId), type: 'billing', isDefault: true },
      });
      billingAddressId = defaultBilling?.id || null;
    }

    // Calculate totals (matches Laravel: $cart->total)
    const subtotal = cart.items.reduce(
      (sum, item) =>
        sum + parseFloat(item.product.price.toString()) * item.quantity,
      0,
    );
    const discount = 0;
    const tax = 0;
    const total = subtotal - discount + tax;

    const orderNumber = this.generateOrderNumber();

    // Create order in transaction (matches Laravel's DB::transaction)
    const order = await this.prisma.$transaction(async (tx) => {
      const newOrder = await tx.order.create({
        data: {
          orderNumber,
          userId: BigInt(userId),
          shippingAddressId,
          billingAddressId,
          status: OrderStatus.Pending,
          subtotal,
          discount,
          tax,
          total,
          notes: dto.notes || null,
          orderedAt: new Date(),
        },
      });

      // Create order items with product snapshot
      for (const item of cart.items) {
        await tx.orderItem.create({
          data: {
            orderId: newOrder.id,
            productId: item.productId,
            productName: item.product.name,
            productPrice: item.product.price,
            quantity: item.quantity,
            subtotal: parseFloat(item.product.price.toString()) * item.quantity,
          },
        });

        // Decrement stock
        if (item.product.trackStock) {
          await tx.product.update({
            where: { id: item.productId },
            data: { stock: { decrement: item.quantity } },
          });
        }
      }

      // Clear cart items
      await tx.cartItem.deleteMany({ where: { cartId: cart.id } });

      return newOrder;
    });

    // Load order with items for response
    const fullOrder = await this.prisma.order.findUnique({
      where: { id: order.id },
      include: { items: true },
    });

    // Dispatch order.completed Kafka event via BullMQ (matches Laravel's queued job pattern)
    this.kafkaQueue
      .add(
        'publish',
        {
          topic: 'order.completed',
          data: {
            event_type: 'order.completed',
            order_id: Number(order.id),
            order_number: order.orderNumber,
            user_id: userId,
            items: cart.items.map((item) => ({
              product_id: Number(item.productId),
              quantity: item.quantity,
              price: parseFloat(item.product.price.toString()),
            })),
            total: parseFloat(total.toFixed(2)),
            timestamp: new Date().toISOString(),
          },
        },
        { attempts: 3, backoff: { type: 'fixed', delay: 5000 } },
      )
      .catch(() => {});

    return {
      message: 'Order placed successfully',
      data: {
        id: Number(fullOrder!.id),
        order_number: fullOrder!.orderNumber,
        status: fullOrder!.status,
        subtotal: parseFloat(fullOrder!.subtotal.toString()),
        discount: parseFloat(fullOrder!.discount.toString()),
        tax: parseFloat(fullOrder!.tax.toString()),
        total: parseFloat(fullOrder!.total.toString()),
        notes: fullOrder!.notes,
        items: fullOrder!.items.map((item) => ({
          id: Number(item.id),
          product_name: item.productName,
          product_price: parseFloat(item.productPrice.toString()),
          quantity: item.quantity,
          subtotal: parseFloat(item.subtotal.toString()),
        })),
        ordered_at: fullOrder!.orderedAt.toISOString(),
      },
    };
  }
}
