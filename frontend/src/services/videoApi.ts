import { env } from "@/src/config/env";

export type VideoUploadResponse = {
  video_id: string;
  bucket: string;
  object_key: string;
  filename: string;
  content_type: string | null;
  size_bytes: number;
  user_id: string | null;
  storage_path: string;
  uploaded_at: string;
};

export type VideoUrlResponse = {
  video_id: string;
  url: string;
  expires_in_seconds: number;
  filename: string;
};

const apiBaseUrl = env.apiBaseUrl.replace(/\/$/, "");

export class VideoApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "VideoApiError";
    this.status = status;
  }
}

function getErrorMessage(payload: unknown) {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const maybePayload = payload as Record<string, unknown>;
  const detail = maybePayload.detail;

  if (typeof detail === "string" && detail.trim().length > 0) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const firstDetail = detail[0];
    if (firstDetail && typeof firstDetail === "object") {
      const message = (firstDetail as Record<string, unknown>).msg;
      if (typeof message === "string" && message.trim().length > 0) {
        return message;
      }
    }
  }

  const message = maybePayload.message;
  if (typeof message === "string" && message.trim().length > 0) {
    return message;
  }

  return null;
}

async function parseResponse<T>(response: Response) {
  if (response.status === 204) {
    return null as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const payload: unknown = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const apiMessage = getErrorMessage(payload);
    const fallbackMessage = typeof payload === "string" && payload.trim().length > 0 ? payload : `Error ${response.status}`;
    throw new VideoApiError(apiMessage ?? fallbackMessage, response.status);
  }

  return payload as T;
}

export const videoApi = {
  async upload(file: File, token?: string | null) {
    const formData = new FormData();
    formData.append("file", file);

    const hasToken = Boolean(token && token.trim().length > 0);
    const endpoint = "/api/v1/videos/upload";

    const response = await fetch(`${apiBaseUrl}${endpoint}`, {
      method: "POST",
      body: formData,
      headers: hasToken
        ? {
            Authorization: `Bearer ${token}`
          }
        : undefined
    });

    return parseResponse<VideoUploadResponse>(response);
  },

  async getVideoUrl(videoId: string, expiresInSeconds = 3600) {
    const params = new URLSearchParams({
      expires_in: String(expiresInSeconds)
    });

    const response = await fetch(`${apiBaseUrl}/api/v1/videos/${videoId}/url?${params.toString()}`, {
      method: "GET"
    });

    return parseResponse<VideoUrlResponse>(response);
  }
};
