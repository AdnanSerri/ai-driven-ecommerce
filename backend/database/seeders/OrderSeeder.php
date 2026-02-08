<?php

namespace Database\Seeders;

use App\Enums\OrderStatus;
use App\Models\Address;
use App\Models\Order;
use App\Models\OrderItem;
use App\Models\Product;
use App\Models\User;
use Illuminate\Database\Seeder;

class OrderSeeder extends Seeder
{
    public function run(): void
    {
        $users = User::where('is_admin', false)->get();
        $products = Product::all();

        foreach ($users as $user) {
            $orderCount = rand(0, 3);

            $shippingAddress = $user->addresses()->where('type', 'shipping')->first();

            for ($i = 0; $i < $orderCount; $i++) {
                $status = fake()->randomElement(OrderStatus::cases());

                $order = Order::factory()->create([
                    'user_id' => $user->id,
                    'shipping_address_id' => $shippingAddress?->id,
                    'status' => $status,
                    'confirmed_at' => in_array($status, [OrderStatus::Confirmed, OrderStatus::Processing, OrderStatus::Shipped, OrderStatus::Delivered]) ? now()->subDays(rand(1, 7)) : null,
                    'shipped_at' => in_array($status, [OrderStatus::Shipped, OrderStatus::Delivered]) ? now()->subDays(rand(1, 5)) : null,
                    'delivered_at' => $status === OrderStatus::Delivered ? now()->subDays(rand(1, 3)) : null,
                    'cancelled_at' => $status === OrderStatus::Cancelled ? now()->subDays(rand(1, 7)) : null,
                ]);

                $selectedProducts = $products->random(rand(1, 4));
                $subtotal = 0;

                foreach ($selectedProducts as $product) {
                    $quantity = rand(1, 3);
                    $itemSubtotal = $product->price * $quantity;
                    $subtotal += $itemSubtotal;

                    OrderItem::factory()->create([
                        'order_id' => $order->id,
                        'product_id' => $product->id,
                        'product_name' => $product->name,
                        'product_price' => $product->price,
                        'quantity' => $quantity,
                        'subtotal' => $itemSubtotal,
                    ]);
                }

                $tax = $subtotal * 0.1;
                $total = $subtotal + $tax;

                $order->update([
                    'subtotal' => $subtotal,
                    'tax' => $tax,
                    'total' => $total,
                ]);
            }
        }
    }
}
