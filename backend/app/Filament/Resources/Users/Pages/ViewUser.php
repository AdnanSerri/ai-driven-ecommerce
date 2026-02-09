<?php

namespace App\Filament\Resources\Users\Pages;

use App\Filament\Resources\Users\UserResource;
use App\Filament\Widgets\PersonalityDimensionsChart;
use App\Services\MLServiceClient;
use Filament\Actions\Action;
use Filament\Actions\EditAction;
use Filament\Infolists\Components\TextEntry;
use Filament\Resources\Pages\ViewRecord;
use Filament\Schemas\Components\Grid;
use Filament\Schemas\Components\Livewire;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Components\Tabs;
use Filament\Schemas\Schema;
use Filament\Support\Enums\FontWeight;

class ViewUser extends ViewRecord
{
    protected static string $resource = UserResource::class;

    private const PERSONALITY_DESCRIPTIONS = [
        'adventurous_premium' => 'Loves exploring new and premium products, making quick decisions with confidence.',
        'cautious_value_seeker' => 'Carefully evaluates products for the best value, prioritizing quality ratings and deals.',
        'loyal_enthusiast' => 'Sticks with brands they trust and engages deeply with favorite products.',
        'bargain_hunter' => 'Always on the lookout for the best deals and discounts.',
        'quality_focused' => 'Quality matters most — thoroughly researches before purchasing.',
        'trend_follower' => 'Stays ahead of the curve, often among the first to try what\'s popular.',
        'practical_shopper' => 'Takes a balanced approach, weighing value, quality, and practicality.',
        'impulse_buyer' => 'Spontaneous and excited by new arrivals and limited-time offers.',
    ];

    protected function getHeaderActions(): array
    {
        return [
            EditAction::make(),
        ];
    }

    public function infolist(Schema $schema): Schema
    {
        $personalityData = $this->getPersonalityData();
        $traitsData = $this->getTraitsData();

        return $schema
            ->components([
                Tabs::make('User')
                    ->tabs([
                        Tabs\Tab::make('User Information')
                            ->icon('heroicon-o-user')
                            ->schema([
                                Grid::make(3)
                                    ->schema([
                                        TextEntry::make('name')
                                            ->label('Name')
                                            ->weight(FontWeight::Bold),
                                        TextEntry::make('email')
                                            ->label('Email')
                                            ->icon('heroicon-o-envelope'),
                                        TextEntry::make('is_admin')
                                            ->label('Role')
                                            ->formatStateUsing(fn ($state) => $state ? 'Administrator' : 'Customer')
                                            ->badge()
                                            ->color(fn ($state) => $state ? 'danger' : 'gray'),
                                    ]),
                                Grid::make(2)
                                    ->schema([
                                        TextEntry::make('created_at')
                                            ->label('Registered')
                                            ->dateTime(),
                                        TextEntry::make('updated_at')
                                            ->label('Last Updated')
                                            ->dateTime(),
                                    ]),
                            ]),

                        Tabs\Tab::make('Activity Summary')
                            ->icon('heroicon-o-chart-bar')
                            ->schema([
                                Grid::make(4)
                                    ->schema([
                                        TextEntry::make('reviews_count')
                                            ->label('Reviews')
                                            ->state(fn ($record) => $record->reviews()->count())
                                            ->icon('heroicon-o-star'),
                                        TextEntry::make('orders_count')
                                            ->label('Orders')
                                            ->state(fn ($record) => $record->orders()->count())
                                            ->icon('heroicon-o-shopping-cart'),
                                        TextEntry::make('wishlist_count')
                                            ->label('Wishlist Items')
                                            ->state(fn ($record) => $record->wishlists()->count())
                                            ->icon('heroicon-o-heart'),
                                        TextEntry::make('addresses_count')
                                            ->label('Addresses')
                                            ->state(fn ($record) => $record->addresses()->count())
                                            ->icon('heroicon-o-map-pin'),
                                    ]),
                            ]),

                        Tabs\Tab::make('ML Personality Profile')
                            ->icon('heroicon-o-sparkles')
                            ->schema([
                                Section::make('Personality Overview')
                                    ->description(
                                        ! empty($personalityData['last_updated'])
                                            ? 'Last calculated: '.date('M j, Y \a\t g:i A', strtotime($personalityData['last_updated']))
                                            : 'AI-powered personality classification'
                                    )
                                    ->headerActions([
                                        Action::make('refreshPersonality')
                                            ->label('Refresh')
                                            ->icon('heroicon-o-arrow-path')
                                            ->color('primary')
                                            ->iconButton()
                                            ->action(function () {
                                                app(MLServiceClient::class)->getUserPersonality($this->record->id, forceRecalculate: true);
                                                $this->js('window.location.reload()');
                                            }),
                                    ])
                                    ->schema($this->getPersonalitySchema($personalityData, $traitsData)),
                            ]),

                        Tabs\Tab::make('User Interactions')
                            ->icon('heroicon-o-cursor-arrow-rays')
                            ->schema($this->getInteractionSchema()),
                    ])
                    ->persistTabInQueryString()
                    ->columnSpanFull(),
            ]);
    }

    protected function getPersonalityData(): ?array
    {
        try {
            $mlClient = app(MLServiceClient::class);
            $response = $mlClient->getUserPersonality($this->record->id);

            return $response['profile'] ?? null;
        } catch (\Exception $e) {
            return null;
        }
    }

    protected function getTraitsData(): ?array
    {
        try {
            $mlClient = app(MLServiceClient::class);

            return $mlClient->getUserPersonalityTraits($this->record->id);
        } catch (\Exception $e) {
            return null;
        }
    }

    protected function getPersonalitySchema(?array $personalityData, ?array $traitsData): array
    {
        if (! $personalityData || ! isset($personalityData['personality_type'])) {
            return [
                TextEntry::make('no_personality')
                    ->label('')
                    ->state('No personality profile available yet. The user needs more interactions to build a profile.')
                    ->icon('heroicon-o-information-circle')
                    ->color('gray'),
            ];
        }

        $dimensions = $personalityData['dimensions'] ?? [];
        $dataPoints = $personalityData['data_points'] ?? 0;
        $personalityType = $personalityData['personality_type'];

        $schema = [
            Grid::make(3)
                ->schema([
                    TextEntry::make('personality_type')
                        ->label('Personality Type')
                        ->state($this->formatPersonalityType($personalityType))
                        ->badge()
                        ->color($this->getPersonalityColor($personalityType)),
                    TextEntry::make('confidence')
                        ->label('Confidence')
                        ->state(number_format(($personalityData['confidence'] ?? 0) * 100, 1).'%')
                        ->icon('heroicon-o-chart-bar'),
                    TextEntry::make('interaction_count')
                        ->label('Data Points')
                        ->state($dataPoints.' ('.$this->getDataQualityLabel($dataPoints).')')
                        ->icon('heroicon-o-cursor-arrow-rays'),
                ]),

            TextEntry::make('personality_description')
                ->label('Description')
                ->state(self::PERSONALITY_DESCRIPTIONS[$personalityType] ?? 'Shopping personality is being analyzed.')
                ->icon('heroicon-o-information-circle'),
        ];

        // Shopping Traits
        $traits = $traitsData['traits'] ?? [];
        if (! empty($traits)) {
            $schema[] = Section::make('Shopping Traits')
                ->description('Behavioral characteristics derived from shopping patterns')
                ->icon('heroicon-o-sparkles')
                ->schema(
                    collect($traits)->map(fn (string $trait, int $index) => TextEntry::make("trait_{$index}")
                        ->hiddenLabel()
                        ->state($trait)
                        ->icon('heroicon-o-check-circle')
                    )->toArray()
                )
                ->compact()
                ->collapsible();
        }

        // Personality Dimensions
        $schema[] = Section::make('Personality Dimensions')
            ->description('Scored dimensions that define the personality classification')
            ->icon('heroicon-o-chart-bar-square')
            ->schema([
                Livewire::make(PersonalityDimensionsChart::class),
            ])
            ->collapsible();

        // Recommendation Impact
        $impact = $traitsData['recommendations_impact'] ?? [];
        if (! empty($impact)) {
            $impactEntries = [];

            if (! empty($impact['product_selection'])) {
                $impactEntries[] = TextEntry::make('impact_products')
                    ->label('Products')
                    ->state($impact['product_selection'])
                    ->icon('heroicon-o-shopping-bag');
            }

            if (! empty($impact['pricing'])) {
                $impactEntries[] = TextEntry::make('impact_pricing')
                    ->label('Pricing')
                    ->state($impact['pricing'])
                    ->icon('heroicon-o-currency-dollar');
            }

            if (! empty($impact['categories'])) {
                $impactEntries[] = TextEntry::make('impact_categories')
                    ->label('Categories')
                    ->state($impact['categories'])
                    ->icon('heroicon-o-tag');
            }

            if (! empty($impactEntries)) {
                $schema[] = Section::make('Recommendation Impact')
                    ->description('How this personality affects product recommendations')
                    ->icon('heroicon-o-adjustments-horizontal')
                    ->schema($impactEntries)
                    ->compact()
                    ->collapsible();
            }
        }

        return $schema;
    }

    protected function getDataQualityLabel(int $dataPoints): string
    {
        if ($dataPoints >= 50) {
            return 'Comprehensive';
        }
        if ($dataPoints >= 20) {
            return 'Good';
        }
        if ($dataPoints >= 10) {
            return 'Growing';
        }

        return 'Limited';
    }

    protected function formatPersonalityType(string $type): string
    {
        return ucwords(str_replace('_', ' ', $type));
    }

    protected function getPersonalityColor(string $type): string
    {
        return match ($type) {
            'adventurous_premium' => 'success',
            'cautious_value_seeker' => 'warning',
            'loyal_enthusiast' => 'primary',
            'bargain_hunter' => 'danger',
            'quality_focused' => 'info',
            'trend_follower' => 'success',
            'practical_shopper' => 'gray',
            'impulse_buyer' => 'warning',
            default => 'gray',
        };
    }

    protected function getInteractionSchema(): array
    {
        $interactions = $this->record->interactions();
        $totalCount = $interactions->count();

        if ($totalCount === 0) {
            return [
                TextEntry::make('no_interactions')
                    ->label('')
                    ->state('No interaction data available for this user.')
                    ->icon('heroicon-o-information-circle')
                    ->color('gray'),
            ];
        }

        $viewCount = $this->record->interactions()->where('interaction_type', 'view')->count();
        $clickCount = $this->record->interactions()->where('interaction_type', 'click')->count();
        $cartCount = $this->record->interactions()->where('interaction_type', 'add_to_cart')->count();
        $purchaseCount = $this->record->interactions()->where('interaction_type', 'purchase')->count();
        $wishlistCount = $this->record->interactions()->where('interaction_type', 'wishlist')->count();

        $topCategories = $this->record->interactions()
            ->join('products', 'user_interactions.product_id', '=', 'products.id')
            ->join('categories', 'products.category_id', '=', 'categories.id')
            ->selectRaw('categories.name, count(*) as count')
            ->groupBy('categories.name')
            ->orderByDesc('count')
            ->limit(3)
            ->pluck('count', 'name')
            ->toArray();

        $recentInteractions = $this->record->interactions()
            ->with('product')
            ->orderByDesc('created_at')
            ->limit(5)
            ->get();

        $schema = [
            Grid::make(5)
                ->schema([
                    TextEntry::make('view_count')
                        ->label('Views')
                        ->state($viewCount)
                        ->icon('heroicon-o-eye')
                        ->color('info'),
                    TextEntry::make('click_count')
                        ->label('Clicks')
                        ->state($clickCount)
                        ->icon('heroicon-o-cursor-arrow-rays')
                        ->color('primary'),
                    TextEntry::make('cart_count')
                        ->label('Add to Cart')
                        ->state($cartCount)
                        ->icon('heroicon-o-shopping-cart')
                        ->color('warning'),
                    TextEntry::make('wishlist_int_count')
                        ->label('Wishlist')
                        ->state($wishlistCount)
                        ->icon('heroicon-o-heart')
                        ->color('danger'),
                    TextEntry::make('purchase_count')
                        ->label('Purchases')
                        ->state($purchaseCount)
                        ->icon('heroicon-o-check-circle')
                        ->color('success'),
                ]),
        ];

        if (! empty($topCategories)) {
            $categoryText = collect($topCategories)
                ->map(fn ($count, $name) => "{$name} ({$count})")
                ->implode(', ');

            $schema[] = TextEntry::make('top_categories')
                ->label('Top Categories')
                ->state($categoryText)
                ->icon('heroicon-o-folder');
        }

        if ($recentInteractions->isNotEmpty()) {
            $schema[] = Section::make('Recent Activity')
                ->schema(
                    $recentInteractions->map(function ($interaction, $index) {
                        $productName = $interaction->product?->name ?? 'Unknown Product';
                        $type = ucwords(str_replace('_', ' ', $interaction->interaction_type));
                        $time = $interaction->created_at->diffForHumans();

                        return TextEntry::make("recent_{$index}")
                            ->label($time)
                            ->state("{$type}: {$productName}")
                            ->icon($this->getInteractionIcon($interaction->interaction_type));
                    })->toArray()
                )
                ->compact()
                ->collapsible();
        }

        return $schema;
    }

    protected function getInteractionIcon(string $type): string
    {
        return match ($type) {
            'view' => 'heroicon-o-eye',
            'click' => 'heroicon-o-cursor-arrow-rays',
            'add_to_cart' => 'heroicon-o-shopping-cart',
            'remove_from_cart' => 'heroicon-o-x-circle',
            'purchase' => 'heroicon-o-check-circle',
            'wishlist' => 'heroicon-o-heart',
            'review' => 'heroicon-o-star',
            default => 'heroicon-o-cursor-arrow-rays',
        };
    }
}
