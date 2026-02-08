import { IsOptional, IsInt, Min, Max } from 'class-validator';

export class PaginationDto {
  @IsOptional()
  @IsInt()
  @Min(1)
  page?: number = 1;

  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  per_page?: number = 15;
}

export interface PaginatedResponse<T> {
  data: T[];
  links: {
    first: string;
    last: string;
    prev: string | null;
    next: string | null;
  };
  meta: {
    current_page: number;
    from: number | null;
    last_page: number;
    per_page: number;
    to: number | null;
    total: number;
  };
}

export function paginate<T>(
  data: T[],
  total: number,
  page: number,
  perPage: number,
  baseUrl: string = '',
): PaginatedResponse<T> {
  const lastPage = Math.ceil(total / perPage) || 1;
  const from = total > 0 ? (page - 1) * perPage + 1 : null;
  const to = total > 0 ? Math.min(page * perPage, total) : null;

  return {
    data,
    links: {
      first: `${baseUrl}?page=1`,
      last: `${baseUrl}?page=${lastPage}`,
      prev: page > 1 ? `${baseUrl}?page=${page - 1}` : null,
      next: page < lastPage ? `${baseUrl}?page=${page + 1}` : null,
    },
    meta: {
      current_page: page,
      from,
      last_page: lastPage,
      per_page: perPage,
      to,
      total,
    },
  };
}
