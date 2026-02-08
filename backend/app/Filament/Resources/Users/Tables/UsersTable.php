<?php

namespace App\Filament\Resources\Users\Tables;

use App\Services\MLServiceClient;
use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\ViewAction;
use Filament\Tables\Columns\IconColumn;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Table;
use Illuminate\Support\Facades\Cache;

class UsersTable
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
                TextColumn::make('email')
                    ->label('Email address')
                    ->searchable()
                    ->sortable(),
                IconColumn::make('is_admin')
                    ->label('Admin')
                    ->boolean()
                    ->sortable(),
                TextColumn::make('personality_type')
                    ->label('Personality')
                    ->state(function ($record) {
                        return self::getPersonalityType($record->id);
                    })
                    ->badge()
                    ->color(fn ($state) => self::getPersonalityColor($state))
                    ->formatStateUsing(fn ($state) => $state ? ucwords(str_replace('_', ' ', $state)) : 'Unknown')
                    ->toggleable(),
                TextColumn::make('reviews_count')
                    ->label('Reviews')
                    ->counts('reviews')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('orders_count')
                    ->label('Orders')
                    ->counts('orders')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('updated_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                //
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

    protected static function getPersonalityType(int $userId): ?string
    {
        $cacheKey = "admin.user.personality.{$userId}";

        return Cache::remember($cacheKey, 300, function () use ($userId) {
            try {
                $mlClient = app(MLServiceClient::class);
                $personality = $mlClient->getUserPersonality($userId);

                return $personality['profile']['personality_type'] ?? null;
            } catch (\Exception $e) {
                return null;
            }
        });
    }

    protected static function getPersonalityColor(?string $type): string
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
}
