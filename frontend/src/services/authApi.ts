import { env } from "@/src/config/env";

export type AuthTokens = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type AuthUser = {
  id: number | string;
  email: string;
  role?: string;
};

type LoginPayload = {
  email: string;
  password: string;
};

type RegisterPayload = {
  email: string;
  password: string;
};

type GoogleCallbackPayload = {
  code: string;
  state: string;
};

export type GoogleAuthUrlPayload = {
  authorization_url: string;
  state: string;
};

const apiBaseUrl = env.apiBaseUrl.replace(/\/$/, "");

export class AuthApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "AuthApiError";
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
    throw new AuthApiError(apiMessage ?? fallbackMessage, response.status);
  }

  return payload as T;
}

export const authApi = {
  async register(payload: RegisterPayload) {
    const response = await fetch(`${apiBaseUrl}/api/v1/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    return parseResponse<AuthTokens>(response);
  },

  async login(payload: LoginPayload) {
    const body = new URLSearchParams({
      username: payload.email,
      password: payload.password
    });

    const response = await fetch(`${apiBaseUrl}/api/v1/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: body.toString()
    });

    return parseResponse<AuthTokens>(response);
  },

  async me(token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/auth/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<AuthUser>(response);
  },

  async refresh(token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/auth/refresh`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<AuthTokens>(response);
  },

  async logout(token: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/auth/logout`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return parseResponse<void>(response);
  },

  async getGoogleAuthUrl() {
    const response = await fetch(`${apiBaseUrl}/api/v1/auth/google/login`, {
      method: "GET"
    });

    return parseResponse<GoogleAuthUrlPayload>(response);
  },

  async googleCallback(payload: GoogleCallbackPayload) {
    const response = await fetch(`${apiBaseUrl}/api/v1/auth/google/callback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    return parseResponse<AuthTokens>(response);
  }
};
