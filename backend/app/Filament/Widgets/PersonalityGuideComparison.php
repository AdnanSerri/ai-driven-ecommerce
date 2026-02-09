<?php

namespace App\Filament\Widgets;

use App\Filament\Pages\PersonalityTypesGuide;
use Filament\Widgets\ChartWidget;

class PersonalityGuideComparison extends ChartWidget
{
    protected ?string $heading = 'Combined Profiles Overview';

    protected ?string $description = 'All 8 personality types overlaid for direct comparison — see individual charts above for detail';

    protected ?string $maxHeight = '400px';

    protected static bool $isDiscovered = false;

    protected static ?int $sort = 4;

    protected int|string|array $columnSpan = 'full';

    protected function getData(): array
    {
        $types = PersonalityTypesGuide::PERSONALITY_TYPES;
        $profiles = PersonalityTypesGuide::IDEAL_PROFILES;
        $labels = PersonalityTypesGuide::DIMENSION_LABELS;

        $colors = [
            'adventurous_premium' => ['border' => '#10b981', 'bg' => 'rgba(16, 185, 129, 0.08)'],
            'cautious_value_seeker' => ['border' => '#f59e0b', 'bg' => 'rgba(245, 158, 11, 0.08)'],
            'loyal_enthusiast' => ['border' => '#634CE9', 'bg' => 'rgba(99, 76, 233, 0.08)'],
            'bargain_hunter' => ['border' => '#f43f5e', 'bg' => 'rgba(244, 63, 94, 0.08)'],
            'quality_focused' => ['border' => '#0ea5e9', 'bg' => 'rgba(14, 165, 233, 0.08)'],
            'trend_follower' => ['border' => '#8B42D2', 'bg' => 'rgba(139, 66, 210, 0.08)'],
            'practical_shopper' => ['border' => '#6b7280', 'bg' => 'rgba(107, 114, 128, 0.08)'],
            'impulse_buyer' => ['border' => '#f97316', 'bg' => 'rgba(249, 115, 22, 0.08)'],
        ];

        $datasets = [];

        foreach ($profiles as $key => $values) {
            $color = $colors[$key] ?? ['border' => '#634CE9', 'bg' => 'rgba(99, 76, 233, 0.08)'];
            $datasets[] = [
                'label' => $types[$key]['label'],
                'data' => array_map(fn (float $v): int => (int) round($v * 100), $values),
                'borderColor' => $color['border'],
                'backgroundColor' => $color['bg'],
                'pointBackgroundColor' => $color['border'],
                'borderWidth' => 2,
            ];
        }

        return [
            'datasets' => $datasets,
            'labels' => $labels,
        ];
    }

    protected function getType(): string
    {
        return 'radar';
    }

    protected function getOptions(): array
    {
        return [
            'scales' => [
                'r' => [
                    'beginAtZero' => true,
                    'max' => 100,
                    'ticks' => [
                        'stepSize' => 25,
                        'display' => true,
                    ],
                    'pointLabels' => [
                        'font' => [
                            'size' => 13,
                        ],
                    ],
                ],
            ],
            'plugins' => [
                'legend' => [
                    'position' => 'right',
                    'labels' => [
                        'usePointStyle' => true,
                        'padding' => 12,
                    ],
                ],
            ],
        ];
    }
}
