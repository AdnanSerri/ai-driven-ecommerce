<?php

namespace App\Http\Requests\Profile;

use Illuminate\Foundation\Http\FormRequest;

class UpdateProfileRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'name' => ['sometimes', 'string', 'max:255'],
            'phone' => ['nullable', 'string', 'max:20'],
            'avatar_url' => ['nullable', 'url', 'max:255'],
            'date_of_birth' => ['nullable', 'date', 'before:today'],
            'preferences' => ['nullable', 'array'],
        ];
    }

    public function messages(): array
    {
        return [
            'name.max' => 'Name cannot exceed 255 characters',
            'avatar_url.url' => 'Avatar URL must be a valid URL',
            'date_of_birth.before' => 'Date of birth must be in the past',
        ];
    }
}
