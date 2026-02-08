<?php

namespace App\Http\Controllers\Api;

use App\Formulas\CartFormula;
use App\Formulas\CartItemFormula;
use App\Formulas\ProductFormula;
use App\Http\Controllers\Controller;
use App\Http\Requests\Cart\AddCartItemRequest;
use App\Http\Requests\Cart\UpdateCartItemRequest;
use App\Jobs\PublishKafkaEventJob;
use App\Models\Cart;
use App\Models\CartItem;
use App\Models\Product;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Serri\Alchemist\Facades\Alchemist;

class CartController extends Controller
{
    public function show(Request $request): JsonResponse
    {
        $cart = $request->user()->getOrCreateCart();
        $cart->load('items.product');

        Cart::setFormula(CartFormula::WithItems);
        CartItem::setFormula(CartItemFormula::WithProduct);
        Product::setFormula(ProductFormula::WithStock);

        return response()->json([
            'data' => Alchemist::brew($cart),
            'total' => $cart->total,
            'item_count' => $cart->item_count,
        ]);
    }

    public function addItem(AddCartItemRequest $request): JsonResponse
    {
        $cart = $request->user()->getOrCreateCart();
        $product = Product::findOrFail($request->product_id);

        if ($product->track_stock && $product->stock < $request->quantity) {
            return response()->json([
                'message' => 'Insufficient stock available',
                'available_stock' => $product->stock,
            ], 422);
        }

        $existingItem = $cart->items()->where('product_id', $product->id)->first();

        if ($existingItem) {
            $newQuantity = $existingItem->quantity + $request->quantity;

            if ($product->track_stock && $product->stock < $newQuantity) {
                return response()->json([
                    'message' => 'Insufficient stock for requested quantity',
                    'available_stock' => $product->stock,
                    'current_in_cart' => $existingItem->quantity,
                ], 422);
            }

            $existingItem->update(['quantity' => $newQuantity]);
            $cartItem = $existingItem;
        } else {
            $cartItem = $cart->items()->create([
                'product_id' => $product->id,
                'quantity' => $request->quantity,
                'added_at' => now(),
            ]);
        }

        $cartItem->load('product');
        $cart->load('items.product');

        $this->dispatchCartUpdatedEvent($request->user()->id, 'item_added', $product->id, $cart);

        CartItem::setFormula(CartItemFormula::WithProduct);
        Product::setFormula(ProductFormula::WithStock);

        return response()->json([
            'message' => 'Item added to cart',
            'data' => Alchemist::brew($cartItem),
            'cart_total' => $cart->total,
            'cart_item_count' => $cart->item_count,
        ], 201);
    }

    public function updateItem(UpdateCartItemRequest $request, CartItem $cartItem): JsonResponse
    {
        $cart = $request->user()->getOrCreateCart();

        if ($cartItem->cart_id !== $cart->id) {
            return response()->json([
                'message' => 'Cart item not found',
            ], 404);
        }

        $product = $cartItem->product;

        if ($product->track_stock && $product->stock < $request->quantity) {
            return response()->json([
                'message' => 'Insufficient stock available',
                'available_stock' => $product->stock,
            ], 422);
        }

        $cartItem->update(['quantity' => $request->quantity]);
        $cartItem->load('product');
        $cart->load('items.product');

        $this->dispatchCartUpdatedEvent($request->user()->id, 'item_updated', $product->id, $cart);

        CartItem::setFormula(CartItemFormula::WithProduct);
        Product::setFormula(ProductFormula::WithStock);

        return response()->json([
            'message' => 'Cart item updated',
            'data' => Alchemist::brew($cartItem),
            'cart_total' => $cart->total,
            'cart_item_count' => $cart->item_count,
        ]);
    }

    public function removeItem(Request $request, CartItem $cartItem): JsonResponse
    {
        $cart = $request->user()->getOrCreateCart();

        if ($cartItem->cart_id !== $cart->id) {
            return response()->json([
                'message' => 'Cart item not found',
            ], 404);
        }

        $productId = $cartItem->product_id;
        $cartItem->delete();
        $cart->load('items.product');

        $this->dispatchCartUpdatedEvent($request->user()->id, 'item_removed', $productId, $cart);

        return response()->json([
            'message' => 'Item removed from cart',
            'cart_total' => $cart->total,
            'cart_item_count' => $cart->item_count,
        ]);
    }

    public function clear(Request $request): JsonResponse
    {
        $cart = $request->user()->getOrCreateCart();
        $cart->items()->delete();

        $this->dispatchCartUpdatedEvent($request->user()->id, 'cart_cleared', null, $cart);

        return response()->json([
            'message' => 'Cart cleared',
        ]);
    }

    /**
     * Dispatch the cart.updated Kafka event.
     */
    protected function dispatchCartUpdatedEvent(int $userId, string $action, ?int $affectedProductId, Cart $cart): void
    {
        $items = $cart->items->map(fn ($item) => [
            'product_id' => $item->product_id,
            'quantity' => $item->quantity,
        ])->toArray();

        PublishKafkaEventJob::dispatch('cart.updated', [
            'event_type' => 'cart.updated',
            'user_id' => $userId,
            'action' => $action,
            'affected_product_id' => $affectedProductId,
            'items' => $items,
            'timestamp' => now()->toIso8601String(),
        ]);
    }
}
