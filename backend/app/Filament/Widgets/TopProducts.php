<?php

namespace App\Filament\Widgets;

use App\Models\Product;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Table;
use Filament\Widgets\TableWidget;
use Illuminate\Database\Eloquent\Builder;

class TopProducts extends TableWidget
{
    protected static ?string $heading = 'Top Selling Products';

    protected int|string|array $columnSpan = 'full';

    protected static ?int $sort = 3;

    public function table(Table $table): Table
    {
        return $table
            ->query(fn (): Builder => Product::query()
                ->withSum('orderItems', 'quantity')
                ->withAvg('reviews', 'rating')
                ->orderByDesc('order_items_sum_quantity')
                ->limit(5))
            ->columns([
                TextColumn::make('name')
                    ->label('Product'),
                TextColumn::make('category.name')
                    ->label('Category'),
                TextColumn::make('price')
                    ->money('USD'),
                TextColumn::make('order_items_sum_quantity')
                    ->label('Total Sales')
                    ->default(0)
                    ->sortable(),
                TextColumn::make('reviews_avg_rating')
                    ->label('Avg Rating')
                    ->formatStateUsing(fn ($state) => $state ? number_format($state, 1) . '/5' : 'N/A'),
            ])
            ->paginated(false);
    }
}
