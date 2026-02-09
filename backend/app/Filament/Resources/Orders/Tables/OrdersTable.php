<?php

namespace App\Filament\Resources\Orders\Tables;

use App\Enums\OrderStatus;
use App\Models\Order;
use Filament\Actions\Action;
use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\ViewAction;
use Filament\Forms\Components\Select;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;

class OrdersTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('order_number')
                    ->searchable()
                    ->sortable(),
                TextColumn::make('user.name')
                    ->label('Customer')
                    ->searchable()
                    ->sortable(),
                TextColumn::make('status')
                    ->badge()
                    ->color(fn (OrderStatus $state): string => $state->color())
                    ->formatStateUsing(fn (OrderStatus $state): string => $state->label())
                    ->sortable(),
                TextColumn::make('items_count')
                    ->label('Items')
                    ->counts('items')
                    ->sortable(),
                TextColumn::make('subtotal')
                    ->money('USD')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('discount')
                    ->money('USD')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('tax')
                    ->money('USD')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('total')
                    ->money('USD')
                    ->sortable(),
                TextColumn::make('ordered_at')
                    ->dateTime()
                    ->sortable(),
            ])
            ->defaultSort('ordered_at', 'desc')
            ->filters([
                SelectFilter::make('status')
                    ->options(collect(OrderStatus::cases())->mapWithKeys(fn ($status) => [
                        $status->value => $status->label(),
                    ])),
                SelectFilter::make('user_id')
                    ->label('Customer')
                    ->relationship('user', 'name')
                    ->searchable()
                    ->preload(),
            ])
            ->recordActions([
                Action::make('change_status')
                    ->label('Change Status')
                    ->icon('heroicon-o-arrow-path')
                    ->color('warning')
                    ->form([
                        Select::make('status')
                            ->options(collect(OrderStatus::cases())->mapWithKeys(fn ($status) => [
                                $status->value => $status->label(),
                            ]))
                            ->default(fn (Order $record): string => $record->status->value)
                            ->required(),
                    ])
                    ->action(function (Order $record, array $data): void {
                        $newStatus = OrderStatus::from($data['status']);
                        $updates = ['status' => $newStatus];

                        $timestampField = match ($newStatus) {
                            OrderStatus::Confirmed => 'confirmed_at',
                            OrderStatus::Shipped => 'shipped_at',
                            OrderStatus::Delivered => 'delivered_at',
                            OrderStatus::Cancelled => 'cancelled_at',
                            default => null,
                        };

                        if ($timestampField && ! $record->{$timestampField}) {
                            $updates[$timestampField] = now();
                        }

                        $record->update($updates);
                    }),
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
