<?php

namespace App\Filament\Widgets;

use App\Models\UserInteraction;
use Filament\Widgets\ChartWidget;
use Illuminate\Support\Facades\Cache;

class InteractionBreakdown extends ChartWidget
{
    protected ?string $heading = 'Interaction Breakdown';

    protected ?string $description = 'User behavior tracking by interaction type';

    protected static ?int $sort = 4;

    protected ?string $maxHeight = '300px';

    protected function getData(): array
    {
        $data = Cache::remember('admin.interaction.breakdown', 60, function () {
            return UserInteraction::selectRaw('interaction_type, count(*) as count')
                ->groupBy('interaction_type')
                ->orderByDesc('count')
                ->pluck('count', 'interaction_type')
                ->toArray();
        });

        if (empty($data)) {
            return [
                'datasets' => [
                    [
                        'data' => [1],
                        'backgroundColor' => ['#e5e7eb'],
                    ],
                ],
                'labels' => ['No Data'],
            ];
        }

        $labels = array_map(fn ($type) => ucwords(str_replace('_', ' ', $type)), array_keys($data));
        $values = array_values($data);

        $colors = [
            '#3b82f6', // blue
            '#10b981', // green
            '#f59e0b', // amber
            '#ef4444', // red
            '#8b5cf6', // violet
            '#ec4899', // pink
            '#06b6d4', // cyan
            '#84cc16', // lime
            '#f97316', // orange
            '#6366f1', // indigo
        ];

        return [
            'datasets' => [
                [
                    'data' => $values,
                    'backgroundColor' => array_slice($colors, 0, count($values)),
                ],
            ],
            'labels' => $labels,
        ];
    }

    protected function getType(): string
    {
        return 'doughnut';
    }

    protected function getOptions(): array
    {
        return [
            'plugins' => [
                'legend' => [
                    'position' => 'right',
                ],
            ],
        ];
    }
}
