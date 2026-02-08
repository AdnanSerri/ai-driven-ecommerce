import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { CurrentUser } from '../common/decorators';
import { IsInt, IsIn, IsOptional, IsObject } from 'class-validator';
import { MlService } from './ml.service';

class TrackInteractionDto {
  @IsInt()
  product_id: number;

  @IsOptional()
  @IsIn(['view', 'click', 'add_to_wishlist', 'share', 'cart_add', 'wishlist_add', 'purchase'])
  action?: string;

  @IsOptional()
  @IsIn(['view', 'click', 'add_to_wishlist', 'share', 'cart_add', 'wishlist_add', 'purchase'])
  interaction_type?: string;

  @IsOptional()
  @IsObject()
  metadata?: Record<string, any>;
}

@Controller('interactions')
export class InteractionController {
  constructor(
    @InjectQueue('kafka-events') private kafkaQueue: Queue,
    private mlService: MlService,
  ) {}

  @Post()
  @HttpCode(HttpStatus.OK)
  async track(
    @CurrentUser('id') userId: number,
    @Body() dto: TrackInteractionDto,
  ) {
    // Accept both `action` (Laravel convention) and `interaction_type` (frontend convention)
    const action = dto.action || dto.interaction_type;
    if (!action) {
      return { message: 'Interaction tracked' };
    }

    // Publish to Kafka for ML service processing
    this.kafkaQueue
      .add(
        'publish',
        {
          topic: 'user.interaction',
          data: {
            event_type: 'user.interaction',
            user_id: userId,
            product_id: dto.product_id,
            action,
            metadata: dto.metadata || [],
            timestamp: new Date().toISOString(),
          },
        },
        { attempts: 3, backoff: { type: 'fixed', delay: 5000 } },
      )
      .catch(() => {});

    // Invalidate recommendation cache so next request gets fresh data
    // This ensures recommendations update after user interactions
    this.mlService.invalidateCache(`recommendations:${userId}`).catch(() => {});

    // On purchase, also invalidate personality cache (significant signal)
    if (action === 'purchase') {
      this.mlService.invalidateCache(`personality:${userId}`).catch(() => {});
    }

    return { message: 'Interaction tracked' };
  }
}
