import {
  Controller,
  Get,
  Post,
  Body,
  Query,
  HttpStatus,
  HttpCode,
  HttpException,
  Header,
} from '@nestjs/common';
import { MlService } from './ml.service';
import { CurrentUser } from '../common/decorators';
import { IsString, IsOptional, IsObject, IsIn, IsInt } from 'class-validator';

class RecordInteractionDto {
  @IsIn(['view', 'click', 'purchase', 'review', 'wishlist', 'cart_add', 'cart_remove'])
  interaction_type: string;

  @IsOptional()
  @IsInt()
  product_id?: number;

  @IsOptional()
  @IsInt()
  category_id?: number;

  @IsOptional()
  @IsObject()
  metadata?: Record<string, any>;
}

@Controller('user/personality')
export class PersonalityController {
  constructor(private mlService: MlService) {}

  @Get()
  @Header('Cache-Control', 'no-store, no-cache, must-revalidate')
  async profile(
    @CurrentUser('id') userId: number,
    @Query('refresh') refresh?: string,
  ) {
    const forceRecalculate = refresh === 'true';
    const result = await this.mlService.getUserPersonality(userId, forceRecalculate);
    if (!result || !result.profile) {
      throw new HttpException(
        {
          message: 'Unable to fetch personality profile at this time',
          data: null,
        },
        HttpStatus.SERVICE_UNAVAILABLE,
      );
    }

    const profile = result.profile;
    // Pass through the full ML response with all data
    return {
      data: {
        user_id: userId,
        personality_type: profile.personality_type ?? null,
        dimensions: profile.dimensions ?? {},
        confidence: profile.confidence ?? 0,
        data_points: profile.data_points ?? 0,
        last_updated: profile.last_updated ?? null,
      },
    };
  }

  @Get('traits')
  @Header('Cache-Control', 'no-store, no-cache, must-revalidate')
  async traits(@CurrentUser('id') userId: number) {
    const result = await this.mlService.getUserPersonalityTraits(userId);
    if (!result) {
      throw new HttpException(
        {
          message: 'Unable to fetch personality traits at this time',
          data: null,
        },
        HttpStatus.SERVICE_UNAVAILABLE,
      );
    }
    // Pass through the full traits response with descriptions and impact
    return {
      data: {
        personality_type: result.personality_type ?? null,
        dimensions: result.dimensions ?? [],
        traits: result.traits ?? [],
        recommendations_impact: result.recommendations_impact ?? {},
      },
    };
  }

  @Post('interaction')
  @HttpCode(HttpStatus.OK)
  async recordInteraction(
    @CurrentUser('id') userId: number,
    @Body() dto: RecordInteractionDto,
  ) {
    // Build data payload matching Laravel: array_filter([...])
    const data: Record<string, any> = {};
    if (dto.product_id !== undefined) data.product_id = dto.product_id;
    if (dto.category_id !== undefined) data.category_id = dto.category_id;
    if (dto.metadata !== undefined) data.metadata = dto.metadata;

    const result = await this.mlService.updateUserPersonality(
      userId,
      dto.interaction_type,
      data,
    );
    if (!result) {
      throw new HttpException(
        { message: 'Unable to record interaction at this time' },
        HttpStatus.SERVICE_UNAVAILABLE,
      );
    }
    return { message: 'Interaction recorded successfully' };
  }
}
