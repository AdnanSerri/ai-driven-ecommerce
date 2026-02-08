import {
  IsOptional,
  IsString,
  MaxLength,
  IsUrl,
  IsDateString,
  IsObject,
} from 'class-validator';

export class UpdateProfileDto {
  @IsOptional()
  @IsString()
  @MaxLength(255)
  name?: string;

  @IsOptional()
  @IsString()
  @MaxLength(20)
  phone?: string;

  @IsOptional()
  @IsUrl()
  @MaxLength(255)
  avatar_url?: string;

  @IsOptional()
  @IsDateString()
  date_of_birth?: string;

  @IsOptional()
  @IsObject()
  preferences?: Record<string, any>;
}
