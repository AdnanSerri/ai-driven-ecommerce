<?php

namespace App\Filament\Pages;

use App\Filament\Widgets\PersonalityGuideAlgorithm;
use App\Filament\Widgets\PersonalityGuideComparison;
use App\Filament\Widgets\PersonalityGuideDimensions;
use App\Filament\Widgets\PersonalityGuideStats;
use App\Filament\Widgets\PersonalityGuideTypeChart;
use BackedEnum;
use Filament\Pages\Dashboard;
use Filament\Support\Icons\Heroicon;
use UnitEnum;

class PersonalityTypesGuide extends Dashboard
{
    protected static string|BackedEnum|null $navigationIcon = Heroicon::OutlinedAcademicCap;

    protected static ?string $navigationLabel = 'Personality Types Guide';

    protected static ?string $title = 'Personality Types Guide';

    protected static UnitEnum|string|null $navigationGroup = 'Analytics';

    protected static ?int $navigationSort = 2;

    protected static string $routePath = 'personality-types-guide';

    protected static ?string $slug = 'personality-types-guide';

    public const PERSONALITY_TYPES = [
        'adventurous_premium' => [
            'label' => 'Adventurous Premium',
            'icon' => 'heroicon-o-sparkles',
            'color' => 'success',
            'description' => 'Explores new and premium products. Not deterred by higher prices, fast decisions.',
            'recommendation_impact' => 'Boosts: new releases, premium items. Price secondary to novelty.',
        ],
        'cautious_value_seeker' => [
            'label' => 'Cautious Value Seeker',
            'icon' => 'heroicon-o-shield-check',
            'color' => 'warning',
            'description' => 'Very price-conscious, prefers familiar well-reviewed products. Slow, deliberate.',
            'recommendation_impact' => 'Boosts: established products, best value. Familiar categories.',
        ],
        'loyal_enthusiast' => [
            'label' => 'Loyal Enthusiast',
            'icon' => 'heroicon-o-heart',
            'color' => 'primary',
            'description' => 'Strong brand loyalty, highly positive engagement. Frequent repeat purchases.',
            'recommendation_impact' => 'Boosts: previously purchased brands, new items from favorites.',
        ],
        'bargain_hunter' => [
            'label' => 'Bargain Hunter',
            'icon' => 'heroicon-o-currency-dollar',
            'color' => 'danger',
            'description' => 'Maximum price sensitivity, focused on deals/discounts. Explores for best prices.',
            'recommendation_impact' => 'Boosts: sale items, lowest prices. Wide range by deal quality.',
        ],
        'quality_focused' => [
            'label' => 'Quality Focused',
            'icon' => 'heroicon-o-star',
            'color' => 'info',
            'description' => 'Prioritizes quality over price. Thorough researcher, willing to wait.',
            'recommendation_impact' => 'Boosts: highest-rated products, quality indicators, premium tier.',
        ],
        'trend_follower' => [
            'label' => 'Trend Follower',
            'icon' => 'heroicon-o-arrow-trending-up',
            'color' => 'success',
            'description' => 'Early adopter, follows popular trends. Active purchaser of trending items.',
            'recommendation_impact' => 'Boosts: trending/popular items. Trend signals over price.',
        ],
        'practical_shopper' => [
            'label' => 'Practical Shopper',
            'icon' => 'heroicon-o-shopping-bag',
            'color' => 'gray',
            'description' => 'Buys only what is needed. Functional over aesthetic, moderate price awareness.',
            'recommendation_impact' => 'Boosts: functional essentials, good value. Need-based suggestions.',
        ],
        'impulse_buyer' => [
            'label' => 'Impulse Buyer',
            'icon' => 'heroicon-o-bolt',
            'color' => 'warning',
            'description' => 'Quick decisions driven by emotion. Attracted to new/exciting, high frequency.',
            'recommendation_impact' => 'Boosts: visually appealing, new items, limited-time offers.',
        ],
    ];

    public const IDEAL_PROFILES = [
        'adventurous_premium' => [0.2, 0.9, 0.7, 0.6, 0.8],
        'cautious_value_seeker' => [0.9, 0.3, 0.5, 0.4, 0.2],
        'loyal_enthusiast' => [0.4, 0.3, 0.8, 0.7, 0.6],
        'bargain_hunter' => [1.0, 0.7, 0.5, 0.5, 0.9],
        'quality_focused' => [0.3, 0.5, 0.6, 0.4, 0.3],
        'trend_follower' => [0.5, 0.8, 0.7, 0.7, 0.7],
        'practical_shopper' => [0.6, 0.4, 0.5, 0.3, 0.5],
        'impulse_buyer' => [0.4, 0.9, 0.6, 0.8, 1.0],
    ];

    public const DIMENSION_LABELS = [
        'Price Sensitivity',
        'Exploration',
        'Sentiment',
        'Purchase Freq.',
        'Decision Speed',
    ];

    public function getWidgets(): array
    {
        return [
            PersonalityGuideStats::class,
            PersonalityGuideAlgorithm::class,
            PersonalityGuideDimensions::class,

            // Individual personality type radar charts (2 per row)
            PersonalityGuideTypeChart::make(['personalityType' => 'adventurous_premium']),
            PersonalityGuideTypeChart::make(['personalityType' => 'cautious_value_seeker']),
            PersonalityGuideTypeChart::make(['personalityType' => 'loyal_enthusiast']),
            PersonalityGuideTypeChart::make(['personalityType' => 'bargain_hunter']),
            PersonalityGuideTypeChart::make(['personalityType' => 'quality_focused']),
            PersonalityGuideTypeChart::make(['personalityType' => 'trend_follower']),
            PersonalityGuideTypeChart::make(['personalityType' => 'practical_shopper']),
            PersonalityGuideTypeChart::make(['personalityType' => 'impulse_buyer']),

            // Combined comparison at the bottom
            PersonalityGuideComparison::class,
        ];
    }

    public function getColumns(): int|array
    {
        return [
            'default' => 1,
            'md' => 2,
        ];
    }
}
