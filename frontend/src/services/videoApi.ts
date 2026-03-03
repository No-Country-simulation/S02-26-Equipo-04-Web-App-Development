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

export type VideoFromJobResponse = {
  video_id: string;
  bucket: string;
  object_key: string;
  filename: string;
  user_id: string | null;
  storage_path: string;
  uploaded_at: string;
};

export type YoutubePublishRequest = {
  title?: string;
  description?: string;
  privacy?: "public" | "private" | "unlisted";
};

export type YoutubePublishResponse = {
  success: boolean;
  message: string;
  job_id: string;
  youtube_video_id: string;
  youtube_url: string;
  title: string;
  privacy: string;
  thumbnail_url: string | null;
};

export type YoutubeConnectionStatus = {
  connected: boolean;
  message: string | null;
  provider_username: string | null;
  provider_user_id: string | null;
  token_expires_at: string | null;
  is_expired: boolean | null;
};

export type YoutubeMetadataSuggestionResponse = {
  title: string;
  description: string;
  hashtags: string[];
  tags: string[];
  provider: string;
  generated_with_ai: boolean;
};

export type AudioUploadResponse = {
  audio_id: string;
  bucket: string;
  object_key: string;
  filename: string;
  content_type: string | null;
  size_bytes: number;
  user_id: string | null;
  storage_path: string;
  uploaded_at: string;
};

export type AudioUrlResponse = {
  audio_id: string;
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
  orchestrator_job_id?: string;
};

type AutoReframeResponseV2 = {
  job_id: string;
  job_type: string;
  status: string;
  filename: string;
  total_jobs: number;
  created_at: string;
};

export type ReframeJobRequest = {
  start_sec: number;
  end_sec: number;
  crop_to_vertical?: boolean;
  subtitles?: boolean;
  watermark?: string;
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

export type AddAudioJobRequest = {
  audio_id: string;
  audio_offset_sec: number;
  audio_start_sec: number;
  audio_end_sec: number;
  audio_volume: number;
};

export type AddAudioJobResponse = {
  job_id: string;
  job_type: string;
  status: string;
  filename: string;
  audio_filename: string;
  audio_volume: number;
  created_at: string;
};

export type JobStatusResponse = {
  job_id: string;
  status: string;
  output_path: string | null;
  subtitles_path: string | null;
  child_jobs: string[];
};

type RawOutputPath = string | Record<string, unknown> | null;

type RawJobStatusResponse = {
  job_id: string;
  status: string;
  output_path: RawOutputPath;
};

export type UserClipItem = {
  job_id: string;
  video_id: string;
  status: string;
  output_path: string | null;
  source_filename: string;
  created_at: string;
};

type RawUserClipItem = {
  job_id: string;
  video_id: string;
  status: string;
  output_path: RawOutputPath;
  source_filename: string;
  created_at: string;
};

type RawUserClipsResponse = {
  total: number;
  limit: number;
  offset: number;
  clips: RawUserClipItem[];
};

type RawUserClipDetailResponse = {
  clip: RawUserClipItem;
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

export type UserAudioItem = {
  audio_id: string;
  filename: string;
  status: string | null;
  uploaded_at: string;
};

export type UserAudiosResponse = {
  total: number;
  limit: number;
  offset: number;
  audios: UserAudioItem[];
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

function extractPlayableUrl(outputPath: RawOutputPath) {
  if (!outputPath) {
    return null;
  }

  if (typeof outputPath === "string") {
    const cleaned = outputPath.trim();
    return cleaned.length > 0 ? cleaned : null;
  }

  if (typeof outputPath !== "object") {
    return null;
  }

  const map = outputPath as Record<string, unknown>;
  const preferredKeys = ["video", "url", "preview_url", "previewUrl"];

  for (const key of preferredKeys) {
    const candidate = map[key];
    if (typeof candidate === "string" && candidate.trim().length > 0) {
      return candidate;
    }
  }

  for (const candidate of Object.values(map)) {
    if (typeof candidate === "string" && candidate.trim().length > 0) {
      return candidate;
    }
  }

  return null;
}

function extractStringFromKeys(map: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const candidate = map[key];
    if (typeof candidate === "string" && candidate.trim().length > 0) {
      return candidate;
    }
  }

  return null;
}

function extractChildJobIds(outputPath: RawOutputPath) {
  if (!outputPath || typeof outputPath !== "object") {
    return [] as string[];
  }

  const map = outputPath as Record<string, unknown>;
  const jobs = map.jobs;

  if (!Array.isArray(jobs)) {
    return [] as string[];
  }

  return jobs.filter((job): job is string => typeof job === "string" && job.trim().length > 0);
}

function extractSubtitlesUrl(outputPath: RawOutputPath) {
  if (!outputPath || typeof outputPath !== "object") {
    return null;
  }

  const map = outputPath as Record<string, unknown>;
  return extractStringFromKeys(map, ["subtitles", "subtitle", "captions", "srt"]);
}

function normalizeUserClip(raw: RawUserClipItem): UserClipItem {
  return {
    ...raw,
    output_path: extractPlayableUrl(raw.output_path)
  };
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

  async uploadAudio(file: File, token?: string | null) {
    const formData = new FormData();
    formData.append("file", file);

    const hasToken = Boolean(token && token.trim().length > 0);
    if (!hasToken) {
      throw new VideoApiError("Necesitas iniciar sesion para subir audios.", 401);
    }

    const response = await fetch(`${apiBaseUrl}/api/v1/audios/audio`, {
      method: "POST",
      body: formData,
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<AudioUploadResponse>(response);
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

  async createVideoFromJob(jobId: string, token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/videos/from-job/${jobId}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<VideoFromJobResponse>(response);
  },

  async getYoutubeStatus(token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/youtube/status`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<YoutubeConnectionStatus>(response);
  },

  async publishToYoutube(jobId: string, token: string, payload: YoutubePublishRequest) {
    const response = await fetch(`${apiBaseUrl}/api/v1/youtube/publish/${jobId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    return parseResponse<YoutubePublishResponse>(response);
  },

  async suggestYoutubeMetadata(jobId: string, token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/youtube/metadata/${jobId}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<YoutubeMetadataSuggestionResponse>(response);
  },

  async createAutoReframeJobs(
    videoId: string,
    token: string,
    options?: {
      clipsCount?: number;
      clipDurationSec?: number;
      outputStyle?: "vertical" | "speaker_split";
      contentProfile?: "auto" | "interview" | "sports" | "music";
      subtitles?: boolean;
      watermark?: string;
    }
  ) {
    const watermark = options?.watermark?.trim();
    const body: Record<string, unknown> = {
      clips_count: options?.clipsCount ?? 3,
      clip_duration_sec: options?.clipDurationSec ?? 15,
      output_style: options?.outputStyle ?? "vertical",
      content_profile: options?.contentProfile ?? "auto",
      subtitles: options?.subtitles ?? false,
      watermark: watermark && watermark.length > 0 ? watermark : "Hacelo Corto"
    };

    const auto2Response = await fetch(`${apiBaseUrl}/api/v1/jobs/reframe/${videoId}/auto2`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(body)
    });

    if (auto2Response.ok) {
      const payload = await parseResponse<AutoReframeResponse | AutoReframeResponseV2>(auto2Response);

      if ("jobs" in payload) {
        return payload;
      }

      return {
        video_id: videoId,
        total_jobs: payload.total_jobs ?? 0,
        clip_duration_sec: options?.clipDurationSec ?? 15,
        used_video_duration_sec: null,
        jobs: [],
        orchestrator_job_id: payload.job_id
      };
    }

    return parseResponse<AutoReframeResponse>(auto2Response);
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

  async addAudioToVideo(videoId: string, token: string, payload: AddAudioJobRequest) {
    const response = await fetch(`${apiBaseUrl}/api/v1/jobs/add-audio/${videoId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    return parseResponse<AddAudioJobResponse>(response);
  },

  async getJobStatus(jobId: string, token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/jobs/status/${jobId}`, {
      method: "GET",
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    const payload = await parseResponse<RawJobStatusResponse>(response);
    return {
      ...payload,
      output_path: extractPlayableUrl(payload.output_path),
      subtitles_path: extractSubtitlesUrl(payload.output_path),
      child_jobs: extractChildJobIds(payload.output_path)
    } satisfies JobStatusResponse;
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
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    const payload = await parseResponse<RawUserClipsResponse>(response);
    return {
      ...payload,
      clips: payload.clips.map(normalizeUserClip)
    } satisfies UserClipsResponse;
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

    const payload = await parseResponse<RawUserClipDetailResponse>(response);
    return {
      clip: normalizeUserClip(payload.clip)
    } satisfies UserClipDetailResponse;
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
  },

  async getMyAudios(token: string, options?: { limit?: number; offset?: number; query?: string }) {
    const params = new URLSearchParams({
      limit: String(options?.limit ?? 20),
      offset: String(options?.offset ?? 0)
    });

    const query = options?.query?.trim();
    if (query) {
      params.set("q", query);
    }

    const response = await fetch(`${apiBaseUrl}/api/v1/audios/my-audios?${params.toString()}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<UserAudiosResponse>(response);
  },

  async getAudioUrl(audioId: string, token: string, expiresInSeconds = 3600) {
    const params = new URLSearchParams({
      expires_in: String(expiresInSeconds)
    });

    const response = await fetch(`${apiBaseUrl}/api/v1/audios/${audioId}/url?${params.toString()}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<AudioUrlResponse>(response);
  },

  async deleteMyAudio(audioId: string, token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/audios/${audioId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<null>(response);
  }
};
