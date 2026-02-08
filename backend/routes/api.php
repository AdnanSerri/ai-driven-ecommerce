<?php

use App\Http\Controllers\Api\AddressController;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\CartController;
use App\Http\Controllers\Api\CategoryController;
use App\Http\Controllers\Api\CheckoutController;
use App\Http\Controllers\Api\InteractionController;
use App\Http\Controllers\Api\OrderController;
use App\Http\Controllers\Api\PersonalityController;
use App\Http\Controllers\Api\ProductController;
use App\Http\Controllers\Api\ProfileController;
use App\Http\Controllers\Api\RecommendationController;
use App\Http\Controllers\Api\ReviewController;
use App\Http\Controllers\Api\WishlistController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
*/

// Authentication routes
Route::post('/register', [AuthController::class, 'register']);
Route::post('/login', [AuthController::class, 'login']);

// Public routes
Route::get('/products', [ProductController::class, 'index']);
Route::get('/products/{product}', [ProductController::class, 'show']);
Route::get('/categories', [CategoryController::class, 'index']);
Route::get('/products/{product}/reviews', [ReviewController::class, 'productReviews']);

// Protected routes
Route::middleware('auth:sanctum')->group(function () {
    Route::post('/logout', [AuthController::class, 'logout']);

    // User reviews
    Route::get('/user/reviews', [ReviewController::class, 'index']);
    Route::post('/reviews', [ReviewController::class, 'store']);

    // Cart
    Route::get('/cart', [CartController::class, 'show']);
    Route::post('/cart/items', [CartController::class, 'addItem']);
    Route::put('/cart/items/{cartItem}', [CartController::class, 'updateItem']);
    Route::delete('/cart/items/{cartItem}', [CartController::class, 'removeItem']);
    Route::delete('/cart', [CartController::class, 'clear']);

    // Checkout
    Route::post('/checkout', [CheckoutController::class, 'store']);

    // Orders
    Route::get('/orders', [OrderController::class, 'index']);
    Route::get('/orders/{order}', [OrderController::class, 'show']);
    Route::post('/orders/{order}/cancel', [OrderController::class, 'cancel']);

    // Wishlist
    Route::get('/wishlist', [WishlistController::class, 'index']);
    Route::post('/wishlist', [WishlistController::class, 'store']);
    Route::delete('/wishlist/{product}', [WishlistController::class, 'destroy']);

    // Addresses
    Route::apiResource('addresses', AddressController::class);
    Route::post('/addresses/{address}/default', [AddressController::class, 'setDefault']);

    // Profile
    Route::get('/user/profile', [ProfileController::class, 'show']);
    Route::put('/user/profile', [ProfileController::class, 'update']);

    // Recommendations (ML Service)
    Route::get('/recommendations', [RecommendationController::class, 'index']);
    Route::get('/products/{product}/similar', [RecommendationController::class, 'similar']);
    Route::post('/recommendations/feedback', [RecommendationController::class, 'feedback']);

    // Personality (ML Service)
    Route::get('/user/personality', [PersonalityController::class, 'profile']);
    Route::get('/user/personality/traits', [PersonalityController::class, 'traits']);
    Route::post('/user/personality/interaction', [PersonalityController::class, 'recordInteraction']);

    // User Interactions (Kafka events)
    Route::post('/interactions', [InteractionController::class, 'track']);
});
