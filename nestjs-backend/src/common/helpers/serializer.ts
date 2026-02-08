/**
 * Converts BigInt IDs and Decimal values to numbers/strings for JSON serialization.
 * Matches the Laravel Alchemist formula output format.
 */
export function serialize(obj: any): any {
  if (obj === null || obj === undefined) return obj;
  if (typeof obj === 'bigint') return Number(obj);
  // Prisma Decimal has a toFixed method
  if (typeof obj === 'object' && obj.constructor?.name === 'Decimal') {
    return parseFloat(obj.toString());
  }
  if (obj instanceof Date) return obj.toISOString();
  if (Array.isArray(obj)) return obj.map(serialize);
  if (typeof obj === 'object') {
    const result: Record<string, any> = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = serialize(value);
    }
    return result;
  }
  return obj;
}

/**
 * Pick specific fields from an object and serialize them.
 */
export function pick<T extends Record<string, any>>(
  obj: T,
  fields: string[],
): Record<string, any> {
  const result: Record<string, any> = {};
  for (const field of fields) {
    if (field in obj) {
      result[field] = serialize(obj[field]);
    }
  }
  return result;
}
