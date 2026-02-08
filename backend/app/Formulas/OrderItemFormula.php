<?php

namespace App\Formulas;

class OrderItemFormula extends Formula
{
    const Basic = ['id', 'product_name', 'product_price', 'quantity', 'subtotal'];

    const WithProduct = ['id', 'product_name', 'product_price', 'quantity', 'subtotal', 'product'];
}
