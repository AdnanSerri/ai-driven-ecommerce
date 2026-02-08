<?php

namespace App\Http\Controllers\Api;

use App\Formulas\OrderFormula;
use App\Formulas\OrderItemFormula;
use App\Http\Controllers\Controller;
use App\Http\Requests\CheckoutRequest;
use App\Models\Order;
use App\Models\OrderItem;
use App\Services\CheckoutService;
use Illuminate\Http\JsonResponse;
use Serri\Alchemist\Facades\Alchemist;

class CheckoutController extends Controller
{
    public function __construct(
        protected CheckoutService $checkoutService
    ) {}

    public function store(CheckoutRequest $request): JsonResponse
    {
        try {
            $order = $this->checkoutService->checkout(
                $request->user(),
                $request->shipping_address_id,
                $request->billing_address_id,
                $request->notes
            );

            $order->load(['items', 'shippingAddress', 'billingAddress']);

            Order::setFormula(OrderFormula::Detail);
            OrderItem::setFormula(OrderItemFormula::Basic);

            return response()->json([
                'message' => 'Order placed successfully',
                'data' => Alchemist::brew($order),
            ], 201);
        } catch (\Exception $e) {
            return response()->json([
                'message' => $e->getMessage(),
            ], 422);
        }
    }
}
