<?php

namespace Database\Seeders;

use App\Models\Product;
use App\Models\User;
use App\Models\Wishlist;
use Illuminate\Database\Seeder;

class WishlistSeeder extends Seeder
{
    public function run(): void
    {
        $users = User::where('is_admin', false)->get();
        $products = Product::all();

        foreach ($users as $user) {
            if (rand(0, 1)) {
                $selectedProducts = $products->random(rand(1, 5));

                foreach ($selectedProducts as $product) {
                    Wishlist::factory()->create([
                        'user_id' => $user->id,
                        'product_id' => $product->id,
                    ]);
                }
            }
        }
    }
}
