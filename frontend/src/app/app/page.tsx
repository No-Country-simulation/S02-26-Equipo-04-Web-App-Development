"use client";

import { GeneratedClipsSection, type Clip } from "@/src/components/home/GeneratedClipsSection";
import { ProjectStatusPanel } from "@/src/components/home/ProjectStatusPanel";
import { UploadDropzone } from "@/src/components/home/UploadDropzone";
import { VideoPreview } from "@/src/components/home/videoPrevewTimeLine/VideoPreview";
import { VideoSettings } from "@/src/components/home/VideoSettings";
import { Panel } from "@/src/components/ui/Panel";
import { Duracion, VideoApiError, VideoReframeResponse, type VideoUploadResponse, videoApi } from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { useEffect, useMemo, useState } from "react";

const mockClips: Clip[] = [
  { id: "clip-1", title: "Hook inicial", duration: "00:31", preset: "Impact", status: "LISTO" },
  { id: "clip-2", title: "Momento clave", duration: "00:24", preset: "Story", status: "RUNNING" },
  { id: "clip-3", title: "CTA final", duration: "00:18", preset: "Fast Cut", status: "PENDING" }
];
// const duracion: Duracion = { 
//   start_sec: ,
//   end_sec: 
// }
function normalizeVideoError(error: unknown, fallbackMessage: string) {
  if (error instanceof VideoApiError) {
    if (error.status === 400) {
      return "El archivo de video es invalido o no cumple los requisitos.";
    }

    if (error.status === 401) {
      return "Tu sesion expiro. Vuelve a iniciar sesion para continuar.";
    }

    return error.message;
  }

  if (error instanceof Error) {
    const normalizedMessage = error.message.toLowerCase();
    if (normalizedMessage.includes("failed to fetch") || normalizedMessage.includes("networkerror")) {
      return "No pudimos conectar con el servidor. Intenta de nuevo en unos segundos.";
    }

    return error.message;
  }

  return fallbackMessage;
}


export default function AppHomePage() {
  const token = useAuthStore((state) => state.token);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedVideo, setUploadedVideo] = useState<VideoUploadResponse | null>(null);
  // const [videoProcesador, setVideoProcesado]  = useState<VideoReframeResponse | null>(null);
  const [job, setJob] = useState<string | null>(null)
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [duracion, setDuracion] = useState<Duracion | null> (null)
  console.log(duracion)
  const hasVideo = Boolean(uploadedVideo);
  const visibleClips = useMemo(() => (hasVideo && !isUploading ? mockClips : []), [hasVideo, isUploading]);

  useEffect(() => {
    return () => {
      if (videoPreviewUrl) {
        URL.revokeObjectURL(videoPreviewUrl);
      }
    };
  }, [videoPreviewUrl]);

  const handleUpload = async (file: File) => {
    const localPreviewUrl = URL.createObjectURL(file);

    setIsUploading(true);
    setUploadedVideo(null);
    setUploadError(null);

    try {
      const uploaded = await videoApi.upload(file, token);
      setUploadedVideo(uploaded);
      setVideoPreviewUrl((prev) => {
        if (prev) {
          URL.revokeObjectURL(prev);
        }
        return localPreviewUrl;
      });
    } catch (error) {
      URL.revokeObjectURL(localPreviewUrl);
      setVideoPreviewUrl(null);
      setUploadError(normalizeVideoError(error, "No pudimos subir el video."));
    } finally {
      setIsUploading(false);
    }
  };

  // generar Video 
const jobVideo = async (idJob:string)=> {
  while(true){
    const response = await videoApi.getStatusVideo(idJob, token);
    
    setJob(response.status)

    if (response.status === "COMPLETED") return;
     if (response.status === "FAILED") throw new Error("Job failed");
    await new Promise((r) => setTimeout(r, 2000));
  }

}
  const handleProcessVideo = async()=>{

    try {
      const response =await videoApi.processVideo(uploadedVideo?.video_id , duracion?.start_sec , duracion?.end_sec, token)
      // setVideoProcesado(response);
      console.log(response);
    jobVideo(response.job_id)
      
    } catch (error) {
      setUploadError(normalizeVideoError(error, "No pudimos generar el Video"));
    }
  }

  const showPreview = Boolean(videoPreviewUrl && hasVideo && !isUploading);
  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid gap-5 xl:grid-cols-[1.55fr_0.95fr]">
        <Panel variant="accent" className="p-4 sm:p-5">
          <UploadDropzone
            onUpload={handleUpload}
            isUploading={isUploading}
            fileName={uploadedVideo?.filename}
          />
        </Panel>

        <Panel>
          <ProjectStatusPanel
            hasVideo={hasVideo}
            isUploading={isUploading}
            uploadError={uploadError}
            videoId={uploadedVideo?.video_id ?? null}
            videoPreviewUrl={videoPreviewUrl}
          />
        </Panel>
      </div>
      {showPreview &&(<div className="flex flex-col lg:flex-row gap-5 mt-5">
        <Panel >
          <VideoPreview videoPreviewUrl={videoPreviewUrl}
          onTrimChange={(start, end) => {
            setDuracion({start_sec:Math.round(start), end_sec: Math.round(end)})
        // console.log("Enviar al backend:", { start, end });
      }}
          />
        </Panel>
        <Panel>
          <VideoSettings onProcessVideo={handleProcessVideo}/>
        </Panel>

      </div>)}
      
      <Panel className="mt-5">
        <GeneratedClipsSection job={job} clips={visibleClips} showLoading={isUploading} />
      </Panel>
    </section>
  );
}
