<?php

use App\Models\Category;
use App\Models\Product;
use App\Models\Review;
use App\Models\User;
use Laravel\Sanctum\Sanctum;

it('lists user reviews', function () {
    $user = User::factory()->create();
    $category = Category::factory()->create();
    $product = Product::factory()->create(['category_id' => $category->id]);

    Review::factory()->count(5)->create([
        'user_id' => $user->id,
        'product_id' => $product->id,
    ]);

    Sanctum::actingAs($user);

    $response = $this->getJson('/api/user/reviews');

    $response->assertSuccessful()
        ->assertJsonCount(5, 'data');
});

it('only shows reviews for authenticated user', function () {
    $user1 = User::factory()->create();
    $user2 = User::factory()->create();
    $category = Category::factory()->create();
    $product = Product::factory()->create(['category_id' => $category->id]);

    Review::factory()->count(3)->create([
        'user_id' => $user1->id,
        'product_id' => $product->id,
    ]);
    Review::factory()->count(2)->create([
        'user_id' => $user2->id,
        'product_id' => $product->id,
    ]);

    Sanctum::actingAs($user1);

    $response = $this->getJson('/api/user/reviews');

    $response->assertSuccessful()
        ->assertJsonCount(3, 'data');
});

it('requires authentication to list reviews', function () {
    $response = $this->getJson('/api/user/reviews');

    $response->assertUnauthorized();
});

it('creates a review successfully', function () {
    $user = User::factory()->create();
    $category = Category::factory()->create();
    $product = Product::factory()->create(['category_id' => $category->id]);

    Sanctum::actingAs($user);

    $response = $this->postJson('/api/reviews', [
        'product_id' => $product->id,
        'rating' => 5,
        'comment' => 'This is an excellent product, highly recommended!',
    ]);

    $response->assertCreated()
        ->assertJsonPath('data.rating', 5)
        ->assertJsonPath('data.comment', 'This is an excellent product, highly recommended!');

    $this->assertDatabaseHas('reviews', [
        'user_id' => $user->id,
        'product_id' => $product->id,
        'rating' => 5,
    ]);
});

it('requires authentication to create review', function () {
    $category = Category::factory()->create();
    $product = Product::factory()->create(['category_id' => $category->id]);

    $response = $this->postJson('/api/reviews', [
        'product_id' => $product->id,
        'rating' => 5,
        'comment' => 'Great product!',
    ]);

    $response->assertUnauthorized();
});

it('validates product_id is required', function () {
    $user = User::factory()->create();
    Sanctum::actingAs($user);

    $response = $this->postJson('/api/reviews', [
        'rating' => 5,
        'comment' => 'Great product, love it!',
    ]);

    $response->assertUnprocessable()
        ->assertJsonValidationErrors(['product_id']);
});

it('validates product exists', function () {
    $user = User::factory()->create();
    Sanctum::actingAs($user);

    $response = $this->postJson('/api/reviews', [
        'product_id' => 999,
        'rating' => 5,
        'comment' => 'Great product, love it!',
    ]);

    $response->assertUnprocessable()
        ->assertJsonValidationErrors(['product_id']);
});

it('validates rating is required', function () {
    $user = User::factory()->create();
    $category = Category::factory()->create();
    $product = Product::factory()->create(['category_id' => $category->id]);

    Sanctum::actingAs($user);

    $response = $this->postJson('/api/reviews', [
        'product_id' => $product->id,
        'comment' => 'Great product, love it!',
    ]);

    $response->assertUnprocessable()
        ->assertJsonValidationErrors(['rating']);
});

it('validates rating minimum is 1', function () {
    $user = User::factory()->create();
    $category = Category::factory()->create();
    $product = Product::factory()->create(['category_id' => $category->id]);

    Sanctum::actingAs($user);

    $response = $this->postJson('/api/reviews', [
        'product_id' => $product->id,
        'rating' => 0,
        'comment' => 'Great product, love it!',
    ]);

    $response->assertUnprocessable()
        ->assertJsonValidationErrors(['rating']);
});

it('validates rating maximum is 5', function () {
    $user = User::factory()->create();
    $category = Category::factory()->create();
    $product = Product::factory()->create(['category_id' => $category->id]);

    Sanctum::actingAs($user);

    $response = $this->postJson('/api/reviews', [
        'product_id' => $product->id,
        'rating' => 6,
        'comment' => 'Great product, love it!',
    ]);

    $response->assertUnprocessable()
        ->assertJsonValidationErrors(['rating']);
});

it('validates comment is required', function () {
    $user = User::factory()->create();
    $category = Category::factory()->create();
    $product = Product::factory()->create(['category_id' => $category->id]);

    Sanctum::actingAs($user);

    $response = $this->postJson('/api/reviews', [
        'product_id' => $product->id,
        'rating' => 5,
    ]);

    $response->assertUnprocessable()
        ->assertJsonValidationErrors(['comment']);
});

it('validates comment minimum length', function () {
    $user = User::factory()->create();
    $category = Category::factory()->create();
    $product = Product::factory()->create(['category_id' => $category->id]);

    Sanctum::actingAs($user);

    $response = $this->postJson('/api/reviews', [
        'product_id' => $product->id,
        'rating' => 5,
        'comment' => 'Short',
    ]);

    $response->assertUnprocessable()
        ->assertJsonValidationErrors(['comment']);
});
