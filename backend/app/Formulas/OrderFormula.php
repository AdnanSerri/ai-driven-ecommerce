<?php

namespace App\Formulas;

class OrderFormula extends Formula
{
    const Basic = ['id', 'order_number', 'status', 'total', 'ordered_at'];

    const List = ['id', 'order_number', 'status', 'subtotal', 'discount', 'tax', 'total', 'ordered_at'];

    const Detail = ['id', 'order_number', 'status', 'subtotal', 'discount', 'tax', 'total', 'notes', 'items', 'shippingAddress', 'billingAddress', 'ordered_at', 'confirmed_at', 'shipped_at', 'delivered_at', 'cancelled_at'];

    const WithItems = ['id', 'order_number', 'status', 'total', 'items', 'ordered_at'];

    const WithUser = ['id', 'order_number', 'status', 'total', 'user', 'ordered_at'];
}
