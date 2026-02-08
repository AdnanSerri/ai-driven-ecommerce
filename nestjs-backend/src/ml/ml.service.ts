import { Inject, Injectable, Logger } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { Cache } from 'cache-manager';
import { firstValueFrom } from 'rxjs';

@Injectable()
export class MlService {
  private readonly logger = new Logger(MlService.name);
  private readonly baseUrl: string;
  private readonly authToken: string;

  constructor(
    private httpService: HttpService,
    private config: ConfigService,
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
  ) {
    this.baseUrl = config.get('ML_SERVICE_URL', 'http://localhost:8001');
    this.authToken = config.get(
      'ML_SERVICE_AUTH_TOKEN',
      'dev-token-change-in-production',
    );
  }

  private get headers() {
    return {
      'X-Service-Auth': this.authToken,
      'Content-Type': 'application/json',
    };
  }

  async invalidateCache(key: string) {
    try {
      // Use the simple del method from cache-manager
      // The keyPrefix 'nest:ml:' is automatically added by the store
      await this.cacheManager.del(key);
      this.logger.debug(`Cache invalidated for key "${key}"`);
    } catch (error) {
      this.logger.warn(`Cache invalidation failed for key "${key}": ${error}`);
    }
  }

  private async get(path: string): Promise<any | null> {
    try {
      const { data } = await firstValueFrom(
        this.httpService.get(`${this.baseUrl}${path}`, {
          headers: this.headers,
          timeout: 10000,
        }),
      );
      return data;
    } catch (error) {
      this.logger.warn(`ML GET ${path} failed: ${error}`);
      return null;
    }
  }

  private async post(path: string, body: any): Promise<any | null> {
    try {
      const { data } = await firstValueFrom(
        this.httpService.post(`${this.baseUrl}${path}`, body, {
          headers: this.headers,
          timeout: 10000,
        }),
      );
      return data;
    } catch (error) {
      this.logger.warn(`ML POST ${path} failed: ${error}`);
      return null;
    }
  }

  async analyzeSentiment(text: string, userId: number) {
    return this.post('/api/v1/sentiment/analyze', { text, user_id: userId });
  }

  async getRecommendations(userId: number, limit = 10) {
    // No caching - recommendations should always reflect latest user interactions
    return this.get(`/api/v1/recommendations/${userId}?limit=${limit}`);
  }

  async getSimilarProducts(productId: number, limit = 10) {
    const cacheKey = `similar:${productId}:${limit}`;
    const cached = await this.cacheManager.get(cacheKey);
    if (cached) return cached;

    const data = await this.get(
      `/api/v1/recommendations/similar/${productId}?limit=${limit}`,
    );
    // Only cache if we got actual similar products (not empty results)
    if (data?.similar_products?.length > 0) {
      await this.cacheManager.set(cacheKey, data, 300_000); // 5 min in ms
    }
    return data;
  }

  async getUserPersonality(userId: number, forceRecalculate = false) {
    const cacheKey = `personality:${userId}`;

    if (!forceRecalculate) {
      const cached = await this.cacheManager.get(cacheKey);
      if (cached) return cached;
    }

    const url = forceRecalculate
      ? `/api/v1/personality/profile/${userId}?force_recalculate=true`
      : `/api/v1/personality/profile/${userId}`;
    const data = await this.get(url);
    if (data) await this.cacheManager.set(cacheKey, data, 120_000); // 2 min in ms
    return data;
  }

  async getUserPersonalityTraits(userId: number) {
    return this.get(`/api/v1/personality/traits/${userId}`);
  }

  async updateUserPersonality(
    userId: number,
    interactionType: string,
    metadata: any,
  ) {
    const result = await this.post('/api/v1/personality/update', {
      user_id: userId,
      interaction_type: interactionType,
      metadata,
    });
    await this.invalidateCache(`personality:${userId}`);
    return result;
  }

  async recordRecommendationFeedback(
    userId: number,
    productId: number,
    action: string,
  ) {
    const result = await this.post('/api/v1/recommendations/feedback', {
      user_id: userId,
      product_id: productId,
      action,
    });
    await this.invalidateCache(`recommendations:${userId}`);
    return result;
  }

  async getFrequentlyBoughtTogether(productId: number, limit = 5) {
    const cacheKey = `bought-together:${productId}:${limit}`;
    const cached = await this.cacheManager.get(cacheKey);
    if (cached) return cached;

    const data = await this.get(
      `/api/v1/recommendations/bought-together/${productId}?limit=${limit}`,
    );
    // Cache for 1 hour (product relationships change slowly)
    if (data?.products?.length > 0) {
      await this.cacheManager.set(cacheKey, data, 3600_000);
    }
    return data;
  }

  async getTrendingProducts(limit = 10, categoryId?: number) {
    const cacheKey = `trending:${categoryId ?? 'all'}:${limit}`;
    const cached = await this.cacheManager.get(cacheKey);
    if (cached) return cached;

    let path = `/api/v1/recommendations/trending?limit=${limit}`;
    if (categoryId) {
      path += `&category_id=${categoryId}`;
    }
    const data = await this.get(path);
    // Cache for 15 minutes (trending changes more frequently)
    if (data?.products?.length > 0) {
      await this.cacheManager.set(cacheKey, data, 900_000);
    }
    return data;
  }

  async markNotInterested(userId: number, productId: number, reason?: string) {
    let path = `/api/v1/recommendations/not-interested?user_id=${userId}&product_id=${productId}`;
    if (reason) {
      path += `&reason=${encodeURIComponent(reason)}`;
    }
    const result = await this.post(path, {});
    await this.invalidateCache(`recommendations:${userId}`);
    return result;
  }

  async removeNotInterested(userId: number, productId: number) {
    try {
      const { data } = await firstValueFrom(
        this.httpService.delete(
          `${this.baseUrl}/api/v1/recommendations/not-interested?user_id=${userId}&product_id=${productId}`,
          { headers: this.headers, timeout: 10000 },
        ),
      );
      await this.invalidateCache(`recommendations:${userId}`);
      return data;
    } catch (error) {
      this.logger.warn(`ML DELETE not-interested failed: ${error}`);
      return null;
    }
  }

  async getRecommendationsWithSession(
    userId: number,
    limit = 10,
    sessionProductIds?: number[],
  ) {
    let path = `/api/v1/recommendations/${userId}?limit=${limit}`;
    if (sessionProductIds && sessionProductIds.length > 0) {
      path += `&session_product_ids=${sessionProductIds.join(',')}`;
    }
    return this.get(path);
  }
}
