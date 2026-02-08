<?php

namespace App\Http\Controllers\Api;

use App\Formulas\ProductFormula;
use App\Formulas\WishlistFormula;
use App\Http\Controllers\Controller;
use App\Http\Requests\Wishlist\AddToWishlistRequest;
use App\Models\Product;
use App\Models\Wishlist;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Serri\Alchemist\Facades\Alchemist;

class WishlistController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $wishlists = $request->user()
            ->wishlists()
            ->with('product.category')
            ->latest('added_at')
            ->paginate(15);

        Wishlist::setFormula(WishlistFormula::WithProduct);
        Product::setFormula(ProductFormula::List);

        return response()->json(
            Alchemist::brewBatch($wishlists)
        );
    }

    public function store(AddToWishlistRequest $request): JsonResponse
    {
        $existing = $request->user()
            ->wishlists()
            ->where('product_id', $request->product_id)
            ->first();

        if ($existing) {
            return response()->json([
                'message' => 'Product already in wishlist',
            ], 409);
        }

        $wishlist = $request->user()->wishlists()->create([
            'product_id' => $request->product_id,
            'added_at' => now(),
        ]);

        $wishlist->load('product');

        Wishlist::setFormula(WishlistFormula::WithProduct);
        Product::setFormula(ProductFormula::Basic);

        return response()->json([
            'message' => 'Product added to wishlist',
            'data' => Alchemist::brew($wishlist),
        ], 201);
    }

    public function destroy(Request $request, Product $product): JsonResponse
    {
        $deleted = $request->user()
            ->wishlists()
            ->where('product_id', $product->id)
            ->delete();

        if (! $deleted) {
            return response()->json([
                'message' => 'Product not found in wishlist',
            ], 404);
        }

        return response()->json([
            'message' => 'Product removed from wishlist',
        ]);
    }
}
