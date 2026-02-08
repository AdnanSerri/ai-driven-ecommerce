<?php

namespace App\Http\Requests\Address;

use App\Enums\AddressType;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class StoreAddressRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'label' => ['nullable', 'string', 'max:100'],
            'type' => ['required', Rule::enum(AddressType::class)],
            'first_name' => ['required', 'string', 'max:100'],
            'last_name' => ['required', 'string', 'max:100'],
            'phone' => ['nullable', 'string', 'max:20'],
            'address_line_1' => ['required', 'string', 'max:255'],
            'address_line_2' => ['nullable', 'string', 'max:255'],
            'city' => ['required', 'string', 'max:100'],
            'state' => ['nullable', 'string', 'max:100'],
            'postal_code' => ['required', 'string', 'max:20'],
            'country' => ['required', 'string', 'size:2'],
            'is_default' => ['nullable', 'boolean'],
        ];
    }

    public function messages(): array
    {
        return [
            'type.required' => 'Address type is required',
            'type.enum' => 'Invalid address type',
            'first_name.required' => 'First name is required',
            'last_name.required' => 'Last name is required',
            'address_line_1.required' => 'Address is required',
            'city.required' => 'City is required',
            'postal_code.required' => 'Postal code is required',
            'country.required' => 'Country is required',
            'country.size' => 'Country must be a 2-letter code',
        ];
    }
}
