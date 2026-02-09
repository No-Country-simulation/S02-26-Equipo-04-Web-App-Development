import redis
import json
import os
import subprocess
import cv2
import time

import ffmpeg
import librosa
import numpy as np

def check_ffmpeg():
    """
    Verifica que FFmpeg esté instalado en el contenedor
    y accesible desde el PATH del sistema.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.split("\n")[0]
    except Exception as e:
        return f"FFmpeg error: {e}"


def check_opencv():
    """
    Verifica que OpenCV esté correctamente instalado
    e importable desde Python.
    """
    try:
        return f"OpenCV version {cv2.__version__}"
    except Exception as e:
        return f"OpenCV error: {e}"


def check_redis():
    """
    Verifica conexión con Redis usando la variable de entorno REDIS_HOST.
    """
    try:
        r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)
        r.ping()
        return "Redis connected"
    except Exception as e:
        return f"Redis error: {e}"


def check_dependencies():
    """
    Ejecuta todos los chequeos de entorno al iniciar el worker.
    Sirve para validar que el contenedor está correctamente armado.
    """
    status = {
    "redis": check_redis(),
    "opencv": check_opencv(),
    "ffmpeg": check_ffmpeg()
    }
    
    print("🔎 Environment check:")
    for k, v in status.items():
        print(f"{k}: {v}")

def publish_event(r, event_type, extra_data=None):
    """
    Publica un evento al canal 'video_events' para que la API lo reciba.

    :param r: cliente Redis
    :param event_type: tipo de evento (string)
    :param extra_data: diccionario opcional con más datos
    """
    event = {"event": event_type}
    if extra_data:
        event.update(extra_data)

    r.publish("video_events", json.dumps(event))
    print(f"📤 Evento enviado: {event}", flush=True)




def redis_listener():
    """
    Conecta a Redis y queda escuchando el canal 'video_jobs'
    donde la API enviará trabajos de procesamiento de video.

    Este worker NO actualiza la base de datos.
    Solo procesa y luego notifica eventos.
    """

    print("🔌 Connecting to Redis...", flush=True)
    r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)

    # --- Enviar solo 2 mensajes de estado ---
    publish_event(r, "WORKER_STARTED")
    time.sleep(1)
    publish_event(r, "WORKER_READY")

    # --- Escuchar trabajos ---
    pubsub = r.pubsub()
    pubsub.subscribe("video_jobs")

    print("🎧 Worker listening for video jobs...", flush=True)

    for message in pubsub.listen():
        
        if message["type"] == "message":
            try:
                job = json.loads(message["data"])
                print(f"🎬 Job recibido: {job}", flush=True)

                # 👉 Aquí irá luego el procesamiento real de video
                
                # Simular fin de procesamiento
                time.sleep(2)

                publish_event(r, "VIDEO_PROCESSED", {"job_id": job.get("job_id")})

            except Exception as e:
                print(f"⚠️ Error procesando job: {e}", flush=True)



FPS = 30
TARGET_W, TARGET_H = 1080, 1920
AUDIO_FILE = "audio.wav"# aca hay que indicar en donde se va a guardar el audio
FRAME_IN = "frames_in"# aca se especifica el nombre del archivo para guardar los frames del video 
FRAME_OUT = "frames_out"# aca se especifica el nombre del archivo para guardar los frames modificados 
OUTPUT_VIDEO = "output_9_16.mp4" # aca hay que indicar en donde se va a guardar el video


def procesarVideo(ubicacionVideo,  inicio, fin):
    
    
    # Pipeline principal:
    # 1. Extrae audio y detecta voz
    # 2. Extrae frames del video
    # 3. Detecta quién está hablando por frame
    # 4. Reencuadra el video a 9:16
    # 5. Reconstruye el video final con audio
    


    os.makedirs(FRAME_IN, exist_ok=True) #esto genera un archivo para alamacenar los frames del video crudo 
    os.makedirs(FRAME_OUT, exist_ok=True) #esto genera un archivo para alamacenar los frames ya recortados

    voice_mask = extraerAudio(ubicacionVideo, inicio, fin)
    frames = extraerFrames(ubicacionVideo, inicio, fin)    
    speaker_x = detectar_hablante(frames, voice_mask)
    reencuadre(frames, speaker_x)
    generarVideoFinal(ubicacionVideo,inicio,fin)



def generarVideoFinal(video_original, inicio, fin):
    
    #  Une los frames reencuadrados con el audio original
    # y genera el video final 9:16.

    

    video = ffmpeg.input(FRAME_OUT+"/%06d.png", framerate=FPS)
    audio = ffmpeg.input(video_original, ss=inicio, to=fin).audio

    (
        ffmpeg
        .output(
            video,
            audio,
            OUTPUT_VIDEO,
            vcodec="libx264",
            pix_fmt="yuv420p",
            movflags="+faststart"
        )
        .run(overwrite_output=True)
    )
    print("🎉 VIDEO FINAL GENERADO:", OUTPUT_VIDEO)

def detectar_hablante(frames, voice_mask):
    # Detecta el hablante estimado por frame usando:
    # - Detección de rostros (Haar Cascade)
    # - Variación en la zona de la boca (proxy de habla)
    # - Voice mask del audio para validar frames hablados
    proto = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(proto)

    speaker_x = {}


    for idx, fname in enumerate(frames):
        img = cv2.imread(f"{FRAME_IN}/{fname}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        best_motion = 0
        best_x = speaker_x.get(idx-1, w // 2)
        frame_area = w * h
        MIN_FACE_AREA = 0.03   # 3% del frame
        MAX_FACE_AREA = 0.40   # 40% del frame
        
        for (x, y, fw, fh) in faces:
            if fw > w * 0.6:
                continue
            if y > h * 0.5:
                continue
            area = fw * fh
            ratio = area / frame_area

            if ratio < MIN_FACE_AREA or ratio > MAX_FACE_AREA:
                continue
            mouth_y1 = int(y + fh * 0.6)
            mouth_y2 = int(y + fh * 0.85)
            mouth = gray[mouth_y1:mouth_y2, x:x+fw]

            motion = np.var(mouth)

            if motion > best_motion:
                best_motion = motion
                best_x = x + fw // 2

        if idx < len(voice_mask) and voice_mask[idx]:
            speaker_x[idx] = best_x
        else:
            speaker_x[idx] = speaker_x.get(idx-1, best_x)

    print("✅ Hablante estimado por frame")
    return speaker_x


def reencuadre(frames, speaker_x):
    
    
    # Reencuadra el video a 9:16 siguiendo al hablante.
    # Usa cortes duros en lugar de transiciones suaves para evitar glitches.


    for idx, fname in enumerate(frames):
        img = cv2.imread(f"{FRAME_IN}/{fname}")
        h, w, _ = img.shape

        x = speaker_x.get(idx, w // 2)

        CUT_THRESHOLD = int(w * 0.15)   # 15% del ancho
        HOLD_FRAMES = 8                 # frames mínimos antes de otro corte

        last_x = None
        last_cut_frame = -HOLD_FRAMES

        if last_x is None:
            smooth_x = x
            last_x = x
        else:
            if abs(x - last_x) > CUT_THRESHOLD and (idx - last_cut_frame) > HOLD_FRAMES:
                # CORTE
                smooth_x = x
                last_x = x
                last_cut_frame = idx
            else:
                # mantener encuadre
                smooth_x = last_x

        crop_w = int(h * 9 / 16)
        x1 = max(0, min(w - crop_w, smooth_x - crop_w // 2))
        x2 = x1 + crop_w

        crop = img[:, x1:x2]
        out = cv2.resize(crop, (TARGET_W, TARGET_H))

        cv2.imwrite(f"{FRAME_OUT}/{fname}", out)

    print("✅ Reencuadre completado")


def extraerAudio(ubicacionVideo, inicio, fin):
#    Extrae el audio del video y detecta en qué frames hay voz
#     usando energía RMS.
    

    (
        ffmpeg
        .input(ubicacionVideo, ss=inicio, to=fin)
        .output(AUDIO_FILE, ac=1, ar=16000)
        .run(overwrite_output=True)
    )

    print("✅ Audio extraído")

    # =========================
    # 2️⃣ ANALIZAR AUDIO (VOZ)
    # =========================


    y, sr = librosa.load(AUDIO_FILE, sr=16000)

    hop_length = int(sr / FPS)
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    voice_mask = rms > np.percentile(rms, 65)

    print("✅ Voz detectada en audio")
    return voice_mask

def extraerFrames(ubicacionVideo, inicio, fin):
        # Extrae frames del video respetando el FPS configurado.

    (
    ffmpeg
    .input(ubicacionVideo, ss=inicio, to=fin) 
    .output(f"{FRAME_IN}/%06d.png", vf=f"fps={FPS}")
    .run(overwrite_output=True)
    )

    frames = sorted(os.listdir(FRAME_IN))
    print("✅ Frames extraídos")
    return frames



if __name__ == "__main__":
    print("\n--------------")
    print(" VIDEO WORKER")
    print("--------------")
    print("\n🚀 VIDEO WORKER STARTING...\n", flush=True)

    check_dependencies()
    redis_listener()