<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class CheckoutRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'shipping_address_id' => ['nullable', 'integer', 'exists:addresses,id'],
            'billing_address_id' => ['nullable', 'integer', 'exists:addresses,id'],
            'notes' => ['nullable', 'string', 'max:1000'],
        ];
    }

    public function messages(): array
    {
        return [
            'shipping_address_id.exists' => 'Shipping address not found',
            'billing_address_id.exists' => 'Billing address not found',
            'notes.max' => 'Notes cannot exceed 1000 characters',
        ];
    }
}
