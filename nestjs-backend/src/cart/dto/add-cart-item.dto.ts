import { IsInt, Min, Max } from 'class-validator';

export class AddCartItemDto {
  @IsInt()
  product_id: number;

  @IsInt()
  @Min(1)
  @Max(100)
  quantity: number;
}
