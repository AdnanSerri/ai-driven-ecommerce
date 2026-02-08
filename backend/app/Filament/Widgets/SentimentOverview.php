<?php

namespace App\Filament\Widgets;

use App\Models\Review;
use Carbon\Carbon;
use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class SentimentOverview extends StatsOverviewWidget
{
    protected ?string $heading = 'Review Sentiment Analysis';

    protected static ?int $sort = 1;

    protected function getStats(): array
    {
        $reviews = Review::whereNotNull('sentiment_label')->get();

        if ($reviews->isEmpty()) {
            return [
                Stat::make('Sentiment Analysis', 'No Data')
                    ->description('No reviews have been analyzed yet')
                    ->color('gray'),
            ];
        }

        $positive = $reviews->where('sentiment_label', 'positive')->count();
        $neutral = $reviews->where('sentiment_label', 'neutral')->count();
        $negative = $reviews->where('sentiment_label', 'negative')->count();
        $total = $reviews->count();

        $avgScore = round($reviews->avg('sentiment_score'), 2);

        // Calculate trend (this week vs last week)
        $thisWeekPositive = Review::whereNotNull('sentiment_label')
            ->where('sentiment_label', 'positive')
            ->where('created_at', '>=', Carbon::now()->startOfWeek())
            ->count();

        $lastWeekPositive = Review::whereNotNull('sentiment_label')
            ->where('sentiment_label', 'positive')
            ->whereBetween('created_at', [
                Carbon::now()->subWeek()->startOfWeek(),
                Carbon::now()->subWeek()->endOfWeek(),
            ])
            ->count();

        $trend = $lastWeekPositive > 0
            ? round((($thisWeekPositive - $lastWeekPositive) / $lastWeekPositive) * 100, 1)
            : ($thisWeekPositive > 0 ? 100 : 0);

        $trendDescription = $trend > 0 ? "+{$trend}% from last week" : "{$trend}% from last week";
        $trendIcon = $trend >= 0 ? 'heroicon-o-arrow-trending-up' : 'heroicon-o-arrow-trending-down';

        return [
            Stat::make('Positive Reviews', $positive)
                ->description(round(($positive / $total) * 100, 1) . '% of analyzed reviews')
                ->descriptionIcon('heroicon-o-face-smile')
                ->color('success')
                ->chart($this->getWeeklyTrend('positive')),

            Stat::make('Neutral Reviews', $neutral)
                ->description(round(($neutral / $total) * 100, 1) . '% of analyzed reviews')
                ->descriptionIcon('heroicon-o-minus-circle')
                ->color('warning'),

            Stat::make('Negative Reviews', $negative)
                ->description(round(($negative / $total) * 100, 1) . '% of analyzed reviews')
                ->descriptionIcon('heroicon-o-face-frown')
                ->color('danger'),

            Stat::make('Average Score', $avgScore)
                ->description($trendDescription)
                ->descriptionIcon($trendIcon)
                ->color($avgScore >= 0 ? 'success' : 'danger'),
        ];
    }

    protected function getWeeklyTrend(string $sentiment): array
    {
        $data = [];

        for ($i = 6; $i >= 0; $i--) {
            $date = Carbon::now()->subDays($i);
            $count = Review::whereNotNull('sentiment_label')
                ->where('sentiment_label', $sentiment)
                ->whereDate('created_at', $date)
                ->count();
            $data[] = $count;
        }

        return $data;
    }
}
