<?php

namespace App\Formulas;

class UserFormula extends Formula
{
    const Basic = ['id', 'name', 'email'];

    const WithReviews = ['id', 'name', 'email', 'reviews'];

    const WithOrders = ['id', 'name', 'email', 'orders'];
}