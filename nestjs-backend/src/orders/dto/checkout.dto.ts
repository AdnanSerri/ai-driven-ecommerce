import { IsOptional, IsInt, IsString, MaxLength } from 'class-validator';

export class CheckoutDto {
  @IsOptional()
  @IsInt()
  shipping_address_id?: number;

  @IsOptional()
  @IsInt()
  billing_address_id?: number;

  @IsOptional()
  @IsString()
  @MaxLength(1000)
  notes?: string;
}
