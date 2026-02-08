<?php

namespace App\Filament\Resources\Orders\Schemas;

use App\Enums\OrderStatus;
use App\Models\Address;
use Filament\Forms\Components\DateTimePicker;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;

class OrderForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Section::make('Order Information')
                    ->schema([
                        TextInput::make('order_number')
                            ->required()
                            ->disabled()
                            ->maxLength(255),
                        Select::make('user_id')
                            ->label('Customer')
                            ->relationship('user', 'name')
                            ->searchable()
                            ->preload()
                            ->required(),
                        Select::make('status')
                            ->options(collect(OrderStatus::cases())->mapWithKeys(fn ($status) => [
                                $status->value => $status->label(),
                            ]))
                            ->required(),
                        Select::make('shipping_address_id')
                            ->label('Shipping Address')
                            ->relationship('shippingAddress', 'label')
                            ->getOptionLabelFromRecordUsing(fn (Address $record): string => $record->label ?? $record->formatted_address)
                            ->searchable()
                            ->preload(),
                        Select::make('billing_address_id')
                            ->label('Billing Address')
                            ->relationship('billingAddress', 'label')
                            ->getOptionLabelFromRecordUsing(fn (Address $record): string => $record->label ?? $record->formatted_address)
                            ->searchable()
                            ->preload(),
                    ])
                    ->columns(2),
                Section::make('Order Totals')
                    ->schema([
                        TextInput::make('subtotal')
                            ->required()
                            ->numeric()
                            ->prefix('$')
                            ->minValue(0),
                        TextInput::make('discount')
                            ->numeric()
                            ->prefix('$')
                            ->minValue(0)
                            ->default(0),
                        TextInput::make('tax')
                            ->numeric()
                            ->prefix('$')
                            ->minValue(0)
                            ->default(0),
                        TextInput::make('total')
                            ->required()
                            ->numeric()
                            ->prefix('$')
                            ->minValue(0),
                    ])
                    ->columns(4),
                Section::make('Timestamps')
                    ->schema([
                        DateTimePicker::make('ordered_at')
                            ->label('Ordered At')
                            ->required(),
                        DateTimePicker::make('confirmed_at')
                            ->label('Confirmed At'),
                        DateTimePicker::make('shipped_at')
                            ->label('Shipped At'),
                        DateTimePicker::make('delivered_at')
                            ->label('Delivered At'),
                        DateTimePicker::make('cancelled_at')
                            ->label('Cancelled At'),
                    ])
                    ->columns(3)
                    ->collapsed(),
                Section::make('Notes')
                    ->schema([
                        Textarea::make('notes')
                            ->rows(3)
                            ->columnSpanFull(),
                    ]),
            ]);
    }
}
