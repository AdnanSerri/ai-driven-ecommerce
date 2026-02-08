<?php

use App\Models\Category;

it('lists all parent categories', function () {
    Category::factory()->count(5)->create();

    $response = $this->getJson('/api/categories');

    $response->assertSuccessful()
        ->assertJsonCount(5, 'data');
});

it('returns categories with children', function () {
    $parent = Category::factory()->create(['name' => 'Electronics']);
    Category::factory()->create([
        'name' => 'Phones',
        'parent_id' => $parent->id,
    ]);
    Category::factory()->create([
        'name' => 'Laptops',
        'parent_id' => $parent->id,
    ]);

    $response = $this->getJson('/api/categories');

    $response->assertSuccessful()
        ->assertJsonCount(1, 'data')
        ->assertJsonPath('data.0.name', 'Electronics')
        ->assertJsonCount(2, 'data.0.children');
});

it('excludes child categories from root level', function () {
    $parent = Category::factory()->create();
    Category::factory()->count(3)->create(['parent_id' => $parent->id]);

    $response = $this->getJson('/api/categories');

    $response->assertSuccessful()
        ->assertJsonCount(1, 'data');
});

it('returns empty list when no categories exist', function () {
    $response = $this->getJson('/api/categories');

    $response->assertSuccessful()
        ->assertJsonCount(0, 'data');
});
