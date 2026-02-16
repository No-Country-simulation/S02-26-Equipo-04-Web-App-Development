const fallbackApiBaseUrl = "http://localhost:8000";

function normalizeBaseUrl(value: string | undefined) {
  if (!value) {
    return fallbackApiBaseUrl;
  }

  const trimmedValue = value.trim();
  return trimmedValue.length > 0 ? trimmedValue : fallbackApiBaseUrl;
}

export const env = {
  apiBaseUrl: normalizeBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL),
};
