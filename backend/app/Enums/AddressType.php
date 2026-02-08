<?php

namespace App\Enums;

enum AddressType: string
{
    case Shipping = 'shipping';
    case Billing = 'billing';

    public function label(): string
    {
        return match ($this) {
            self::Shipping => 'Shipping',
            self::Billing => 'Billing',
        };
    }
}
