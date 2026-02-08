<?php

namespace App\Filament\Widgets;

use App\Services\MLServiceClient;
use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Facades\Cache;

class MLServiceHealth extends StatsOverviewWidget
{
    protected ?string $pollingInterval = '30s';

    protected static ?int $sort = 0;

    protected function getStats(): array
    {
        $mlClient = app(MLServiceClient::class);
        $cacheKey = 'ml.service.health';

        // Cache health check for 30 seconds to avoid excessive calls
        $healthData = Cache::remember($cacheKey, 30, function () use ($mlClient) {
            $startTime = microtime(true);
            $isHealthy = $mlClient->isHealthy();
            $responseTime = round((microtime(true) - $startTime) * 1000);

            return [
                'healthy' => $isHealthy,
                'response_time' => $responseTime,
                'checked_at' => now(),
            ];
        });

        $statusStat = $healthData['healthy']
            ? Stat::make('ML Service', 'Connected')
                ->description('Service is healthy')
                ->descriptionIcon('heroicon-o-check-circle')
                ->color('success')
            : Stat::make('ML Service', 'Disconnected')
                ->description('Service unavailable')
                ->descriptionIcon('heroicon-o-x-circle')
                ->color('danger');

        $responseTimeStat = Stat::make('Response Time', $healthData['response_time'] . 'ms')
            ->description('Last health check')
            ->descriptionIcon('heroicon-o-clock')
            ->color($healthData['response_time'] < 500 ? 'success' : ($healthData['response_time'] < 1000 ? 'warning' : 'danger'));

        $lastCheckStat = Stat::make('Last Check', $healthData['checked_at']->diffForHumans())
            ->description($healthData['checked_at']->format('H:i:s'))
            ->descriptionIcon('heroicon-o-arrow-path')
            ->color('gray');

        return [$statusStat, $responseTimeStat, $lastCheckStat];
    }

    public static function canView(): bool
    {
        return true;
    }
}
