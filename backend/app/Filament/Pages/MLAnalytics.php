<?php

namespace App\Filament\Pages;

use App\Filament\Widgets\InteractionBreakdown;
use App\Filament\Widgets\InteractionStats;
use App\Filament\Widgets\InteractionTrendChart;
use App\Filament\Widgets\MLServiceHealth;
use App\Filament\Widgets\PersonalityDistribution;
use App\Filament\Widgets\SentimentOverview;
use App\Filament\Widgets\SentimentTrendChart;
use BackedEnum;
use Filament\Pages\Dashboard;
use Filament\Support\Icons\Heroicon;
use UnitEnum;

class MLAnalytics extends Dashboard
{
    protected static string|BackedEnum|null $navigationIcon = Heroicon::OutlinedSparkles;

    protected static ?string $navigationLabel = 'ML Analytics';

    protected static ?string $title = 'ML Analytics Dashboard';

    protected static UnitEnum|string|null $navigationGroup = 'Analytics';

    protected static ?int $navigationSort = 1;

    protected static string $routePath = 'm-l-analytics';

    protected static ?string $slug = 'm-l-analytics';

    public function getWidgets(): array
    {
        return [
            MLServiceHealth::class,
            SentimentOverview::class,
            InteractionStats::class,
            PersonalityDistribution::class,
            InteractionBreakdown::class,
            SentimentTrendChart::class,
            InteractionTrendChart::class,
        ];
    }

    public function getColumns(): int|array
    {
        return [
            'default' => 1,
            'md' => 2,
            'lg' => 3,
        ];
    }
}
