import { createBrowserRouter } from "react-router";
import App from "./App";
import { AppHomePage } from "./pages/AppHomePage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ProtectedRoute, PublicOnlyRoute } from "./router/RouteGuards";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    errorElement: <NotFoundPage />,
    children: [
      {
        index: true,
        element: <LandingPage />,
      },
      {
        path: "auth",
        element: <PublicOnlyRoute />,
        children: [
          {
            path: "login",
            element: <LoginPage />,
          },
          {
            path: "register",
            element: <RegisterPage />,
          },
        ],
      },
      {
        path: "app",
        element: <ProtectedRoute />,
        children: [
          {
            index: true,
            element: <AppHomePage />,
          },
        ],
      },
    ],
  },
]);
