<?php

namespace App\Formulas;

class AddressFormula extends Formula
{
    const Basic = ['id', 'label', 'type', 'first_name', 'last_name', 'city', 'country', 'is_default'];

    const Detail = ['id', 'label', 'type', 'first_name', 'last_name', 'phone', 'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country', 'is_default', 'created_at'];
}
