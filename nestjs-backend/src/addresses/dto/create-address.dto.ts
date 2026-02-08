import {
  IsString,
  IsOptional,
  IsBoolean,
  IsIn,
  MaxLength,
  Length,
} from 'class-validator';

export class CreateAddressDto {
  @IsOptional()
  @IsString()
  @MaxLength(100)
  label?: string;

  @IsIn(['shipping', 'billing'])
  type: string;

  @IsString()
  @MaxLength(100)
  first_name: string;

  @IsString()
  @MaxLength(100)
  last_name: string;

  @IsOptional()
  @IsString()
  @MaxLength(20)
  phone?: string;

  @IsString()
  @MaxLength(255)
  address_line_1: string;

  @IsOptional()
  @IsString()
  @MaxLength(255)
  address_line_2?: string;

  @IsString()
  @MaxLength(100)
  city: string;

  @IsOptional()
  @IsString()
  @MaxLength(100)
  state?: string;

  @IsString()
  @MaxLength(20)
  postal_code: string;

  @IsString()
  @Length(2, 2)
  country: string;

  @IsOptional()
  @IsBoolean()
  is_default?: boolean;
}
