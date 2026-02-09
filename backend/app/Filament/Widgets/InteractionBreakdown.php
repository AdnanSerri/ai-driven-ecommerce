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
                        'backgroundColor' => ['rgba(99, 76, 233, 0.15)'],
                    ],
                ],
                'labels' => ['No Data'],
            ];
        }

        $labels = array_map(fn ($type) => ucwords(str_replace('_', ' ', $type)), array_keys($data));
        $values = array_values($data);

        $colors = [
            '#634CE9', // primary indigo
            '#10b981', // success emerald
            '#f59e0b', // warning amber
            '#f43f5e', // danger rose
            '#8B42D2', // violet (gradient end)
            '#0ea5e9', // info sky
            '#6D42E0', // violet (gradient mid)
            '#84cc16', // lime
            '#f97316', // orange
            '#8178F6', // primary light
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
