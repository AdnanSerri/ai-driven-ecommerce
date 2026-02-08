<?php

namespace Database\Factories;

use App\Enums\OrderStatus;
use App\Models\Address;
use App\Models\Order;
use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Order>
 */
class OrderFactory extends Factory
{
    public function definition(): array
    {
        $subtotal = fake()->randomFloat(2, 50, 500);
        $discount = fake()->optional(0.3)->randomFloat(2, 0, $subtotal * 0.2) ?? 0;
        $tax = $subtotal * 0.1;
        $total = $subtotal - $discount + $tax;

        return [
            'order_number' => Order::generateOrderNumber(),
            'user_id' => User::factory(),
            'shipping_address_id' => null,
            'billing_address_id' => null,
            'status' => OrderStatus::Pending,
            'subtotal' => $subtotal,
            'discount' => $discount,
            'tax' => $tax,
            'total' => $total,
            'notes' => fake()->optional()->sentence(),
            'ordered_at' => now(),
            'confirmed_at' => null,
            'shipped_at' => null,
            'delivered_at' => null,
            'cancelled_at' => null,
        ];
    }

    public function withAddresses(): static
    {
        return $this->state(function (array $attributes) {
            $user = User::find($attributes['user_id']) ?? User::factory()->create();

            return [
                'shipping_address_id' => Address::factory()->shipping()->create(['user_id' => $user->id])->id,
                'billing_address_id' => Address::factory()->billing()->create(['user_id' => $user->id])->id,
            ];
        });
    }

    public function confirmed(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => OrderStatus::Confirmed,
            'confirmed_at' => now(),
        ]);
    }

    public function processing(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => OrderStatus::Processing,
            'confirmed_at' => now()->subHours(2),
        ]);
    }

    public function shipped(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => OrderStatus::Shipped,
            'confirmed_at' => now()->subDays(2),
            'shipped_at' => now()->subDay(),
        ]);
    }

    public function delivered(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => OrderStatus::Delivered,
            'confirmed_at' => now()->subDays(5),
            'shipped_at' => now()->subDays(3),
            'delivered_at' => now()->subDay(),
        ]);
    }

    public function cancelled(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => OrderStatus::Cancelled,
            'cancelled_at' => now(),
        ]);
    }
}
