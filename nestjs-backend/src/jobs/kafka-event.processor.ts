import { Processor, WorkerHost } from '@nestjs/bullmq';
import { Logger } from '@nestjs/common';
import { Job } from 'bullmq';
import { KafkaService } from '../kafka/kafka.service';

@Processor('kafka-events', {
  concurrency: 5,
})
export class KafkaEventProcessor extends WorkerHost {
  private readonly logger = new Logger(KafkaEventProcessor.name);

  constructor(private kafkaService: KafkaService) {
    super();
  }

  async process(job: Job<{ topic: string; data: Record<string, any> }>) {
    this.logger.debug(`Publishing Kafka event to ${job.data.topic}`);
    await this.kafkaService.publish(job.data.topic, job.data.data);
  }
}
