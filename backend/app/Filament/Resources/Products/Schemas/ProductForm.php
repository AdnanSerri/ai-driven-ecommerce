<?php

namespace App\Filament\Resources\Products\Schemas;

use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;

class ProductForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Section::make('Product Information')
                    ->schema([
                        TextInput::make('name')
                            ->required()
                            ->maxLength(255),
                        Select::make('category_id')
                            ->label('Category')
                            ->relationship('category', 'name')
                            ->searchable()
                            ->preload()
                            ->required(),
                        TextInput::make('price')
                            ->required()
                            ->numeric()
                            ->prefix('$')
                            ->minValue(0),
                        Textarea::make('description')
                            ->required()
                            ->rows(4)
                            ->columnSpanFull(),
                        TextInput::make('image_url')
                            ->label('Image URL')
                            ->url()
                            ->maxLength(255)
                            ->columnSpanFull(),
                    ])
                    ->columns(2),
                Section::make('Inventory')
                    ->schema([
                        Toggle::make('track_stock')
                            ->label('Track Stock')
                            ->helperText('Enable to track inventory levels')
                            ->default(true)
                            ->live(),
                        TextInput::make('stock')
                            ->label('Stock Quantity')
                            ->numeric()
                            ->minValue(0)
                            ->default(0)
                            ->visible(fn ($get) => $get('track_stock')),
                        TextInput::make('low_stock_threshold')
                            ->label('Low Stock Threshold')
                            ->numeric()
                            ->minValue(0)
                            ->default(10)
                            ->helperText('Alert when stock falls below this level')
                            ->visible(fn ($get) => $get('track_stock')),
                    ])
                    ->columns(3),
            ]);
    }
}
