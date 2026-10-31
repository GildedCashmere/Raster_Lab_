function positiveInteger(value: string | undefined, fallback: number): number {
  const result = value === undefined ? fallback : Number(value);
  if (!Number.isSafeInteger(result) || result <= 0) throw new Error('Image limits must be positive integers. Check the frontend environment settings.');
  return result;
}

export const API_URL = (import.meta.env.PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');
export const MAX_UPLOAD_BYTES = positiveInteger(import.meta.env.PUBLIC_MAX_UPLOAD_BYTES, 8 * 1024 * 1024);
export const MAX_IMAGE_PIXELS = positiveInteger(import.meta.env.PUBLIC_MAX_IMAGE_PIXELS, 12_000_000);
export const uploadLimitLabel = `${MAX_UPLOAD_BYTES / 1024 / 1024} MiB`;
export const pixelLimitLabel = `${MAX_IMAGE_PIXELS / 1_000_000} MP`;
