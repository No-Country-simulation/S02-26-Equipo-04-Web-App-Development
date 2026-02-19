import { Button } from "@/src/components/ui/Button";

type DownloadVideoActionsProps = {
  videoId: string | null;
  isUploading: boolean;
  isResolvingDownloadUrl: boolean;
  downloadUrl: string | null;
  onResolveDownloadUrl: () => Promise<void>;
};

export function DownloadVideoActions({
  videoId,
  isUploading,
  isResolvingDownloadUrl,
  downloadUrl,
  onResolveDownloadUrl
}: DownloadVideoActionsProps) {
  return (
    <div className="mt-4 flex flex-wrap items-center gap-2">
      <Button
        variant="neutral"
        className="h-10 w-auto px-4"
        onClick={() => {
          void onResolveDownloadUrl();
        }}
        disabled={!videoId || isResolvingDownloadUrl || isUploading}
      >
        {isResolvingDownloadUrl ? "Generando URL..." : "Obtener URL de descarga"}
      </Button>

      {downloadUrl ? (
        <a
          href={downloadUrl}
          target="_blank"
          rel="noreferrer"
          className="inline-flex rounded-lg border border-neon-mint/40 bg-neon-mint/15 px-3 py-2 text-sm font-semibold text-neon-mint transition hover:bg-neon-mint/25"
        >
          Descargar video subido
        </a>
      ) : null}
    </div>
  );
}
