<?php

namespace App\Http\Controllers\Api;

use App\Formulas\ProductFormula;
use App\Http\Controllers\Controller;
use App\Models\Product;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Serri\Alchemist\Facades\Alchemist;

class ProductController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $query = Product::query()->with(['category', 'reviews']);

        if ($request->filled('search')) {
            $search = $request->search;
            $query->whereRaw(
                'MATCH(name, description) AGAINST(? IN BOOLEAN MODE)',
                [$search . '*']
            );
        }

        if ($request->filled('category')) {
            $query->where('category_id', $request->category);
        }

        if ($request->filled('min_price')) {
            $query->where('price', '>=', $request->min_price);
        }

        if ($request->filled('max_price')) {
            $query->where('price', '<=', $request->max_price);
        }

        if ($request->filled('min_rating')) {
            $query->whereHas('reviews', function ($q) use ($request) {
                $q->havingRaw('AVG(rating) >= ?', [$request->min_rating]);
            }, '>=', 1);
        }

        if ($request->boolean('in_stock')) {
            $query->where(function ($q) {
                $q->where('track_stock', false)
                    ->orWhere('stock', '>', 0);
            });
        }

        $sortBy = $request->input('sort_by', 'created_at');
        $sortDir = $request->input('sort_dir', 'desc');

        $allowedSorts = ['name', 'price', 'created_at', 'stock'];
        if (in_array($sortBy, $allowedSorts)) {
            $query->orderBy($sortBy, $sortDir === 'asc' ? 'asc' : 'desc');
        }

        $products = $query->paginate(15);

        Product::setFormula(ProductFormula::List);

        return response()->json(
            Alchemist::brewBatch($products)
        );
    }

    public function show(Product $product): JsonResponse
    {
        $product->load(['category', 'reviews.user', 'images']);

        Product::setFormula(ProductFormula::Detail);

        return response()->json([
            'data' => Alchemist::brew($product),
        ]);
    }
}
