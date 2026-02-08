<?php

namespace App\Filament\Resources\Products\Tables;

use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\ViewAction;
use Filament\Tables\Columns\IconColumn;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Filters\TernaryFilter;
use Filament\Tables\Table;

class ProductsTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('id')
                    ->sortable(),
                TextColumn::make('name')
                    ->searchable()
                    ->sortable(),
                TextColumn::make('category.name')
                    ->label('Category')
                    ->searchable()
                    ->sortable(),
                TextColumn::make('price')
                    ->money('USD')
                    ->sortable(),
                TextColumn::make('stock')
                    ->label('Stock')
                    ->sortable()
                    ->badge()
                    ->color(fn ($record): string => match (true) {
                        ! $record->track_stock => 'gray',
                        $record->stock <= 0 => 'danger',
                        $record->stock <= $record->low_stock_threshold => 'warning',
                        default => 'success',
                    }),
                IconColumn::make('track_stock')
                    ->label('Tracked')
                    ->boolean()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('order_items_sum_quantity')
                    ->label('Total Sold')
                    ->sum('orderItems', 'quantity')
                    ->sortable(),
                TextColumn::make('reviews_count')
                    ->label('Reviews')
                    ->counts('reviews')
                    ->sortable(),
                TextColumn::make('reviews_avg_rating')
                    ->label('Avg Rating')
                    ->avg('reviews', 'rating')
                    ->formatStateUsing(fn ($state) => $state ? number_format($state, 1) . '/5' : 'N/A')
                    ->sortable()
                    ->toggleable(),
                TextColumn::make('sentiment')
                    ->label('Sentiment')
                    ->state(function ($record) {
                        $reviews = $record->reviews()->whereNotNull('sentiment_label')->get();
                        if ($reviews->isEmpty()) {
                            return null;
                        }
                        $positive = $reviews->where('sentiment_label', 'positive')->count();
                        $total = $reviews->count();

                        return round(($positive / $total) * 100);
                    })
                    ->formatStateUsing(fn ($state) => $state !== null ? $state . '% positive' : 'N/A')
                    ->badge()
                    ->color(fn ($state) => match (true) {
                        $state === null => 'gray',
                        $state >= 70 => 'success',
                        $state >= 40 => 'warning',
                        default => 'danger',
                    })
                    ->toggleable(),
                TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                SelectFilter::make('category_id')
                    ->label('Category')
                    ->relationship('category', 'name')
                    ->searchable()
                    ->preload(),
                TernaryFilter::make('track_stock')
                    ->label('Track Stock'),
                TernaryFilter::make('in_stock')
                    ->label('In Stock')
                    ->queries(
                        true: fn ($query) => $query->where(fn ($q) => $q->where('track_stock', false)->orWhere('stock', '>', 0)),
                        false: fn ($query) => $query->where('track_stock', true)->where('stock', '<=', 0),
                    ),
            ])
            ->recordActions([
                ViewAction::make(),
                EditAction::make(),
            ])
            ->toolbarActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ]);
    }
}
