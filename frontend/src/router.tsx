import { createBrowserRouter } from "react-router-dom";
import App from "./App";
import { LandingPage } from "./pages/LandingPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { AuthLayout } from "./layouts/AuthLayout";
import { Login } from "./pages/auth/Login";
import { Registro } from "./pages/auth/Registro";

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
    ],
  },
  {
    path:"/auth",
    element:<AuthLayout/>,
    children:[
      {
        path: "login",
        element:<Login/>
      },
      {
        path:"registro",
        element:<Registro/>
      }
    ]
  }
]);
