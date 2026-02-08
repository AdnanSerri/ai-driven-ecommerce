<?php

namespace App\Filament\Widgets;

use App\Models\Review;
use Carbon\Carbon;
use Filament\Widgets\ChartWidget;
use Illuminate\Support\Facades\Cache;

class SentimentTrendChart extends ChartWidget
{
    protected ?string $heading = 'Sentiment Trend (7 Days)';

    protected static ?int $sort = 6;

    protected ?string $maxHeight = '250px';

    protected function getData(): array
    {
        $data = Cache::remember('admin.sentiment.trend', 60, function () {
            $trend = [];

            for ($i = 6; $i >= 0; $i--) {
                $date = Carbon::now()->subDays($i);

                $positive = Review::whereNotNull('sentiment_label')
                    ->where('sentiment_label', 'positive')
                    ->whereDate('created_at', $date)
                    ->count();

                $negative = Review::whereNotNull('sentiment_label')
                    ->where('sentiment_label', 'negative')
                    ->whereDate('created_at', $date)
                    ->count();

                $trend[] = [
                    'date' => $date->format('M d'),
                    'positive' => $positive,
                    'negative' => $negative,
                ];
            }

            return $trend;
        });

        return [
            'datasets' => [
                [
                    'label' => 'Positive',
                    'data' => array_column($data, 'positive'),
                    'borderColor' => '#10b981',
                    'backgroundColor' => 'rgba(16, 185, 129, 0.1)',
                    'fill' => true,
                    'tension' => 0.3,
                ],
                [
                    'label' => 'Negative',
                    'data' => array_column($data, 'negative'),
                    'borderColor' => '#ef4444',
                    'backgroundColor' => 'rgba(239, 68, 68, 0.1)',
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
