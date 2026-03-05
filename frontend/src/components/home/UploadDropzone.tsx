"use client";

import { Button } from "@/src/components/ui/Button";
import { Loader } from "@/src/components/ui/Loader";
import { AudioLines, CloudUpload, Film } from "lucide-react";
import { useLocale } from "next-intl";
import { useRef, useState } from "react";

type UploadDropzoneProps = {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
  fileName?: string;
  fileKind?: "video" | "audio";
};

export function UploadDropzone({ onUpload, isUploading, fileName, fileKind = "video" }: UploadDropzoneProps) {
  const isEn = useLocale() === "en";
  const tr = (es: string, en: string) => (isEn ? en : es);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const processFile = async (file: File | null) => {
    if (!file || isUploading) return;
    await onUpload(file);
  };

  const borderClass = isDragging
    ? "border-neon-cyan bg-neon-cyan/10 shadow-glow"
    : "border-white/20 bg-gradient-to-b from-night-900/80 to-night-800/45 hover:border-neon-cyan/35";

  return (
    <div
      onDrop={(event) => {
        event.preventDefault();
        setIsDragging(false);
        const file = event.dataTransfer.files?.[0] ?? null;
        void processFile(file);
      }}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      className={[
        "flex min-h-[18rem] flex-col items-center justify-center rounded-2xl border border-dashed px-5 py-8 text-center transition sm:min-h-[21rem]",
        borderClass
      ].join(" ")}
    >
        <input
          ref={inputRef}
          type="file"
          accept="video/*,audio/*"
          className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0] ?? null;
          void processFile(file);
          event.target.value = "";
        }}
      />

      <div className="mb-4 grid h-14 w-14 place-items-center rounded-2xl border border-neon-cyan/50 bg-neon-cyan/10 text-neon-cyan">
        {fileKind === "audio" ? <AudioLines size={18} /> : <Film size={18} />}
      </div>

      <p className="text-xs uppercase tracking-[0.22em] text-neon-cyan/80">{tr("carga de media", "media upload")}</p>
      <h2 className="mt-2 font-display text-2xl text-white sm:text-3xl">{tr("Arrastra tu video o audio, o subilo con un click", "Drag your video or audio, or upload with one click")}</h2>
      <p className="mt-2 max-w-xl text-sm text-white/70">{tr("Soporta videos y audios. Recomendado para clips: mp4 horizontal 16:9.", "Supports videos and audios. Recommended for clips: horizontal 16:9 mp4.")}</p>

      <Button
        className="mt-6 w-auto min-w-52"
        onClick={() => inputRef.current?.click()}
        disabled={isUploading}
      >
        <CloudUpload size={16} />
        {isUploading ? tr("Subiendo...", "Uploading...") : tr("Seleccionar archivo", "Select file")}
      </Button>

      {isUploading ? <Loader className="mt-4" label={tr("Procesando archivo...", "Processing file...")} /> : null}
      {!isUploading && fileName ? (
        <p className="mt-4 text-sm text-neon-mint">
          {tr("Archivo cargado", "Uploaded file")} ({fileKind === "audio" ? tr("audio", "audio") : tr("video", "video")}): {fileName}
        </p>
      ) : null}
    </div>
  );
}
