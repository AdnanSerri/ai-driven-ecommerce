<?php

namespace Database\Factories;

use App\Models\Category;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Product>
 */
class ProductFactory extends Factory
{
    public function definition(): array
    {
        return [
            'name' => fake()->words(3, true),
            'description' => fake()->paragraph(),
            'price' => fake()->randomFloat(2, 10, 1000),
            'stock' => fake()->numberBetween(0, 100),
            'low_stock_threshold' => 10,
            'track_stock' => true,
            'category_id' => Category::factory(),
            'image_url' => fake()->optional()->imageUrl(640, 480, 'products'),
            'created_at' => now(),
        ];
    }

    public function outOfStock(): static
    {
        return $this->state(fn (array $attributes) => [
            'stock' => 0,
        ]);
    }

    public function lowStock(): static
    {
        return $this->state(fn (array $attributes) => [
            'stock' => fake()->numberBetween(1, 10),
        ]);
    }

    public function unlimitedStock(): static
    {
        return $this->state(fn (array $attributes) => [
            'track_stock' => false,
        ]);
    }
}
