<?php

namespace App\Filament\Resources\Reviews\Tables;

use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;

class ReviewsTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('id')
                    ->sortable(),
                TextColumn::make('user.name')
                    ->label('Reviewer')
                    ->searchable()
                    ->sortable(),
                TextColumn::make('product.name')
                    ->label('Product')
                    ->searchable()
                    ->sortable(),
                TextColumn::make('rating')
                    ->badge()
                    ->color(fn (int $state): string => match (true) {
                        $state >= 4 => 'success',
                        $state >= 3 => 'warning',
                        default => 'danger',
                    })
                    ->sortable(),
                TextColumn::make('comment')
                    ->limit(50)
                    ->searchable()
                    ->toggleable(),
                TextColumn::make('sentiment_label')
                    ->label('Sentiment')
                    ->badge()
                    ->color(fn (?string $state): string => match ($state) {
                        'positive' => 'success',
                        'negative' => 'danger',
                        'neutral' => 'gray',
                        default => 'gray',
                    })
                    ->sortable(),
                TextColumn::make('sentiment_score')
                    ->label('Score')
                    ->formatStateUsing(fn (?float $state): string => $state !== null ? number_format($state, 2) : '-')
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('sentiment_confidence')
                    ->label('Confidence')
                    ->formatStateUsing(fn (?float $state): string => $state !== null ? number_format($state * 100, 1) . '%' : '-')
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable(),
            ])
            ->defaultSort('created_at', 'desc')
            ->filters([
                SelectFilter::make('rating')
                    ->options([
                        1 => '1 - Poor',
                        2 => '2 - Fair',
                        3 => '3 - Good',
                        4 => '4 - Very Good',
                        5 => '5 - Excellent',
                    ]),
                SelectFilter::make('sentiment_label')
                    ->label('Sentiment')
                    ->options([
                        'positive' => 'Positive',
                        'neutral' => 'Neutral',
                        'negative' => 'Negative',
                    ]),
                SelectFilter::make('product_id')
                    ->label('Product')
                    ->relationship('product', 'name')
                    ->searchable()
                    ->preload(),
                SelectFilter::make('user_id')
                    ->label('Reviewer')
                    ->relationship('user', 'name')
                    ->searchable()
                    ->preload(),
            ])
            ->recordActions([
                EditAction::make(),
            ])
            ->toolbarActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ]);
    }
}
