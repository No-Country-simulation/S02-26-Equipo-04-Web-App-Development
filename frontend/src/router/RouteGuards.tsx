import { Navigate, Outlet } from "react-router";
import { useAuthStore } from "../store/useAuthStore";
import { getProtectedRedirect, getPublicOnlyRedirect } from "./redirects";

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const redirect = getProtectedRedirect(isAuthenticated);

  if (redirect) {
    return <Navigate to={redirect} replace />;
  }

  return <Outlet />;
}

export function PublicOnlyRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const redirect = getPublicOnlyRedirect(isAuthenticated);

  if (redirect) {
    return <Navigate to={redirect} replace />;
  }

  return <Outlet />;
}
