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

export type AutoReframeJobItem = {
  job_id: string;
  job_type: string;
  status: string;
  start_sec: number;
  end_sec: number;
  created_at: string;
};

export type AutoReframeResponse = {
  video_id: string;
  total_jobs: number;
  clip_duration_sec: number;
  used_video_duration_sec: number | null;
  jobs: AutoReframeJobItem[];
};

export type ReframeJobRequest = {
  start_sec: number;
  end_sec: number;
  crop_to_vertical?: boolean;
  subtitles?: boolean;
  face_tracking?: boolean;
  color_filter?: boolean;
  output_style?: "vertical" | "speaker_split";
  content_profile?: "auto" | "interview" | "sports" | "music";
};

export type ReframeJobResponse = {
  job_id: string;
  job_type: string;
  status: string;
  filename: string;
  start_sec: number;
  end_sec: number;
  created_at: string;
};

export type JobStatusResponse = {
  job_id: string;
  status: string;
  output_path: string | null;
};

export type UserClipItem = {
  job_id: string;
  video_id: string;
  status: string;
  output_path: string | null;
  source_filename: string;
  created_at: string;
};

export type UserClipsResponse = {
  total: number;
  limit: number;
  offset: number;
  clips: UserClipItem[];
};

export type UserClipDetailResponse = {
  clip: UserClipItem;
};

export type UserVideoItem = {
  video_id: string;
  filename: string;
  status: string | null;
  uploaded_at: string;
  preview_url: string | null;
};

export type UserVideoDetail = {
  video_id: string;
  filename: string;
  status: string | null;
  uploaded_at: string;
  updated_at: string;
  storage_path: string | null;
  preview_url: string | null;
};

export type UserVideosResponse = {
  total: number;
  limit: number;
  offset: number;
  videos: UserVideoItem[];
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
  },

  async createAutoReframeJobs(
    videoId: string,
    token: string,
    options?: {
      clipsCount?: number;
      clipDurationSec?: number;
      outputStyle?: "vertical" | "speaker_split";
      contentProfile?: "auto" | "interview" | "sports" | "music";
    }
  ) {
    const body: Record<string, unknown> = {
      output_style: options?.outputStyle ?? "vertical",
      content_profile: options?.contentProfile ?? "auto"
    };

    if (typeof options?.clipsCount === "number") {
      body.clips_count = options.clipsCount;
    }
    if (typeof options?.clipDurationSec === "number") {
      body.clip_duration_sec = options.clipDurationSec;
    }

    const response = await fetch(`${apiBaseUrl}/api/v1/jobs/reframe/${videoId}/auto`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(body)
    });

    return parseResponse<AutoReframeResponse>(response);
  },

  async createReframeJob(videoId: string, token: string, payload: ReframeJobRequest) {
    const response = await fetch(`${apiBaseUrl}/api/v1/jobs/reframe/${videoId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    return parseResponse<ReframeJobResponse>(response);
  },

  async getJobStatus(jobId: string, token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/jobs/status/${jobId}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<JobStatusResponse>(response);
  },

  async getMyClips(token: string, options?: { limit?: number; offset?: number; query?: string }) {
    const params = new URLSearchParams({
      limit: String(options?.limit ?? 50),
      offset: String(options?.offset ?? 0)
    });

    const query = options?.query?.trim();
    if (query) {
      params.set("q", query);
    }

    const response = await fetch(`${apiBaseUrl}/api/v1/jobs/my-clips?${params.toString()}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<UserClipsResponse>(response);
  },

  async deleteMyClip(jobId: string, token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/jobs/${jobId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<null>(response);
  },

  async getMyClipById(jobId: string, token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/jobs/${jobId}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<UserClipDetailResponse>(response);
  },

  async getMyVideos(token: string, options?: { limit?: number; offset?: number; query?: string }) {
    const params = new URLSearchParams({
      limit: String(options?.limit ?? 20),
      offset: String(options?.offset ?? 0)
    });

    const query = options?.query?.trim();
    if (query) {
      params.set("q", query);
    }

    const response = await fetch(`${apiBaseUrl}/api/v1/videos/my-videos?${params.toString()}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<UserVideosResponse>(response);
  },

  async getMyVideoById(videoId: string, token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/videos/${videoId}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<UserVideoDetail>(response);
  },

  async updateMyVideo(videoId: string, token: string, payload: { filename: string }) {
    const response = await fetch(`${apiBaseUrl}/api/v1/videos/${videoId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    return parseResponse<UserVideoItem>(response);
  },

  async deleteMyVideo(videoId: string, token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/videos/${videoId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<null>(response);
  }
};
