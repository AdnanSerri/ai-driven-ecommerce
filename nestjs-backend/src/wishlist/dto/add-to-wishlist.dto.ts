import { IsInt } from 'class-validator';

export class AddToWishlistDto {
  @IsInt()
  product_id: number;
}
