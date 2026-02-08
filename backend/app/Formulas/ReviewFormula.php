<?php

namespace App\Formulas;

class ReviewFormula extends Formula
{
    const Basic = ['id', 'rating', 'comment', 'created_at'];

    const WithProduct = ['id', 'rating', 'comment', 'created_at', 'product'];

    const WithUser = ['id', 'rating', 'comment', 'created_at', 'user'];

    const Full = ['id', 'rating', 'comment', 'created_at', 'product', 'user'];
}