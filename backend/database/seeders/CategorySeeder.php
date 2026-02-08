<?php

namespace Database\Seeders;

use App\Models\Category;
use Illuminate\Database\Seeder;

class CategorySeeder extends Seeder
{
    public function run(): void
    {
        $parentCategories = Category::factory(8)->create();

        foreach ($parentCategories as $parent) {
            Category::factory(rand(2, 4))->child($parent)->create();
        }
    }
}