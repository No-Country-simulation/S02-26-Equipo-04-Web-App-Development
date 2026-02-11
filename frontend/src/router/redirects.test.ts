import { describe, expect, it } from "vitest";
import { getProtectedRedirect, getPublicOnlyRedirect } from "./redirects";

describe("route redirects", () => {
  it("envia a login cuando intenta entrar a ruta protegida sin sesion", () => {
    expect(getProtectedRedirect(false)).toBe("/auth/login");
  });

  it("permite ruta protegida cuando ya hay sesion", () => {
    expect(getProtectedRedirect(true)).toBeNull();
  });

  it("permite rutas publicas cuando no hay sesion", () => {
    expect(getPublicOnlyRedirect(false)).toBeNull();
  });

  it("redirige a app si el usuario autenticado intenta entrar a auth", () => {
    expect(getPublicOnlyRedirect(true)).toBe("/app");
  });
});
