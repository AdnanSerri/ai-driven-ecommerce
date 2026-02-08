import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bullmq';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { SentimentProcessor } from './sentiment.processor';
import { KafkaEventProcessor } from './kafka-event.processor';
import { RecommendationFeedbackProcessor } from './recommendation-feedback.processor';
import { MlModule } from '../ml/ml.module';
import { KafkaModule } from '../kafka/kafka.module';

@Module({
  imports: [
    BullModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        connection: {
          host: config.get('REDIS_HOST', '127.0.0.1'),
          port: config.get<number>('REDIS_PORT', 6379),
        },
      }),
    }),
    BullModule.registerQueue(
      { name: 'sentiment-analysis' },
      { name: 'kafka-events' },
      { name: 'recommendation-feedback' },
    ),
    MlModule,
    KafkaModule,
  ],
  providers: [
    SentimentProcessor,
    KafkaEventProcessor,
    RecommendationFeedbackProcessor,
  ],
  exports: [BullModule],
})
export class JobsModule {}
