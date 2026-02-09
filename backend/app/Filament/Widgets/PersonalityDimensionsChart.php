<?php

namespace App\Filament\Widgets;

use App\Services\MLServiceClient;
use Filament\Widgets\ChartWidget;
use Illuminate\Database\Eloquent\Model;

class PersonalityDimensionsChart extends ChartWidget
{
    protected ?string $heading = null;

    protected ?string $maxHeight = '300px';

    protected static bool $isDiscovered = false;

    public ?Model $record = null;

    protected function getData(): array
    {
        $dimensions = $this->getDimensions();

        if (empty($dimensions)) {
            return [
                'datasets' => [
                    [
                        'data' => [0, 0, 0, 0, 0],
                        'backgroundColor' => 'rgba(99, 76, 233, 0.15)',
                        'borderColor' => '#634CE9',
                        'pointBackgroundColor' => '#634CE9',
                    ],
                ],
                'labels' => ['Price Sensitivity', 'Exploration', 'Sentiment', 'Purchase Frequency', 'Decision Speed'],
            ];
        }

        return [
            'datasets' => [
                [
                    'label' => 'Score',
                    'data' => [
                        round(($dimensions['price_sensitivity'] ?? 0) * 100),
                        round(($dimensions['exploration_tendency'] ?? 0) * 100),
                        round(($dimensions['sentiment_tendency'] ?? 0) * 100),
                        round(($dimensions['purchase_frequency'] ?? 0) * 100),
                        round(($dimensions['decision_speed'] ?? 0) * 100),
                    ],
                    'backgroundColor' => 'rgba(99, 76, 233, 0.2)',
                    'borderColor' => '#634CE9',
                    'pointBackgroundColor' => '#634CE9',
                    'pointBorderColor' => '#634CE9',
                    'pointHoverBackgroundColor' => '#8B42D2',
                    'borderWidth' => 2,
                ],
            ],
            'labels' => ['Price Sensitivity', 'Exploration', 'Sentiment', 'Purchase Frequency', 'Decision Speed'],
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
                            'size' => 12,
                        ],
                    ],
                ],
            ],
            'plugins' => [
                'legend' => [
                    'display' => false,
                ],
            ],
        ];
    }

    protected function getDimensions(): array
    {
        if (! $this->record) {
            return [];
        }

        try {
            $mlClient = app(MLServiceClient::class);
            $response = $mlClient->getUserPersonality($this->record->id);

            return $response['profile']['dimensions'] ?? [];
        } catch (\Exception $e) {
            return [];
        }
    }
}
