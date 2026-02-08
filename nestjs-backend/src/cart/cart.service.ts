import {
  Injectable,
  NotFoundException,
  UnprocessableEntityException,
} from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { PrismaService } from '../prisma/prisma.service';
import { AddCartItemDto } from './dto/add-cart-item.dto';
import { UpdateCartItemDto } from './dto/update-cart-item.dto';

@Injectable()
export class CartService {
  constructor(
    private prisma: PrismaService,
    @InjectQueue('kafka-events') private kafkaQueue: Queue,
  ) {}

  private async getOrCreateCart(userId: number) {
    let cart = await this.prisma.cart.findFirst({
      where: { userId: BigInt(userId) },
    });
    if (!cart) {
      cart = await this.prisma.cart.create({
        data: {
          userId: BigInt(userId),
          createdAt: new Date(),
          updatedAt: new Date(),
        },
      });
    }
    return cart;
  }

  private serializeCartItem(item: any) {
    const price = item.product ? parseFloat(item.product.price.toString()) : 0;
    return {
      id: Number(item.id),
      cart_id: Number(item.cartId),
      product_id: Number(item.productId),
      quantity: item.quantity,
      price: price,
      created_at: item.addedAt.toISOString(),
      updated_at: item.addedAt.toISOString(),
      product: item.product
        ? {
            id: Number(item.product.id),
            name: item.product.name,
            price: price,
            stock_quantity: item.product.stock,
            low_stock_threshold: item.product.lowStockThreshold,
            track_stock: item.product.trackStock,
            images: item.product.images
              ? item.product.images.map((img: any) => ({
                  id: Number(img.id),
                  product_id: Number(img.productId),
                  url: img.url,
                  alt_text: img.altText,
                  sort_order: img.sortOrder,
                  is_primary: img.isPrimary,
                }))
              : [],
          }
        : null,
    };
  }

  private readonly productSelectWithStock = {
    id: true,
    name: true,
    price: true,
    imageUrl: true,
    stock: true,
    lowStockThreshold: true,
    trackStock: true,
    images: {
      select: {
        id: true,
        productId: true,
        url: true,
        altText: true,
        isPrimary: true,
        sortOrder: true,
      },
      orderBy: [{ isPrimary: 'desc' as const }, { sortOrder: 'asc' as const }],
    },
  };

  async show(userId: number) {
    const cart = await this.getOrCreateCart(userId);
    const items = await this.prisma.cartItem.findMany({
      where: { cartId: cart.id },
      include: {
        product: { select: this.productSelectWithStock },
      },
      orderBy: { addedAt: 'desc' },
    });

    const serializedItems = items.map((i) => this.serializeCartItem(i));
    const total = items.reduce(
      (sum, item) => sum + parseFloat(item.product.price.toString()) * item.quantity,
      0,
    );
    const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);

    // Return structure matching frontend Cart type expectations
    return {
      data: {
        id: Number(cart.id),
        user_id: Number(cart.userId),
        items: serializedItems,
        total: parseFloat(total.toFixed(2)),
        items_count: itemCount,
        created_at: cart.createdAt?.toISOString() || null,
        updated_at: cart.updatedAt?.toISOString() || null,
      },
    };
  }

  async addItem(userId: number, dto: AddCartItemDto) {
    const product = await this.prisma.product.findUnique({
      where: { id: BigInt(dto.product_id) },
    });
    if (!product) throw new NotFoundException('Product not found');

    if (product.trackStock && product.stock < dto.quantity) {
      throw new UnprocessableEntityException({
        message: 'Insufficient stock available',
        available_stock: product.stock,
      });
    }

    const cart = await this.getOrCreateCart(userId);

    const existingItem = await this.prisma.cartItem.findUnique({
      where: {
        cartId_productId: {
          cartId: cart.id,
          productId: BigInt(dto.product_id),
        },
      },
    });

    let cartItem;
    if (existingItem) {
      const newQty = existingItem.quantity + dto.quantity;
      if (product.trackStock && product.stock < newQty) {
        throw new UnprocessableEntityException({
          message: 'Insufficient stock for requested quantity',
          available_stock: product.stock,
          current_in_cart: existingItem.quantity,
        });
      }
      cartItem = await this.prisma.cartItem.update({
        where: { id: existingItem.id },
        data: { quantity: newQty },
        include: { product: { select: this.productSelectWithStock } },
      });
    } else {
      cartItem = await this.prisma.cartItem.create({
        data: {
          cartId: cart.id,
          productId: BigInt(dto.product_id),
          quantity: dto.quantity,
          addedAt: new Date(),
        },
        include: { product: { select: this.productSelectWithStock } },
      });
    }

    await this.prisma.cart.update({
      where: { id: cart.id },
      data: { updatedAt: new Date() },
    });

    const { total, itemCount, items } = await this.getCartTotals(cart.id);

    this.dispatchCartUpdatedEvent(userId, 'item_added', dto.product_id, items);

    return {
      message: 'Item added to cart',
      data: this.serializeCartItem(cartItem),
      cart_total: total,
      cart_item_count: itemCount,
    };
  }

  async updateItem(userId: number, cartItemId: number, dto: UpdateCartItemDto) {
    const cartItem = await this.prisma.cartItem.findUnique({
      where: { id: BigInt(cartItemId) },
      include: {
        cart: true,
        product: { select: this.productSelectWithStock },
      },
    });

    if (!cartItem || Number(cartItem.cart.userId) !== userId) {
      throw new NotFoundException('Cart item not found');
    }

    if (cartItem.product.trackStock && cartItem.product.stock < dto.quantity) {
      throw new UnprocessableEntityException({
        message: 'Insufficient stock available',
        available_stock: cartItem.product.stock,
      });
    }

    const updated = await this.prisma.cartItem.update({
      where: { id: BigInt(cartItemId) },
      data: { quantity: dto.quantity },
      include: { product: { select: this.productSelectWithStock } },
    });

    await this.prisma.cart.update({
      where: { id: cartItem.cartId },
      data: { updatedAt: new Date() },
    });

    const { total, itemCount, items } = await this.getCartTotals(cartItem.cartId);

    this.dispatchCartUpdatedEvent(userId, 'item_updated', Number(cartItem.productId), items);

    return {
      message: 'Cart item updated',
      data: this.serializeCartItem(updated),
      cart_total: total,
      cart_item_count: itemCount,
    };
  }

  async removeItem(userId: number, cartItemId: number) {
    const cartItem = await this.prisma.cartItem.findUnique({
      where: { id: BigInt(cartItemId) },
      include: { cart: true },
    });

    if (!cartItem || Number(cartItem.cart.userId) !== userId) {
      throw new NotFoundException('Cart item not found');
    }

    const productId = Number(cartItem.productId);

    await this.prisma.cartItem.delete({
      where: { id: BigInt(cartItemId) },
    });

    await this.prisma.cart.update({
      where: { id: cartItem.cartId },
      data: { updatedAt: new Date() },
    });

    const { total, itemCount, items } = await this.getCartTotals(cartItem.cartId);

    this.dispatchCartUpdatedEvent(userId, 'item_removed', productId, items);

    return {
      message: 'Item removed from cart',
      cart_total: total,
      cart_item_count: itemCount,
    };
  }

  async clear(userId: number) {
    const cart = await this.prisma.cart.findFirst({
      where: { userId: BigInt(userId) },
    });

    if (cart) {
      await this.prisma.cartItem.deleteMany({
        where: { cartId: cart.id },
      });
      await this.prisma.cart.update({
        where: { id: cart.id },
        data: { updatedAt: new Date() },
      });
    }

    this.dispatchCartUpdatedEvent(userId, 'cart_cleared', null, []);

    return { message: 'Cart cleared' };
  }

  private async getCartTotals(cartId: bigint) {
    const cartItems = await this.prisma.cartItem.findMany({
      where: { cartId },
      include: { product: { select: { id: true, price: true } } },
    });

    const total = cartItems.reduce(
      (sum, item) => sum + parseFloat(item.product.price.toString()) * item.quantity,
      0,
    );
    const itemCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);
    const items = cartItems.map((item) => ({
      product_id: Number(item.productId),
      quantity: item.quantity,
    }));

    return {
      total: parseFloat(total.toFixed(2)),
      itemCount,
      items,
    };
  }

  /**
   * Dispatch cart.updated Kafka event matching Laravel's payload shape exactly.
   */
  private dispatchCartUpdatedEvent(
    userId: number,
    action: string,
    affectedProductId: number | null,
    items: { product_id: number; quantity: number }[],
  ) {
    this.kafkaQueue
      .add(
        'publish',
        {
          topic: 'cart.updated',
          data: {
            event_type: 'cart.updated',
            user_id: userId,
            action,
            affected_product_id: affectedProductId,
            items,
            timestamp: new Date().toISOString(),
          },
        },
        { attempts: 3, backoff: { type: 'fixed', delay: 5000 } },
      )
      .catch(() => {});
  }
}
