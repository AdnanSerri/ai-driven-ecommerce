import { Module } from '@nestjs/common';
import { CacheModule } from '@nestjs/cache-manager';
import { HttpModule } from '@nestjs/axios';
import { BullModule } from '@nestjs/bullmq';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { redisStore } from 'cache-manager-ioredis-yet';
import { MlService } from './ml.service';
import { RecommendationsController } from './recommendations.controller';
import { PersonalityController } from './personality.controller';
import { InteractionController } from './interaction.controller';

@Module({
  imports: [
    HttpModule,
    BullModule.registerQueue(
      { name: 'kafka-events' },
      { name: 'recommendation-feedback' },
    ),
    CacheModule.registerAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: async (config: ConfigService) => ({
        store: await redisStore({
          host: config.get('REDIS_HOST', 'localhost'),
          port: config.get<number>('REDIS_PORT', 6379),
          keyPrefix: 'nest:ml:',
        }),
      }),
    }),
  ],
  controllers: [
    RecommendationsController,
    PersonalityController,
    InteractionController,
  ],
  providers: [MlService],
  exports: [MlService],
})
export class MlModule {}
