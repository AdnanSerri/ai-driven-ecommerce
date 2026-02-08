<?php

namespace App\Formulas;

class CartFormula extends Formula
{
    const Basic = ['id', 'created_at', 'updated_at'];

    const WithItems = ['id', 'items', 'created_at', 'updated_at'];
}
