import { Processor, WorkerHost } from '@nestjs/bullmq';
import { Logger } from '@nestjs/common';
import { Job } from 'bullmq';
import { MlService } from '../ml/ml.service';

@Processor('recommendation-feedback', {
  concurrency: 2,
})
export class RecommendationFeedbackProcessor extends WorkerHost {
  private readonly logger = new Logger(RecommendationFeedbackProcessor.name);

  constructor(private mlService: MlService) {
    super();
  }

  async process(
    job: Job<{ userId: number; productId: number; action: string }>,
  ) {
    this.logger.debug(
      `Processing recommendation feedback: user=${job.data.userId}, product=${job.data.productId}`,
    );

    await this.mlService.recordRecommendationFeedback(
      job.data.userId,
      job.data.productId,
      job.data.action,
    );

    // Invalidate cache
    await this.mlService.invalidateCache(`recommendations:${job.data.userId}`);
  }
}
