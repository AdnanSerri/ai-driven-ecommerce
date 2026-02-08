<?php

namespace Database\Seeders;

use App\Models\Product;
use App\Models\ProductImage;
use Illuminate\Database\Seeder;

class ProductImageSeeder extends Seeder
{
    public function run(): void
    {
        $products = Product::all();

        foreach ($products as $product) {
            ProductImage::factory()
                ->primary()
                ->create(['product_id' => $product->id]);

            if (rand(0, 1)) {
                ProductImage::factory(rand(1, 3))
                    ->create(['product_id' => $product->id]);
            }
        }
    }
}
