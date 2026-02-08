<?php

namespace Database\Factories;

use App\Enums\AddressType;
use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Address>
 */
class AddressFactory extends Factory
{
    public function definition(): array
    {
        return [
            'user_id' => User::factory(),
            'label' => fake()->randomElement(['Home', 'Work', 'Other', null]),
            'type' => fake()->randomElement(AddressType::cases()),
            'first_name' => fake()->firstName(),
            'last_name' => fake()->lastName(),
            'phone' => fake()->optional()->phoneNumber(),
            'address_line_1' => fake()->streetAddress(),
            'address_line_2' => fake()->optional()->secondaryAddress(),
            'city' => fake()->city(),
            'state' => fake()->optional()->state(),
            'postal_code' => fake()->postcode(),
            'country' => 'US',
            'is_default' => false,
            'created_at' => now(),
        ];
    }

    public function shipping(): static
    {
        return $this->state(fn (array $attributes) => [
            'type' => AddressType::Shipping,
        ]);
    }

    public function billing(): static
    {
        return $this->state(fn (array $attributes) => [
            'type' => AddressType::Billing,
        ]);
    }

    public function default(): static
    {
        return $this->state(fn (array $attributes) => [
            'is_default' => true,
        ]);
    }
}
