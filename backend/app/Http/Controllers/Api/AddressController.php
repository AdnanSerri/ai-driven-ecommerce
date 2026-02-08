<?php

namespace App\Http\Controllers\Api;

use App\Formulas\AddressFormula;
use App\Http\Controllers\Controller;
use App\Http\Requests\Address\StoreAddressRequest;
use App\Http\Requests\Address\UpdateAddressRequest;
use App\Models\Address;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Serri\Alchemist\Facades\Alchemist;

class AddressController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $addresses = $request->user()
            ->addresses()
            ->latest('created_at')
            ->get();

        Address::setFormula(AddressFormula::Detail);

        return response()->json([
            'data' => Alchemist::brew($addresses),
        ]);
    }

    public function store(StoreAddressRequest $request): JsonResponse
    {
        if ($request->is_default) {
            $request->user()
                ->addresses()
                ->where('type', $request->type)
                ->update(['is_default' => false]);
        }

        $address = $request->user()->addresses()->create([
            'label' => $request->label,
            'type' => $request->type,
            'first_name' => $request->first_name,
            'last_name' => $request->last_name,
            'phone' => $request->phone,
            'address_line_1' => $request->address_line_1,
            'address_line_2' => $request->address_line_2,
            'city' => $request->city,
            'state' => $request->state,
            'postal_code' => $request->postal_code,
            'country' => $request->country,
            'is_default' => $request->is_default ?? false,
            'created_at' => now(),
        ]);

        Address::setFormula(AddressFormula::Detail);

        return response()->json([
            'message' => 'Address created successfully',
            'data' => Alchemist::brew($address),
        ], 201);
    }

    public function show(Request $request, Address $address): JsonResponse
    {
        if ($address->user_id !== $request->user()->id) {
            return response()->json([
                'message' => 'Address not found',
            ], 404);
        }

        Address::setFormula(AddressFormula::Detail);

        return response()->json([
            'data' => Alchemist::brew($address),
        ]);
    }

    public function update(UpdateAddressRequest $request, Address $address): JsonResponse
    {
        if ($address->user_id !== $request->user()->id) {
            return response()->json([
                'message' => 'Address not found',
            ], 404);
        }

        if ($request->is_default) {
            $type = $request->type ?? $address->type;
            $request->user()
                ->addresses()
                ->where('type', $type)
                ->where('id', '!=', $address->id)
                ->update(['is_default' => false]);
        }

        $address->update($request->validated());

        Address::setFormula(AddressFormula::Detail);

        return response()->json([
            'message' => 'Address updated successfully',
            'data' => Alchemist::brew($address),
        ]);
    }

    public function destroy(Request $request, Address $address): JsonResponse
    {
        if ($address->user_id !== $request->user()->id) {
            return response()->json([
                'message' => 'Address not found',
            ], 404);
        }

        $address->delete();

        return response()->json([
            'message' => 'Address deleted successfully',
        ]);
    }

    public function setDefault(Request $request, Address $address): JsonResponse
    {
        if ($address->user_id !== $request->user()->id) {
            return response()->json([
                'message' => 'Address not found',
            ], 404);
        }

        $request->user()
            ->addresses()
            ->where('type', $address->type)
            ->update(['is_default' => false]);

        $address->update(['is_default' => true]);

        Address::setFormula(AddressFormula::Detail);

        return response()->json([
            'message' => 'Default address updated',
            'data' => Alchemist::brew($address),
        ]);
    }
}
