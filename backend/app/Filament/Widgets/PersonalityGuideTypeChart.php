<?php

namespace App\Filament\Widgets;

use App\Filament\Pages\PersonalityTypesGuide;
use Filament\Widgets\ChartWidget;
use Illuminate\Support\Facades\Cache;

class PersonalityGuideTypeChart extends ChartWidget
{
    public string $personalityType = '';

    protected ?string $maxHeight = '280px';

    protected static bool $isDiscovered = false;

    public function getHeading(): ?string
    {
        $types = PersonalityTypesGuide::PERSONALITY_TYPES;

        return $types[$this->personalityType]['label'] ?? 'Unknown';
    }

    public function getDescription(): ?string
    {
        $types = PersonalityTypesGuide::PERSONALITY_TYPES;
        $type = $types[$this->personalityType] ?? null;

        if (! $type) {
            return null;
        }

        $parts = [$type['recommendation_impact']];

        $cached = Cache::get('admin.personality-guide.stats');
        $live = ($cached['types'] ?? [])[$this->personalityType] ?? null;

        if ($live) {
            array_unshift($parts, $live['count'].' users ('.$live['percentage'].'%)');
        }

        return implode(' — ', $parts);
    }

    protected function getData(): array
    {
        $profiles = PersonalityTypesGuide::IDEAL_PROFILES;
        $labels = PersonalityTypesGuide::DIMENSION_LABELS;
        $types = PersonalityTypesGuide::PERSONALITY_TYPES;

        $profile = $profiles[$this->personalityType] ?? [0, 0, 0, 0, 0];
        $baseline = $profiles['practical_shopper'];
        $color = $this->getTypeColor();

        return [
            'datasets' => [
                [
                    'label' => $types[$this->personalityType]['label'] ?? 'Type',
                    'data' => array_map(fn (float $v): int => (int) round($v * 100), $profile),
                    'borderColor' => $color,
                    'backgroundColor' => $this->hexToRgba($color, 0.2),
                    'pointBackgroundColor' => $color,
                    'pointBorderColor' => $color,
                    'borderWidth' => 2,
                    'fill' => true,
                ],
                [
                    'label' => 'Baseline (Practical Shopper)',
                    'data' => array_map(fn (float $v): int => (int) round($v * 100), $baseline),
                    'borderColor' => 'rgba(107, 114, 128, 0.4)',
                    'backgroundColor' => 'rgba(107, 114, 128, 0.05)',
                    'pointBackgroundColor' => 'rgba(107, 114, 128, 0.4)',
                    'borderWidth' => 1,
                    'borderDash' => [5, 5],
                    'fill' => true,
                ],
            ],
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
                        'display' => false,
                    ],
                    'pointLabels' => [
                        'font' => [
                            'size' => 11,
                        ],
                    ],
                ],
            ],
            'plugins' => [
                'legend' => [
                    'position' => 'bottom',
                    'labels' => [
                        'usePointStyle' => true,
                        'padding' => 10,
                        'font' => [
                            'size' => 10,
                        ],
                    ],
                ],
            ],
        ];
    }

    protected function getTypeColor(): string
    {
        return match ($this->personalityType) {
            'adventurous_premium' => '#10b981',
            'cautious_value_seeker' => '#f59e0b',
            'loyal_enthusiast' => '#634CE9',
            'bargain_hunter' => '#f43f5e',
            'quality_focused' => '#0ea5e9',
            'trend_follower' => '#8B42D2',
            'practical_shopper' => '#6b7280',
            'impulse_buyer' => '#f97316',
            default => '#634CE9',
        };
    }

    protected function hexToRgba(string $hex, float $alpha): string
    {
        $hex = ltrim($hex, '#');
        $r = hexdec(substr($hex, 0, 2));
        $g = hexdec(substr($hex, 2, 2));
        $b = hexdec(substr($hex, 4, 2));

        return "rgba({$r}, {$g}, {$b}, {$alpha})";
    }
}
