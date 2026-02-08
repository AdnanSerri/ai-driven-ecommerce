<?php

namespace App\Formulas;

class ProductFormula extends Formula
{
    const Basic = ['id', 'name', 'price', 'image_url'];

    const List = ['id', 'name', 'description', 'price', 'stock', 'image_url', 'category', 'created_at'];

    const Detail = ['id', 'name', 'description', 'price', 'stock', 'low_stock_threshold', 'track_stock', 'image_url', 'category', 'reviews', 'images', 'created_at'];

    const WithStock = ['id', 'name', 'price', 'stock', 'low_stock_threshold', 'track_stock', 'image_url'];

    const WithImages = ['id', 'name', 'description', 'price', 'stock', 'image_url', 'category', 'images', 'created_at'];
}