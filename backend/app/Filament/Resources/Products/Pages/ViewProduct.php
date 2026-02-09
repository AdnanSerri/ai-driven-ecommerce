<?php

namespace App\Filament\Resources\Products\Pages;

use App\Filament\Resources\Products\ProductResource;
use App\Models\Product;
use App\Services\MLServiceClient;
use Filament\Actions\EditAction;
use Filament\Infolists\Components\TextEntry;
use Filament\Resources\Pages\ViewRecord;
use Filament\Schemas\Components\Grid;
use Filament\Schemas\Components\Tabs;
use Filament\Schemas\Schema;
use Filament\Support\Enums\FontWeight;

class ViewProduct extends ViewRecord
{
    protected static string $resource = ProductResource::class;

    protected function getHeaderActions(): array
    {
        return [
            EditAction::make(),
        ];
    }

    public function infolist(Schema $schema): Schema
    {
        $sentimentData = $this->getSentimentData();
        $similarProducts = $this->getSimilarProducts();
        $boughtTogether = $this->getFrequentlyBoughtTogether();

        return $schema
            ->components([
                Tabs::make('Product')
                    ->tabs([
                        Tabs\Tab::make('Product Information')
                            ->icon('heroicon-o-information-circle')
                            ->schema([
                                Grid::make(3)
                                    ->schema([
                                        TextEntry::make('name')
                                            ->label('Product Name')
                                            ->weight(FontWeight::Bold),
                                        TextEntry::make('category.name')
                                            ->label('Category')
                                            ->badge(),
                                        TextEntry::make('price')
                                            ->label('Price')
                                            ->money('USD'),
                                    ]),
                                Grid::make(3)
                                    ->schema([
                                        TextEntry::make('stock')
                                            ->label('Stock')
                                            ->badge()
                                            ->color(fn ($record) => match (true) {
                                                ! $record->track_stock => 'gray',
                                                $record->stock <= 0 => 'danger',
                                                $record->stock <= $record->low_stock_threshold => 'warning',
                                                default => 'success',
                                            }),
                                        TextEntry::make('track_stock')
                                            ->label('Track Stock')
                                            ->formatStateUsing(fn ($state) => $state ? 'Yes' : 'No'),
                                        TextEntry::make('low_stock_threshold')
                                            ->label('Low Stock Threshold'),
                                    ]),
                                TextEntry::make('description')
                                    ->label('Description')
                                    ->columnSpanFull(),
                            ]),

                        Tabs\Tab::make('Performance Metrics')
                            ->icon('heroicon-o-chart-bar')
                            ->schema([
                                Grid::make(4)
                                    ->schema([
                                        TextEntry::make('total_sold')
                                            ->label('Total Sold')
                                            ->state(fn ($record) => $record->orderItems()->sum('quantity'))
                                            ->icon('heroicon-o-shopping-cart'),
                                        TextEntry::make('reviews_count')
                                            ->label('Total Reviews')
                                            ->state(fn ($record) => $record->reviews()->count())
                                            ->icon('heroicon-o-star'),
                                        TextEntry::make('avg_rating')
                                            ->label('Average Rating')
                                            ->state(fn ($record) => number_format($record->reviews()->avg('rating') ?? 0, 1).'/5')
                                            ->icon('heroicon-o-star'),
                                        TextEntry::make('wishlist_count')
                                            ->label('Wishlisted')
                                            ->state(fn ($record) => $record->wishlists()->count())
                                            ->icon('heroicon-o-heart'),
                                    ]),
                            ]),

                        Tabs\Tab::make('Sentiment Analysis')
                            ->icon('heroicon-o-face-smile')
                            ->schema($this->getSentimentSchema($sentimentData)),

                        Tabs\Tab::make('Similar Products')
                            ->icon('heroicon-o-sparkles')
                            ->schema($this->getSimilarProductsSchema($similarProducts)),

                        Tabs\Tab::make('Frequently Bought Together')
                            ->icon('heroicon-o-shopping-bag')
                            ->schema($this->getBoughtTogetherSchema($boughtTogether)),
                    ])
                    ->persistTabInQueryString()
                    ->columnSpanFull(),
            ]);
    }

    protected function getSentimentData(): array
    {
        $reviews = $this->record->reviews()->whereNotNull('sentiment_label')->get();

        if ($reviews->isEmpty()) {
            return [
                'has_data' => false,
            ];
        }

        $positive = $reviews->where('sentiment_label', 'positive')->count();
        $neutral = $reviews->where('sentiment_label', 'neutral')->count();
        $negative = $reviews->where('sentiment_label', 'negative')->count();
        $total = $reviews->count();

        $avgScore = $reviews->avg('sentiment_score');
        $avgConfidence = $reviews->avg('sentiment_confidence');

        return [
            'has_data' => true,
            'positive' => $positive,
            'neutral' => $neutral,
            'negative' => $negative,
            'total' => $total,
            'positive_percent' => round(($positive / $total) * 100, 1),
            'neutral_percent' => round(($neutral / $total) * 100, 1),
            'negative_percent' => round(($negative / $total) * 100, 1),
            'avg_score' => $avgScore,
            'avg_confidence' => $avgConfidence,
        ];
    }

    protected function getSentimentSchema(array $data): array
    {
        if (! $data['has_data']) {
            return [
                TextEntry::make('no_sentiment')
                    ->label('')
                    ->state('No sentiment data available. Reviews need to be analyzed first.')
                    ->icon('heroicon-o-information-circle')
                    ->color('gray'),
            ];
        }

        return [
            Grid::make(4)
                ->schema([
                    TextEntry::make('positive_reviews')
                        ->label('Positive')
                        ->state($data['positive'].' ('.$data['positive_percent'].'%)')
                        ->icon('heroicon-o-face-smile')
                        ->color('success'),
                    TextEntry::make('neutral_reviews')
                        ->label('Neutral')
                        ->state($data['neutral'].' ('.$data['neutral_percent'].'%)')
                        ->icon('heroicon-o-minus-circle')
                        ->color('gray'),
                    TextEntry::make('negative_reviews')
                        ->label('Negative')
                        ->state($data['negative'].' ('.$data['negative_percent'].'%)')
                        ->icon('heroicon-o-face-frown')
                        ->color('danger'),
                    TextEntry::make('avg_confidence')
                        ->label('Avg Confidence')
                        ->state(number_format($data['avg_confidence'] * 100, 1).'%')
                        ->icon('heroicon-o-chart-bar')
                        ->color('info'),
                ]),
            TextEntry::make('overall_sentiment')
                ->label('Overall Sentiment')
                ->state(function () use ($data) {
                    if ($data['positive_percent'] >= 70) {
                        return 'Very Positive';
                    }
                    if ($data['positive_percent'] >= 50) {
                        return 'Mostly Positive';
                    }
                    if ($data['negative_percent'] >= 50) {
                        return 'Mostly Negative';
                    }

                    return 'Mixed';
                })
                ->badge()
                ->color(function () use ($data) {
                    if ($data['positive_percent'] >= 70) {
                        return 'success';
                    }
                    if ($data['positive_percent'] >= 50) {
                        return 'success';
                    }
                    if ($data['negative_percent'] >= 50) {
                        return 'danger';
                    }

                    return 'warning';
                }),
        ];
    }

    protected function getSimilarProducts(): array
    {
        try {
            $mlClient = app(MLServiceClient::class);
            $similar = $mlClient->getSimilarProducts($this->record->id, 5);

            if (! $similar || ! isset($similar['similar_products'])) {
                return [];
            }

            // Fetch product details
            $productIds = collect($similar['similar_products'])->pluck('product_id')->toArray();
            $products = Product::whereIn('id', $productIds)->get()->keyBy('id');

            return collect($similar['similar_products'])->map(function ($item) use ($products) {
                $product = $products[$item['product_id']] ?? null;

                return [
                    'id' => $item['product_id'],
                    'name' => $product?->name ?? 'Unknown Product',
                    'category' => $product?->category?->name ?? 'N/A',
                    'price' => $product?->price ?? 0,
                    'score' => $item['score'] ?? 0,
                ];
            })->toArray();
        } catch (\Exception $e) {
            return [];
        }
    }

    protected function getSimilarProductsSchema(array $products): array
    {
        if (empty($products)) {
            return [
                TextEntry::make('no_similar')
                    ->label('')
                    ->state('No similar products found. The ML service may need to index this product first.')
                    ->icon('heroicon-o-information-circle')
                    ->color('gray'),
            ];
        }

        $entries = [];
        foreach ($products as $index => $product) {
            $entries[] = Grid::make(4)
                ->schema([
                    TextEntry::make("similar_{$index}_name")
                        ->label('Product')
                        ->state($product['name'])
                        ->url(fn () => ProductResource::getUrl('view', ['record' => $product['id']]))
                        ->weight(FontWeight::Bold),
                    TextEntry::make("similar_{$index}_category")
                        ->label('Category')
                        ->state($product['category'])
                        ->badge(),
                    TextEntry::make("similar_{$index}_price")
                        ->label('Price')
                        ->state('$'.number_format($product['price'], 2)),
                    TextEntry::make("similar_{$index}_score")
                        ->label('Similarity')
                        ->state(number_format($product['score'] * 100, 1).'%')
                        ->badge()
                        ->color(fn () => $product['score'] >= 0.8 ? 'success' : ($product['score'] >= 0.5 ? 'warning' : 'gray')),
                ]);
        }

        return $entries;
    }

    protected function getFrequentlyBoughtTogether(): array
    {
        try {
            $mlClient = app(MLServiceClient::class);
            $response = $mlClient->getFrequentlyBoughtTogether($this->record->id, 5);

            if (! $response || ! isset($response['products'])) {
                return [];
            }

            // Fetch product details
            $productIds = collect($response['products'])->pluck('product_id')->toArray();
            $products = Product::whereIn('id', $productIds)->get()->keyBy('id');

            return collect($response['products'])->map(function ($item) use ($products) {
                $product = $products[$item['product_id']] ?? null;

                return [
                    'id' => $item['product_id'],
                    'name' => $product?->name ?? 'Unknown Product',
                    'category' => $product?->category?->name ?? 'N/A',
                    'price' => $product?->price ?? 0,
                    'co_purchase_count' => $item['co_purchase_count'] ?? 0,
                    'confidence' => $item['confidence'] ?? 0,
                ];
            })->toArray();
        } catch (\Exception $e) {
            return [];
        }
    }

    protected function getBoughtTogetherSchema(array $products): array
    {
        if (empty($products)) {
            return [
                TextEntry::make('no_bought_together')
                    ->label('')
                    ->state('No frequently bought together data available. More purchase history needed.')
                    ->icon('heroicon-o-information-circle')
                    ->color('gray'),
            ];
        }

        $entries = [];
        foreach ($products as $index => $product) {
            $entries[] = Grid::make(4)
                ->schema([
                    TextEntry::make("bought_{$index}_name")
                        ->label('Product')
                        ->state($product['name'])
                        ->url(fn () => ProductResource::getUrl('view', ['record' => $product['id']]))
                        ->weight(FontWeight::Bold),
                    TextEntry::make("bought_{$index}_category")
                        ->label('Category')
                        ->state($product['category'])
                        ->badge(),
                    TextEntry::make("bought_{$index}_price")
                        ->label('Price')
                        ->state('$'.number_format($product['price'], 2)),
                    TextEntry::make("bought_{$index}_count")
                        ->label('Co-purchases')
                        ->state($product['co_purchase_count'].' times')
                        ->icon('heroicon-o-shopping-cart')
                        ->color('success'),
                ]);
        }

        return $entries;
    }
}
