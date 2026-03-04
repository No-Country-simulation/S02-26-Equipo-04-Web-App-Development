import { ImageResponse } from "next/og";

export const size = {
  width: 1200,
  height: 630
};

export const contentType = "image/png";

export default function TwitterImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: "20px",
          padding: "64px",
          background:
            "radial-gradient(circle at 80% 15%, rgba(136,57,239,0.24), transparent 35%), linear-gradient(160deg, #eff1f5 0%, #e6e9ef 100%)",
          color: "#4c4f69",
          fontFamily: "Segoe UI"
        }}
      >
        <div style={{ fontSize: 28, fontWeight: 600, color: "#1e66f5" }}>Hacelo Corto</div>
        <div style={{ fontSize: 72, fontWeight: 700, lineHeight: 1.05, maxWidth: "960px" }}>
          Crea shorts desde videos largos en minutos
        </div>
        <div style={{ fontSize: 34, color: "#5c5f77", maxWidth: "860px" }}>
          Flujo completo: upload, timeline, audio y exportacion.
        </div>
      </div>
    ),
    {
      ...size
    }
  );
}
