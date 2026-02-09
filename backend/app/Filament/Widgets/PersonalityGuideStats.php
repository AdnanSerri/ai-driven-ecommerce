<?php

namespace App\Filament\Widgets;

use App\Models\User;
use App\Services\MLServiceClient;
use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

class PersonalityGuideStats extends StatsOverviewWidget
{
    protected ?string $heading = 'Live Statistics';

    protected static bool $isDiscovered = false;

    protected static ?int $sort = 0;

    protected int|string|array $columnSpan = 'full';

    protected function getStats(): array
    {
        $stats = $this->fetchStats();

        return [
            Stat::make('Users Analyzed', $stats['total'])
                ->description('Most recent non-admin users sampled')
                ->descriptionIcon('heroicon-o-users')
                ->color('primary'),

            Stat::make('Active Types Found', $stats['active_types'].' / 8')
                ->description('Distinct personality types detected')
                ->descriptionIcon('heroicon-o-squares-2x2')
                ->color('success'),

            Stat::make('ML Service', $stats['healthy'] ? 'Connected' : 'Unavailable')
                ->description($stats['healthy'] ? 'Personality classification active' : 'Stats show cached or no data')
                ->descriptionIcon($stats['healthy'] ? 'heroicon-o-signal' : 'heroicon-o-signal-slash')
                ->color($stats['healthy'] ? 'success' : 'danger'),
        ];
    }

    protected function fetchStats(): array
    {
        return Cache::remember('admin.personality-guide.stats', 300, function () {
            try {
                $mlClient = app(MLServiceClient::class);

                if (! $mlClient->isHealthy()) {
                    return ['healthy' => false, 'total' => 0, 'active_types' => 0, 'types' => []];
                }

                $users = User::where('is_admin', false)
                    ->orderByDesc('updated_at')
                    ->limit(50)
                    ->pluck('id');

                $typeStats = [];
                $analyzed = 0;

                foreach ($users as $userId) {
                    try {
                        $personality = $mlClient->getUserPersonality($userId);
                        $profile = $personality['profile'] ?? [];
                        $type = $profile['personality_type'] ?? 'unknown';
                        $confidence = (float) ($profile['confidence'] ?? 0);
                        $dataPoints = (int) ($profile['data_points'] ?? 0);

                        if (! isset($typeStats[$type])) {
                            $typeStats[$type] = [
                                'count' => 0,
                                'confidences' => [],
                                'data_points' => [],
                            ];
                        }

                        $typeStats[$type]['count']++;
                        $typeStats[$type]['confidences'][] = $confidence;
                        $typeStats[$type]['data_points'][] = $dataPoints;
                        $analyzed++;
                    } catch (\Exception $e) {
                        continue;
                    }
                }

                $processed = [];

                foreach ($typeStats as $type => $data) {
                    $confidences = $data['confidences'];
                    $processed[$type] = [
                        'count' => $data['count'],
                        'percentage' => $analyzed > 0 ? round(($data['count'] / $analyzed) * 100, 1) : 0,
                        'avg_confidence' => count($confidences) > 0
                            ? round(array_sum($confidences) / count($confidences), 2)
                            : 0,
                        'avg_data_points' => count($data['data_points']) > 0
                            ? (int) round(array_sum($data['data_points']) / count($data['data_points']))
                            : 0,
                    ];
                }

                return [
                    'healthy' => true,
                    'total' => $analyzed,
                    'active_types' => count(array_filter(
                        array_keys($processed),
                        fn (string $t): bool => $t !== 'unknown'
                    )),
                    'types' => $processed,
                ];
            } catch (\Exception $e) {
                Log::warning('Failed to fetch personality guide stats', ['error' => $e->getMessage()]);

                return ['healthy' => false, 'total' => 0, 'active_types' => 0, 'types' => []];
            }
        });
    }
}
