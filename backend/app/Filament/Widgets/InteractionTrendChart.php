<?php

namespace App\Filament\Widgets;

use App\Models\UserInteraction;
use Carbon\Carbon;
use Filament\Widgets\ChartWidget;
use Illuminate\Support\Facades\Cache;

class InteractionTrendChart extends ChartWidget
{
    protected ?string $heading = 'Interaction Trend (7 Days)';

    protected static ?int $sort = 5;

    protected ?string $maxHeight = '250px';

    protected function getData(): array
    {
        $data = Cache::remember('admin.interaction.trend', 60, function () {
            $trend = [];

            for ($i = 6; $i >= 0; $i--) {
                $date = Carbon::now()->subDays($i);
                $count = UserInteraction::whereDate('created_at', $date)->count();
                $trend[] = [
                    'date' => $date->format('M d'),
                    'count' => $count,
                ];
            }

            return $trend;
        });

        return [
            'datasets' => [
                [
                    'label' => 'Interactions',
                    'data' => array_column($data, 'count'),
                    'borderColor' => '#3b82f6',
                    'backgroundColor' => 'rgba(59, 130, 246, 0.1)',
                    'fill' => true,
                    'tension' => 0.3,
                ],
            ],
            'labels' => array_column($data, 'date'),
        ];
    }

    protected function getType(): string
    {
        return 'line';
    }
}
