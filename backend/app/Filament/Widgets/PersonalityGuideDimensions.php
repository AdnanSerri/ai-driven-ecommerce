<?php

namespace App\Filament\Widgets;

use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class PersonalityGuideDimensions extends StatsOverviewWidget
{
    protected ?string $heading = 'The 5 Behavioral Dimensions';

    protected ?string $description = 'Each user is scored 0.0 to 1.0 on these dimensions to create a behavioral fingerprint';

    protected static bool $isDiscovered = false;

    protected static ?int $sort = 2;

    protected int|string|array $columnSpan = 'full';

    protected function getColumns(): int
    {
        return 1;
    }

    protected function getStats(): array
    {
        return [
            Stat::make('Price Sensitivity (Weight: 25%)', '1 - min( avg_price / (baseline × 2) , 1.0 )')
                ->description('Baseline = $50 platform avg. Discount-adjusted. Blended with filter signals: 70% purchase history + 30% filter behavior. Min 3 filter samples required.')
                ->descriptionIcon('heroicon-o-currency-dollar')
                ->color('danger'),

            Stat::make('Exploration Tendency (Weight: 20%)', '( unique_categories / 10 + unique_products / total ) / 2')
                ->description('Category diversity capped at 10 unique categories. Product novelty = unique vs total purchases. Higher values mean more adventurous browsing.')
                ->descriptionIcon('heroicon-o-globe-alt')
                ->color('success'),

            Stat::make('Sentiment Tendency (Weight: 15%)', '( avg_rating - 1 ) / 4')
                ->description('Maps 1-5 star ratings to 0.0-1.0 scale. Users with no reviews default to 0.5 (neutral). Lowest-weighted dimension.')
                ->descriptionIcon('heroicon-o-face-smile')
                ->color('warning'),

            Stat::make('Purchase Frequency (Weight: 20%)', 'weekly = 1.0 | bi-weekly = 0.8 | monthly = 0.6 | bi-monthly = 0.4 | quarterly = 0.2')
                ->description('Based on average days between consecutive orders. Users with only one purchase default to 0.3. Beyond 90 days = 0.1.')
                ->descriptionIcon('heroicon-o-shopping-cart')
                ->color('info'),

            Stat::make('Decision Speed (Weight: 20%)', '≤30s = 1.0 | 30-60s = 0.7 | 1-3min = 0.5 | 3-5min = 0.3 | >5min = 0.1')
                ->description('Average time between first product view and purchase. Shorter times indicate impulsive behavior. Measured from interaction timestamps.')
                ->descriptionIcon('heroicon-o-clock')
                ->color('primary'),
        ];
    }
}
