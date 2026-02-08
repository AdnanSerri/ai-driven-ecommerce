<?php

namespace App\Filament\Resources\Users\Pages;

use App\Filament\Resources\Users\UserResource;
use App\Services\MLServiceClient;
use Filament\Actions\EditAction;
use Filament\Infolists\Components\TextEntry;
use Filament\Resources\Pages\ViewRecord;
use Filament\Schemas\Components\Grid;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;
use Filament\Support\Enums\FontWeight;

class ViewUser extends ViewRecord
{
    protected static string $resource = UserResource::class;

    protected function getHeaderActions(): array
    {
        return [
            EditAction::make(),
        ];
    }

    public function infolist(Schema $schema): Schema
    {
        $personalityData = $this->getPersonalityData();

        return $schema
            ->components([
                Section::make('User Information')
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

                Section::make('ML Personality Profile')
                    ->description('AI-powered personality classification based on shopping behavior')
                    ->icon('heroicon-o-sparkles')
                    ->schema($this->getPersonalitySchema($personalityData))
                    ->collapsible(),

                Section::make('Activity Summary')
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
                    ])
                    ->collapsible(),

                Section::make('User Interactions')
                    ->description('Tracked user behavior from browsing and shopping activity')
                    ->icon('heroicon-o-cursor-arrow-rays')
                    ->schema($this->getInteractionSchema())
                    ->collapsible(),
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

    protected function getPersonalitySchema(?array $personalityData): array
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

        return [
            Grid::make(3)
                ->schema([
                    TextEntry::make('personality_type')
                        ->label('Personality Type')
                        ->state($this->formatPersonalityType($personalityData['personality_type']))
                        ->badge()
                        ->color($this->getPersonalityColor($personalityData['personality_type'])),
                    TextEntry::make('confidence')
                        ->label('Confidence')
                        ->state(number_format(($personalityData['confidence'] ?? 0) * 100, 1) . '%')
                        ->icon('heroicon-o-chart-bar'),
                    TextEntry::make('interaction_count')
                        ->label('Data Points')
                        ->state($personalityData['data_points'] ?? 'N/A')
                        ->icon('heroicon-o-cursor-arrow-rays'),
                ]),

            Section::make('Personality Dimensions')
                ->schema([
                    Grid::make(5)
                        ->schema([
                            $this->makeDimensionEntry('Price Sensitivity', $dimensions['price_sensitivity'] ?? null, 'heroicon-o-currency-dollar'),
                            $this->makeDimensionEntry('Exploration', $dimensions['exploration_tendency'] ?? null, 'heroicon-o-magnifying-glass'),
                            $this->makeDimensionEntry('Sentiment', $dimensions['sentiment_tendency'] ?? null, 'heroicon-o-face-smile'),
                            $this->makeDimensionEntry('Purchase Frequency', $dimensions['purchase_frequency'] ?? null, 'heroicon-o-shopping-bag'),
                            $this->makeDimensionEntry('Decision Speed', $dimensions['decision_speed'] ?? null, 'heroicon-o-bolt'),
                        ]),
                ])
                ->compact()
                ->collapsible(),
        ];
    }

    protected function makeDimensionEntry(string $label, ?float $value, string $icon): TextEntry
    {
        $displayValue = $value !== null ? number_format($value, 2) : 'N/A';
        $color = $this->getDimensionColor($value);

        return TextEntry::make(strtolower(str_replace(' ', '_', $label)))
            ->label($label)
            ->state($displayValue)
            ->icon($icon)
            ->color($color);
    }

    protected function getDimensionColor(?float $value): string
    {
        if ($value === null) {
            return 'gray';
        }

        if ($value >= 0.7) {
            return 'success';
        }
        if ($value >= 0.4) {
            return 'warning';
        }

        return 'danger';
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

        // Get interaction counts by type
        $viewCount = $this->record->interactions()->where('interaction_type', 'view')->count();
        $clickCount = $this->record->interactions()->where('interaction_type', 'click')->count();
        $cartCount = $this->record->interactions()->where('interaction_type', 'add_to_cart')->count();
        $purchaseCount = $this->record->interactions()->where('interaction_type', 'purchase')->count();
        $wishlistCount = $this->record->interactions()->where('interaction_type', 'wishlist')->count();

        // Get top categories from interactions
        $topCategories = $this->record->interactions()
            ->join('products', 'user_interactions.product_id', '=', 'products.id')
            ->join('categories', 'products.category_id', '=', 'categories.id')
            ->selectRaw('categories.name, count(*) as count')
            ->groupBy('categories.name')
            ->orderByDesc('count')
            ->limit(3)
            ->pluck('count', 'name')
            ->toArray();

        // Get recent interactions
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

        // Add top categories
        if (! empty($topCategories)) {
            $categoryText = collect($topCategories)
                ->map(fn ($count, $name) => "{$name} ({$count})")
                ->implode(', ');

            $schema[] = TextEntry::make('top_categories')
                ->label('Top Categories')
                ->state($categoryText)
                ->icon('heroicon-o-folder');
        }

        // Add recent activity section
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
