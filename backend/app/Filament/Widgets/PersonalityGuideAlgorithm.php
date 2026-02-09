<?php

namespace App\Filament\Widgets;

use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class PersonalityGuideAlgorithm extends StatsOverviewWidget
{
    protected ?string $heading = 'Classification Algorithm & Parameters';

    protected ?string $description = '5-dimensional behavioral analysis with weighted Euclidean distance classification';

    protected static bool $isDiscovered = false;

    protected static ?int $sort = 1;

    protected int|string|array $columnSpan = 'full';

    protected function getColumns(): int
    {
        return 2;
    }

    protected function getStats(): array
    {
        return [
            Stat::make('Classification', 'Weighted Euclidean Distance')
                ->description('distance = sqrt(sum(w_i * (user_i - profile_i)^2))')
                ->descriptionIcon('heroicon-o-cpu-chip')
                ->color('primary'),

            Stat::make('Confidence Score', '1 - distance')
                ->description('0.0 (no match) to 1.0 (perfect match)')
                ->descriptionIcon('heroicon-o-check-badge')
                ->color('info'),

            Stat::make('Cold Start Default', 'practical_shopper')
                ->description('Assigned at 0.3 confidence when < 5 data points')
                ->descriptionIcon('heroicon-o-user-plus')
                ->color('gray'),

            Stat::make('Default Alpha', '0.4')
                ->description('final = 0.4*personality + 0.6*behavioral')
                ->descriptionIcon('heroicon-o-adjustments-horizontal')
                ->color('primary'),

            Stat::make('Alpha Range', '0.1 - 0.9')
                ->description('Clamped to prevent extreme values')
                ->descriptionIcon('heroicon-o-arrows-right-left')
                ->color('gray'),

            Stat::make('Sparse Data Boost', '+0.20 alpha')
                ->description('When < 5% collaborative filtering coverage')
                ->descriptionIcon('heroicon-o-arrow-trending-up')
                ->color('info'),

            Stat::make('New User Boost', '+0.15 alpha')
                ->description('When user has < 10 interactions')
                ->descriptionIcon('heroicon-o-user-plus')
                ->color('info'),

            Stat::make('Filter Signal Weight', '30%')
                ->description('70% purchase + 30% filter behavior blending')
                ->descriptionIcon('heroicon-o-funnel')
                ->color('warning'),
        ];
    }
}
