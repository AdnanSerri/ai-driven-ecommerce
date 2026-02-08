import {
  Injectable,
  NotFoundException,
  UnprocessableEntityException,
} from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { paginate } from '../common/dto/pagination.dto';
import { OrderStatus } from '../common/enums';

@Injectable()
export class OrdersService {
  constructor(private prisma: PrismaService) {}

  private serializeOrder(order: any, detail = false) {
    const base: any = {
      id: Number(order.id),
      order_number: order.orderNumber,
      status: order.status,
      subtotal: parseFloat(order.subtotal.toString()),
      discount: parseFloat(order.discount.toString()),
      tax: parseFloat(order.tax.toString()),
      total: parseFloat(order.total.toString()),
      ordered_at: order.orderedAt.toISOString(),
    };

    if (detail) {
      base.notes = order.notes;
      base.items = order.items?.map((item: any) => ({
        id: Number(item.id),
        product_name: item.productName,
        product_price: parseFloat(item.productPrice.toString()),
        quantity: item.quantity,
        subtotal: parseFloat(item.subtotal.toString()),
        product: item.product
          ? {
              id: Number(item.product.id),
              name: item.product.name,
              price: parseFloat(item.product.price.toString()),
              image_url: item.product.imageUrl,
            }
          : null,
      }));
      base.shippingAddress = order.shippingAddress
        ? this.serializeAddress(order.shippingAddress)
        : null;
      base.billingAddress = order.billingAddress
        ? this.serializeAddress(order.billingAddress)
        : null;
      base.confirmed_at = order.confirmedAt?.toISOString() || null;
      base.shipped_at = order.shippedAt?.toISOString() || null;
      base.delivered_at = order.deliveredAt?.toISOString() || null;
      base.cancelled_at = order.cancelledAt?.toISOString() || null;
    }

    return base;
  }

  private serializeAddress(addr: any) {
    return {
      id: Number(addr.id),
      label: addr.label,
      type: addr.type,
      first_name: addr.firstName,
      last_name: addr.lastName,
      phone: addr.phone,
      address_line_1: addr.addressLine1,
      address_line_2: addr.addressLine2,
      city: addr.city,
      state: addr.state,
      postal_code: addr.postalCode,
      country: addr.country,
      is_default: addr.isDefault,
      created_at: addr.createdAt.toISOString(),
    };
  }

  async findAll(userId: number, page = 1, perPage = 15) {
    const where = { userId: BigInt(userId) };

    const [orders, total] = await Promise.all([
      this.prisma.order.findMany({
        where,
        orderBy: { orderedAt: 'desc' },
        skip: (page - 1) * perPage,
        take: perPage,
      }),
      this.prisma.order.count({ where }),
    ]);

    const serialized = orders.map((o) => this.serializeOrder(o));
    return paginate(serialized, total, page, perPage);
  }

  async findOne(userId: number, id: number) {
    const order = await this.prisma.order.findUnique({
      where: { id: BigInt(id) },
      include: {
        items: { include: { product: true } },
        shippingAddress: true,
        billingAddress: true,
      },
    });

    if (!order || Number(order.userId) !== userId) {
      throw new NotFoundException('Order not found');
    }

    return { data: this.serializeOrder(order, true) };
  }

  async cancel(userId: number, id: number) {
    const order = await this.prisma.order.findUnique({
      where: { id: BigInt(id) },
      include: { items: true },
    });

    if (!order || Number(order.userId) !== userId) {
      throw new NotFoundException('Order not found');
    }

    const cancellableStatuses = [OrderStatus.Pending, OrderStatus.Confirmed];
    if (!cancellableStatuses.includes(order.status as OrderStatus)) {
      throw new UnprocessableEntityException('Order cannot be cancelled');
    }

    // Restore stock only for products that track stock
    for (const item of order.items) {
      const product = await this.prisma.product.findUnique({
        where: { id: item.productId },
        select: { trackStock: true },
      });
      if (product?.trackStock) {
        await this.prisma.product.update({
          where: { id: item.productId },
          data: { stock: { increment: item.quantity } },
        });
      }
    }

    await this.prisma.order.update({
      where: { id: BigInt(id) },
      data: {
        status: OrderStatus.Cancelled,
        cancelledAt: new Date(),
      },
    });

    // Reload with full relations for detail response
    const fullOrder = await this.prisma.order.findUnique({
      where: { id: BigInt(id) },
      include: {
        items: { include: { product: true } },
        shippingAddress: true,
        billingAddress: true,
      },
    });

    return {
      message: 'Order cancelled successfully',
      data: this.serializeOrder(fullOrder, true),
    };
  }
}
