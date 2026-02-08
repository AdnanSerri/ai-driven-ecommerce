import { Injectable, Logger, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Kafka, Producer } from 'kafkajs';

@Injectable()
export class KafkaService implements OnModuleDestroy {
  private readonly logger = new Logger(KafkaService.name);
  private kafka: Kafka | null = null;
  private producer: Producer | null = null;
  private connected = false;
  private readonly enabled: boolean;
  private readonly brokers: string[];

  constructor(private config: ConfigService) {
    this.enabled = config.get('KAFKA_ENABLED', 'true') === 'true';
    this.brokers = (config.get('KAFKA_BROKERS', 'localhost:29092')).split(',');
  }

  private async getProducer(): Promise<Producer> {
    if (this.producer && this.connected) return this.producer;

    if (!this.kafka) {
      this.kafka = new Kafka({
        clientId: 'nestjs-backend',
        brokers: this.brokers,
        retry: { retries: 3, initialRetryTime: 100 },
      });
    }

    this.producer = this.kafka.producer();
    await this.producer.connect();
    this.connected = true;
    return this.producer;
  }

  async publish(topic: string, data: Record<string, any>): Promise<void> {
    if (!this.enabled) {
      this.logger.debug(`Kafka disabled, skipping publish to ${topic}`);
      return;
    }

    const maxRetries = 3;
    const backoffMs = 100;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const producer = await this.getProducer();
        await producer.send({
          topic,
          messages: [
            {
              value: JSON.stringify({
                ...data,
                timestamp: new Date().toISOString(),
              }),
            },
          ],
        });
        this.logger.debug(`Published to ${topic}`);
        return;
      } catch (error) {
        this.logger.warn(
          `Kafka publish attempt ${attempt}/${maxRetries} to ${topic} failed: ${error}`,
        );
        this.connected = false;
        this.producer = null;
        if (attempt < maxRetries) {
          await new Promise((r) => setTimeout(r, backoffMs * attempt));
        }
      }
    }

    this.logger.error(`Failed to publish to ${topic} after ${maxRetries} attempts`);
  }

  async onModuleDestroy() {
    if (this.producer && this.connected) {
      try {
        await this.producer.disconnect();
      } catch {
        // ignore disconnect errors
      }
    }
  }
}
