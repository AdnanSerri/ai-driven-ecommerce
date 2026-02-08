<?php

namespace App\Http\Controllers\Api;

use App\Formulas\CategoryFormula;
use App\Http\Controllers\Controller;
use App\Models\Category;
use Illuminate\Http\JsonResponse;
use Serri\Alchemist\Facades\Alchemist;

class CategoryController extends Controller
{
    public function index(): JsonResponse
    {
        $categories = Category::with('children')->whereNull('parent_id')->get();

        Category::setFormula(CategoryFormula::WithChildren);

        return response()->json([
            'data' => Alchemist::brew($categories),
        ]);
    }
}
