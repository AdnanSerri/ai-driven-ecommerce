<?php

namespace Database\Seeders;

use App\Models\Cart;
use App\Models\CartItem;
use App\Models\Product;
use App\Models\User;
use Illuminate\Database\Seeder;

class CartSeeder extends Seeder
{
    public function run(): void
    {
        $users = User::where('is_admin', false)->take(5)->get();
        $products = Product::where('stock', '>', 0)->get();

        foreach ($users as $user) {
            if (rand(0, 1)) {
                $cart = Cart::factory()->create(['user_id' => $user->id]);

                $selectedProducts = $products->random(rand(1, 3));

                foreach ($selectedProducts as $product) {
                    CartItem::factory()->create([
                        'cart_id' => $cart->id,
                        'product_id' => $product->id,
                        'quantity' => rand(1, min(3, $product->stock ?: 3)),
                    ]);
                }
            }
        }
    }
}
