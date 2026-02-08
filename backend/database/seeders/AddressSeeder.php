<?php

namespace Database\Seeders;

use App\Models\Address;
use App\Models\User;
use Illuminate\Database\Seeder;

class AddressSeeder extends Seeder
{
    public function run(): void
    {
        $users = User::where('is_admin', false)->get();

        foreach ($users as $user) {
            Address::factory()
                ->shipping()
                ->default()
                ->create(['user_id' => $user->id]);

            if (rand(0, 1)) {
                Address::factory()
                    ->billing()
                    ->default()
                    ->create(['user_id' => $user->id]);
            }

            if (rand(0, 1)) {
                Address::factory(rand(1, 2))
                    ->create(['user_id' => $user->id]);
            }
        }
    }
}
