<?php

namespace App\Formulas;

class ProductImageFormula extends Formula
{
    const Basic = ['id', 'url', 'is_primary'];

    const Detail = ['id', 'url', 'alt_text', 'is_primary', 'sort_order', 'created_at'];
}
