<?php

namespace App\Formulas;

class CategoryFormula extends Formula
{
    const Basic = ['id', 'name'];

    const WithParent = ['id', 'name', 'parent'];

    const WithChildren = ['id', 'name', 'children'];
}