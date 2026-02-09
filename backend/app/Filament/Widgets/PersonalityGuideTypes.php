<?php

namespace App\Filament\Widgets;

use App\Filament\Pages\PersonalityTypesGuide;
use Filament\Widgets\StatsOverviewWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Facades\Cache;

class PersonalityGuideTypes extends StatsOverviewWidget
{
    protected ?string $heading = 'Personality Types Catalog';

    protected ?string $description = '8 types with ideal dimension profiles (sparkline: PS, ET, ST, PF, DS)';

    protected static bool $isDiscovered = false;

    protected static ?int $sort = 3;

    protected int|string|array $columnSpan = 'full';

    protected function getColumns(): int
    {
        return 2;
    }

    protected function getStats(): array
    {
        $liveStats = $this->getLiveStats();
        $types = PersonalityTypesGuide::PERSONALITY_TYPES;
        $profiles = PersonalityTypesGuide::IDEAL_PROFILES;

        $stats = [];

        foreach ($types as $key => $type) {
            $live = $liveStats[$key] ?? null;
            $profile = $profiles[$key];

            $value = $live
                ? $live['count'].' users ('.$live['percentage'].'%)'
                : 'No data';

            $description = $type['description'];
            if ($live) {
                $description .= ' | Confidence: '.$live['avg_confidence'];
            }

            $stats[] = Stat::make($type['label'], $value)
                ->description($description)
                ->descriptionIcon($type['icon'])
                ->chart(array_map(fn (float $v): int => (int) round($v * 100), $profile))
                ->color($type['color']);
        }

        return $stats;
    }

    protected function getLiveStats(): array
    {
        $cached = Cache::get('admin.personality-guide.stats');

        return $cached['types'] ?? [];
    }
}
