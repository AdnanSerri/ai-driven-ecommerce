<?php

namespace App\Models;

use Filament\Models\Contracts\FilamentUser;
use Filament\Panel;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\HasOne;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens;
use Serri\Alchemist\Concerns\HasAlchemyFormulas;
use Serri\Alchemist\Decorators\Relation;

class User extends Authenticatable implements FilamentUser
{
    /** @use HasFactory<\Database\Factories\UserFactory> */
    use HasApiTokens, HasFactory, Notifiable, HasAlchemyFormulas;

    protected $guarded = ['id'];

    protected $fillable = [
        'name',
        'email',
        'password',
        'is_admin',
        'phone',
        'avatar_url',
        'date_of_birth',
        'preferences',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
            'is_admin' => 'boolean',
            'date_of_birth' => 'date',
            'preferences' => 'array',
        ];
    }

    public function canAccessPanel(Panel $panel): bool
    {
        return $this->is_admin;
    }

    #[Relation]
    public function reviews(): HasMany
    {
        return $this->hasMany(Review::class);
    }

    #[Relation]
    public function addresses(): HasMany
    {
        return $this->hasMany(Address::class);
    }

    #[Relation]
    public function cart(): HasOne
    {
        return $this->hasOne(Cart::class);
    }

    #[Relation]
    public function orders(): HasMany
    {
        return $this->hasMany(Order::class);
    }

    #[Relation]
    public function wishlists(): HasMany
    {
        return $this->hasMany(Wishlist::class);
    }

    #[Relation]
    public function interactions(): HasMany
    {
        return $this->hasMany(UserInteraction::class);
    }

    public function getOrCreateCart(): Cart
    {
        return $this->cart ?? $this->cart()->create();
    }

    public function getDefaultShippingAddress(): ?Address
    {
        return $this->addresses()
            ->where('type', 'shipping')
            ->where('is_default', true)
            ->first();
    }

    public function getDefaultBillingAddress(): ?Address
    {
        return $this->addresses()
            ->where('type', 'billing')
            ->where('is_default', true)
            ->first();
    }
}
