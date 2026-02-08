<?php

namespace App\Formulas;

class WishlistFormula extends Formula
{
    const Basic = ['id', 'added_at'];

    const WithProduct = ['id', 'product', 'added_at'];
}
