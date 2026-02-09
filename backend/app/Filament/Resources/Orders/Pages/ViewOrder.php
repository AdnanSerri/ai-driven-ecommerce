<?php

namespace App\Filament\Resources\Orders\Pages;

use App\Enums\OrderStatus;
use App\Filament\Resources\Orders\OrderResource;
use Filament\Actions\Action;
use Filament\Actions\EditAction;
use Filament\Forms\Components\Select;
use Filament\Resources\Pages\ViewRecord;

class ViewOrder extends ViewRecord
{
    protected static string $resource = OrderResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Action::make('change_status')
                ->label('Change Status')
                ->icon('heroicon-o-arrow-path')
                ->color('warning')
                ->form([
                    Select::make('status')
                        ->options(collect(OrderStatus::cases())->mapWithKeys(fn ($status) => [
                            $status->value => $status->label(),
                        ]))
                        ->default(fn () => $this->record->status->value)
                        ->required(),
                ])
                ->action(function (array $data): void {
                    $newStatus = OrderStatus::from($data['status']);
                    $updates = ['status' => $newStatus];

                    $timestampField = match ($newStatus) {
                        OrderStatus::Confirmed => 'confirmed_at',
                        OrderStatus::Shipped => 'shipped_at',
                        OrderStatus::Delivered => 'delivered_at',
                        OrderStatus::Cancelled => 'cancelled_at',
                        default => null,
                    };

                    if ($timestampField && ! $this->record->{$timestampField}) {
                        $updates[$timestampField] = now();
                    }

                    $this->record->update($updates);
                    $this->refreshFormData(['status', 'confirmed_at', 'shipped_at', 'delivered_at', 'cancelled_at']);
                }),
            EditAction::make(),
        ];
    }
}
