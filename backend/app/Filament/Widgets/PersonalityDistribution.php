<?php

namespace App\Filament\Widgets;

use App\Models\User;
use App\Services\MLServiceClient;
use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Facades\Cache;

class PersonalityDistribution extends StatsOverviewWidget
{
    protected ?string $heading = 'User Personality Distribution';

    protected static ?int $sort = 2;

    protected ?string $pollingInterval = '120s';

    protected function getStats(): array
    {
        $distribution = $this->getPersonalityDistribution();

        if (empty($distribution) || $distribution['total'] === 0) {
            return [
                Stat::make('Personality Analysis', 'No Data')
                    ->description('No user personality data available yet')
                    ->color('gray'),
            ];
        }

        $stats = [];

        // Get top 4 personality types for display
        $topTypes = collect($distribution['types'])
            ->sortByDesc('count')
            ->take(4);

        $colors = [
            'adventurous_premium' => 'success',
            'cautious_value_seeker' => 'warning',
            'loyal_enthusiast' => 'primary',
            'bargain_hunter' => 'danger',
            'quality_focused' => 'info',
            'trend_follower' => 'success',
            'practical_shopper' => 'gray',
            'impulse_buyer' => 'warning',
            'unknown' => 'gray',
        ];

        $icons = [
            'adventurous_premium' => 'heroicon-o-sparkles',
            'cautious_value_seeker' => 'heroicon-o-shield-check',
            'loyal_enthusiast' => 'heroicon-o-heart',
            'bargain_hunter' => 'heroicon-o-currency-dollar',
            'quality_focused' => 'heroicon-o-star',
            'trend_follower' => 'heroicon-o-arrow-trending-up',
            'practical_shopper' => 'heroicon-o-shopping-bag',
            'impulse_buyer' => 'heroicon-o-bolt',
            'unknown' => 'heroicon-o-question-mark-circle',
        ];

        foreach ($topTypes as $type => $data) {
            $percentage = $distribution['total'] > 0
                ? round(($data['count'] / $distribution['total']) * 100, 1)
                : 0;

            $stats[] = Stat::make(ucwords(str_replace('_', ' ', $type)), $data['count'])
                ->description($percentage . '% of analyzed users')
                ->descriptionIcon($icons[$type] ?? 'heroicon-o-user')
                ->color($colors[$type] ?? 'gray');
        }

        return $stats;
    }

    protected function getPersonalityDistribution(): array
    {
        return Cache::remember('admin.personality.distribution', 300, function () {
            $mlClient = app(MLServiceClient::class);

            // Check if ML service is healthy first
            if (! $mlClient->isHealthy()) {
                return ['total' => 0, 'types' => []];
            }

            // Sample users (limit to avoid too many API calls)
            $users = User::where('is_admin', false)
                ->orderByDesc('updated_at')
                ->limit(50)
                ->pluck('id');

            $distribution = [];
            $analyzed = 0;

            foreach ($users as $userId) {
                try {
                    $personality = $mlClient->getUserPersonality($userId);
                    $type = $personality['profile']['personality_type'] ?? 'unknown';

                    if (! isset($distribution[$type])) {
                        $distribution[$type] = ['count' => 0];
                    }
                    $distribution[$type]['count']++;
                    $analyzed++;
                } catch (\Exception $e) {
                    // Skip users that fail
                    continue;
                }
            }

            return [
                'total' => $analyzed,
                'types' => $distribution,
            ];
        });
    }

    public static function canView(): bool
    {
        return true;
    }
}
