import { Processor, WorkerHost } from '@nestjs/bullmq';
import { Logger } from '@nestjs/common';
import { Job } from 'bullmq';
import { MlService } from '../ml/ml.service';
import { PrismaService } from '../prisma/prisma.service';

@Processor('sentiment-analysis', {
  concurrency: 2,
})
export class SentimentProcessor extends WorkerHost {
  private readonly logger = new Logger(SentimentProcessor.name);

  constructor(
    private mlService: MlService,
    private prisma: PrismaService,
  ) {
    super();
  }

  async process(job: Job<{ reviewId: number; text: string; userId: number }>) {
    this.logger.debug(`Processing sentiment for review ${job.data.reviewId}`);

    const response = await this.mlService.analyzeSentiment(
      job.data.text,
      job.data.userId,
    );
    if (!response?.result) {
      throw new Error('Sentiment analysis failed');
    }

    const sentiment = response.result;

    await this.prisma.review.update({
      where: { id: BigInt(job.data.reviewId) },
      data: {
        sentimentScore: sentiment.score,
        sentimentLabel: sentiment.label,
        sentimentConfidence: sentiment.confidence,
        sentimentAnalyzedAt: new Date(),
      },
    });

    this.logger.debug(
      `Sentiment for review ${job.data.reviewId}: ${sentiment.label} (${sentiment.score})`,
    );
  }
}
