<?php

namespace App\Filament\Widgets;

use App\Models\UserInteraction;
use Carbon\Carbon;
use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Facades\Cache;

class InteractionStats extends StatsOverviewWidget
{
    protected ?string $heading = 'User Interactions';

    protected static ?int $sort = 3;

    protected function getStats(): array
    {
        $stats = Cache::remember('admin.interaction.stats', 60, function () {
            $total = UserInteraction::count();

            if ($total === 0) {
                return null;
            }

            $today = UserInteraction::whereDate('created_at', Carbon::today())->count();
            $thisWeek = UserInteraction::where('created_at', '>=', Carbon::now()->startOfWeek())->count();
            $lastWeek = UserInteraction::whereBetween('created_at', [
                Carbon::now()->subWeek()->startOfWeek(),
                Carbon::now()->subWeek()->endOfWeek(),
            ])->count();

            $weeklyTrend = $lastWeek > 0
                ? round((($thisWeek - $lastWeek) / $lastWeek) * 100, 1)
                : ($thisWeek > 0 ? 100 : 0);

            return [
                'total' => $total,
                'today' => $today,
                'this_week' => $thisWeek,
                'weekly_trend' => $weeklyTrend,
            ];
        });

        if ($stats === null) {
            return [
                Stat::make('User Interactions', 'No Data')
                    ->description('No interaction data available yet')
                    ->color('gray'),
            ];
        }

        $trendDescription = $stats['weekly_trend'] >= 0
            ? "+{$stats['weekly_trend']}% from last week"
            : "{$stats['weekly_trend']}% from last week";

        return [
            Stat::make('Total Interactions', number_format($stats['total']))
                ->description('All time tracked interactions')
                ->descriptionIcon('heroicon-o-cursor-arrow-rays')
                ->color('primary'),

            Stat::make('Today', number_format($stats['today']))
                ->description('Interactions today')
                ->descriptionIcon('heroicon-o-calendar')
                ->color('success'),

            Stat::make('This Week', number_format($stats['this_week']))
                ->description($trendDescription)
                ->descriptionIcon($stats['weekly_trend'] >= 0 ? 'heroicon-o-arrow-trending-up' : 'heroicon-o-arrow-trending-down')
                ->color($stats['weekly_trend'] >= 0 ? 'success' : 'danger'),
        ];
    }
}
