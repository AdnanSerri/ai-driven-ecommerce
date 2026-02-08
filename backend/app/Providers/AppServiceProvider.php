<?php

namespace App\Providers;

use App\Models\Product;
use App\Models\Review;
use App\Observers\ProductObserver;
use App\Observers\ReviewObserver;
use App\Services\KafkaProducerService;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        $this->app->singleton(KafkaProducerService::class);
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        Product::observe(ProductObserver::class);
        Review::observe(ReviewObserver::class);
    }
}
