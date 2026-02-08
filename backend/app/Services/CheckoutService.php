<?php

namespace App\Services;

use App\Enums\OrderStatus;
use App\Jobs\PublishKafkaEventJob;
use App\Models\Cart;
use App\Models\Order;
use App\Models\User;
use Illuminate\Support\Facades\DB;

class CheckoutService
{
    public function checkout(User $user, ?int $shippingAddressId = null, ?int $billingAddressId = null, ?string $notes = null): Order
    {
        $cart = $user->cart;

        if (! $cart || $cart->items->isEmpty()) {
            throw new \Exception('Cart is empty');
        }

        $cart->load('items.product');

        $this->validateStock($cart);

        $order = DB::transaction(function () use ($user, $cart, $shippingAddressId, $billingAddressId, $notes) {
            $subtotal = $cart->total;
            $discount = 0;
            $tax = 0;
            $total = $subtotal - $discount + $tax;

            $order = Order::create([
                'order_number' => Order::generateOrderNumber(),
                'user_id' => $user->id,
                'shipping_address_id' => $shippingAddressId,
                'billing_address_id' => $billingAddressId,
                'status' => OrderStatus::Pending,
                'subtotal' => $subtotal,
                'discount' => $discount,
                'tax' => $tax,
                'total' => $total,
                'notes' => $notes,
                'ordered_at' => now(),
            ]);

            foreach ($cart->items as $cartItem) {
                $product = $cartItem->product;

                $order->items()->create([
                    'product_id' => $product->id,
                    'product_name' => $product->name,
                    'product_price' => $product->price,
                    'quantity' => $cartItem->quantity,
                    'subtotal' => $product->price * $cartItem->quantity,
                ]);

                $product->decrementStock($cartItem->quantity);
            }

            $cart->items()->delete();

            return $order;
        });

        // Dispatch Kafka event after transaction commits
        $this->dispatchOrderCompletedEvent($order);

        return $order;
    }

    /**
     * Dispatch the order.completed Kafka event.
     */
    protected function dispatchOrderCompletedEvent(Order $order): void
    {
        $order->load('items');

        $items = $order->items->map(fn ($item) => [
            'product_id' => $item->product_id,
            'quantity' => $item->quantity,
            'price' => (float) $item->product_price,
        ])->toArray();

        PublishKafkaEventJob::dispatch('order.completed', [
            'event_type' => 'order.completed',
            'order_id' => $order->id,
            'order_number' => $order->order_number,
            'user_id' => $order->user_id,
            'items' => $items,
            'total' => (float) $order->total,
            'timestamp' => now()->toIso8601String(),
        ]);
    }

    protected function validateStock(Cart $cart): void
    {
        foreach ($cart->items as $item) {
            $product = $item->product;

            if ($product->track_stock && $product->stock < $item->quantity) {
                throw new \Exception("Insufficient stock for product: {$product->name}. Available: {$product->stock}, Requested: {$item->quantity}");
            }
        }
    }
}
