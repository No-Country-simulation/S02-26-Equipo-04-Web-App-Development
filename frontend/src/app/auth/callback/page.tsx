import { Suspense } from "react";
import { GoogleCallbackClient } from "./GoogleCallbackClient";

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={null}>
      <GoogleCallbackClient />
    </Suspense>
  );
}
