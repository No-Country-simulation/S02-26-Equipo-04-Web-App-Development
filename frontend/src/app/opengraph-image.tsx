import { ImageResponse } from "next/og";

export const size = {
  width: 1200,
  height: 630
};

export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "56px",
          background:
            "radial-gradient(circle at 15% 20%, rgba(4,165,229,0.35), transparent 35%), radial-gradient(circle at 85% 15%, rgba(234,118,203,0.3), transparent 32%), linear-gradient(135deg, #eff1f5 0%, #dce0e8 100%)",
          color: "#4c4f69",
          fontFamily: "Segoe UI"
        }}
      >
        <div
          style={{
            border: "1px solid rgba(76,79,105,0.22)",
            borderRadius: "999px",
            padding: "10px 18px",
            fontSize: 24,
            fontWeight: 600
          }}
        >
          Hacelo Corto
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "18px", maxWidth: "920px" }}>
          <div style={{ fontSize: 70, fontWeight: 700, lineHeight: 1.05 }}>
            Convierte videos largos en shorts listos para publicar
          </div>
          <div style={{ fontSize: 34, color: "#5c5f77", lineHeight: 1.25 }}>
            Upload, recorte en timeline, audio editor, biblioteca y exportacion en una sola app web.
          </div>
        </div>
      </div>
    ),
    {
      ...size
    }
  );
}
