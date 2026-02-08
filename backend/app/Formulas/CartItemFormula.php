<?php

namespace App\Formulas;

class CartItemFormula extends Formula
{
    const Basic = ['id', 'quantity', 'added_at'];

    const WithProduct = ['id', 'quantity', 'product', 'added_at'];
}
