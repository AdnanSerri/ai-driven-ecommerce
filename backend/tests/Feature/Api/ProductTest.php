<?php

use App\Models\Category;
use App\Models\Product;

it('lists all products with pagination', function () {
    $category = Category::factory()->create();
    Product::factory()->count(20)->create(['category_id' => $category->id]);

    $response = $this->getJson('/api/products');

    $response->assertSuccessful()
        ->assertJsonStructure([
            'data',
            'current_page',
            'last_page',
            'per_page',
            'total',
        ])
        ->assertJsonCount(15, 'data');
});

it('returns empty list when no products exist', function () {
    $response = $this->getJson('/api/products');

    $response->assertSuccessful()
        ->assertJsonCount(0, 'data');
});

it('shows a single product', function () {
    $category = Category::factory()->create();
    $product = Product::factory()->create(['category_id' => $category->id]);

    $response = $this->getJson("/api/products/{$product->id}");

    $response->assertSuccessful()
        ->assertJsonPath('data.id', $product->id)
        ->assertJsonPath('data.name', $product->name);
});

it('returns 404 for non-existent product', function () {
    $response = $this->getJson('/api/products/999');

    $response->assertNotFound();
});

it('filters products by category', function () {
    $category1 = Category::factory()->create();
    $category2 = Category::factory()->create();

    Product::factory()->count(5)->create(['category_id' => $category1->id]);
    Product::factory()->count(3)->create(['category_id' => $category2->id]);

    $response = $this->getJson("/api/products?category={$category1->id}");

    $response->assertSuccessful()
        ->assertJsonCount(5, 'data');
});

it('returns products with category relationship', function () {
    $category = Category::factory()->create(['name' => 'Electronics']);
    Product::factory()->create(['category_id' => $category->id]);

    $response = $this->getJson('/api/products');

    $response->assertSuccessful()
        ->assertJsonPath('data.0.category.name', 'Electronics');
});
