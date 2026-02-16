import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthApiError } from "@/src/services/authApi";
import { useAuthStore } from "./useAuthStore";
import { authApi } from "@/src/services/authApi";

vi.mock("@/src/services/authApi", () => ({
  AuthApiError: class extends Error {
    status: number;

    constructor(message: string, status: number) {
      super(message);
      this.name = "AuthApiError";
      this.status = status;
    }
  },
  authApi: {
    register: vi.fn(),
    login: vi.fn(),
    me: vi.fn(),
    refresh: vi.fn(),
    logout: vi.fn()
  }
}));

const mockedAuthApi = vi.mocked(authApi);

describe("useAuthStore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      isBootstrapped: false,
      error: null
    });
  });

  it("login stores token and authenticates user", async () => {
    mockedAuthApi.login.mockResolvedValue({
      access_token: "token-ok",
      token_type: "bearer",
      expires_in: 3600
    });
    mockedAuthApi.me.mockResolvedValue({ id: 1, email: "dev@team.com", role: "user" });

    const didLogin = await useAuthStore.getState().login("dev@team.com", "secret");

    expect(didLogin).toBe(true);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAuthStore.getState().user?.email).toBe("dev@team.com");
    expect(window.localStorage.getItem("auth_token")).toBe("token-ok");
  });

  it("register authenticates and stores session", async () => {
    mockedAuthApi.register.mockResolvedValue({
      access_token: "register-token",
      token_type: "bearer",
      expires_in: 3600
    });
    mockedAuthApi.me.mockResolvedValue({ id: 2, email: "new@team.com", role: "user" });

    const didRegister = await useAuthStore.getState().register("new@team.com", "secret");

    expect(didRegister).toBe(true);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(window.localStorage.getItem("auth_token")).toBe("register-token");
  });

  it("bootstrap clears invalid token", async () => {
    window.localStorage.setItem("auth_token", "bad-token");
    mockedAuthApi.me.mockRejectedValue(new AuthApiError("invalid token", 401));

    await useAuthStore.getState().bootstrapSession();

    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().isBootstrapped).toBe(true);
    expect(window.localStorage.getItem("auth_token")).toBeNull();
  });

  it("logout clears local session and calls endpoint", async () => {
    window.localStorage.setItem("auth_token", "token-ok");
    useAuthStore.setState({
      token: "token-ok",
      user: { id: 3, email: "dev@team.com", role: "user" },
      isAuthenticated: true,
      isBootstrapped: true
    });

    await useAuthStore.getState().logout();

    expect(mockedAuthApi.logout).toHaveBeenCalledWith("token-ok");
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(window.localStorage.getItem("auth_token")).toBeNull();
  });
});
