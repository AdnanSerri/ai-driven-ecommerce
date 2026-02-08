<?php

namespace App\Filament\Widgets;

use App\Models\Category;
use App\Models\Order;
use App\Models\Product;
use App\Models\Review;
use App\Models\User;
use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class StatsOverview extends StatsOverviewWidget
{
    protected function getStats(): array
    {
        return [
            Stat::make('Total Users', User::count())
                ->description('Registered users')
                ->descriptionIcon('heroicon-o-users')
                ->color('primary'),
            Stat::make('Total Products', Product::count())
                ->description('Available products')
                ->descriptionIcon('heroicon-o-shopping-bag')
                ->color('success'),
            Stat::make('Total Orders', Order::count())
                ->description('Orders placed')
                ->descriptionIcon('heroicon-o-shopping-cart')
                ->color('warning'),
            Stat::make('Total Reviews', Review::count())
                ->description('Customer reviews')
                ->descriptionIcon('heroicon-o-star')
                ->color('info'),
        ];
    }
}
