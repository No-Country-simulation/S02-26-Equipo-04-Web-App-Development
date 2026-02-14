import os
import cv2
import math
import ffmpeg
import librosa
import subprocess
import numpy as np
from pathlib import Path

"""
============================
    pipeline.py
============================

🧠 ARQUITECTURA:

stream_processing()
 ├─ setup_output()
 ├─ get_video_metadata()
 ├─ init_stream_decoder()
 ├─ init_stream_encoder()
 ├─ analyze_speech_activity()
 ├─ process_frames_loop()
 │     ├─ read_frame()
 │     ├─ select_active_subject()
 │     ├─ get_camera_position()
 │     ├─ reframe_to_vertical()
 │     └─ write_frame()
 └─ close_streams()

 
========================================================================
TODO
(!)Posibilidad de realizar el analisis sobre el video de baja resolucion para
previsualizar en el front y ofrecer micro ajustes y sus resultados ??
(!)Crear una clase de config ??
========================================================================
"""

DEBUG = True

# output routes and dirs
OUTPUT_DIR = Path("output")
NORMALIZED_VIDEO = OUTPUT_DIR / "normalized"
PROCESSED_VIDEO = OUTPUT_DIR / "processed"
RESULT_VIDEO = OUTPUT_DIR / "result"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
NORMALIZED_VIDEO.mkdir(exist_ok=True)
PROCESSED_VIDEO.mkdir(exist_ok=True)
RESULT_VIDEO.mkdir(exist_ok=True)


# face tracking
EDGE_MARGIN_RATIO = 0.10
SUBJECT_LOST_TIMEOUT_SEC = 2.0
MIN_FACE_RATIO = 0.003  # 0.3% shows / escenario
#MIN_FACE_RATIO = 0.0015 # si la cámara está lejos:
#MIN_FACE_RATIO = 0.01 # si está cerca


# camera direction parameters
SWITCH_DISTANCE_RATIO = 0.25
CANDIDATE_CONFIRMATION_SEC = 0.5
NO_FACE_HOLD_SEC = 1.0
SMOOTHING_FACTOR = 0.15
MIN_HOLD_SEC = 0.8


# audio analysis parameters
AUDIO_SAMPLE_RATE = 16000
SPEECH_PERCENTILE = 65

# output params
TARGET_MAX_W = 1280
TARGET_FPS = 30
OUTPUT_ASPECT = 9 / 16

# loads and validates an OpenCV Haar Cascade classifier for face detection.
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
if face_cascade.empty():
    raise RuntimeError("Failed to load face cascade classifier")
#========================================================================   


class CameraDirector:
    """
    Cinematic camera direction logic for automated reframing.

    This class acts as the "brain" of the virtual camera. It converts noisy
    detection data (faces, speaker position, motion) into stable, human-like
    camera behavior.

    The director enforces cinematic rules to avoid jitter and unnatural motion.

    Core behaviors implemented
    --------------------------
    • Minimum hold time before camera can move
    • Consensus-based subject switching (prevents false jumps)
    • Smooth transitions with bounded duration
    • Intelligent hard cuts for strong speaker changes
    • Fusion of audio (speech) and visual detection
    • Anti ping-pong logic (prevents rapid back-and-forth)

    Camera States
    -------------
    HOLD        : Camera remains stable
    TRANSITION  : Camera smoothly moves toward a new framing target

    Parameters
    ----------
    frame_width : int
        Width of the input video frame. Used to scale movement thresholds.
    fps : float
        Frame rate of the video. Used to convert timing rules into frame counts.

    Notes
    -----
    This class does NOT:
    - detect faces
    - analyze audio
    - crop frames

    It ONLY decides *where the camera should point*.
    """
    def __init__(self, frame_width, final_w, fps):
        self.w = frame_width
        self.crop_w = final_w
        self.fps = fps

        self.current_x = frame_width // 2
        self.target_x = None
        self.mode = "HOLD"

        self.frames_in_state = 0
        self.hold_frames = 0

        self.possible_target = None
        self.possible_counter = 0

        # Parámetros
        self.MOVE_THRESHOLD = int(frame_width * 0.18)
        self.HARD_CUT_THRESHOLD = int(frame_width * 0.35)

        self.HOLD_MIN = int(fps * 0.5)
        self.CONSENSUS = int(fps * 0.25)

        self.TRANSITION_MIN = int(fps * 0.3)
        self.TRANSITION_MAX = int(fps * 0.6)

        # Historical
        self.last_detected_x = None
        self.detected_persistence = 0
        self.MIN_DETECTED_PERSISTENCE = int(self.fps * 0.4)

    def update(self, detected_x, is_voice):
        """
        Updates camera position based on subject detection and speech activity.

        Decision flow
        -------------
        1. Hard cut if:
           - Voice is active
           - Subject jump is very large

        2. Build consensus if subject is drifting away:
           - Candidate must persist for several frames

        3. HOLD state:
           - Enforces minimum time before moving
           - Switches to TRANSITION if consensus is reached

        4. TRANSITION state:
           - Smoothly interpolates camera position
           - Stops when close enough to target

        Parameters
        ----------
        detected_x : int
            X coordinate of detected subject.
        is_voice : bool
            Whether speech is present in this frame.

        Returns
        -------
        int
            Updated camera X position.
        """
        if detected_x == self.last_detected_x:
            self.detected_persistence += 1
        else:
            self.detected_persistence = 1
            self.last_detected_x = detected_x

        if detected_x is None:
            # No subject detected → hold position
            print(f"\n🔔 NO SUBJECT DETECTED, CURRENT POSITION: {self.current_x}\n")
            return self.current_x
        
        #Eso hace que:
        # espere estabilidad del activo
        # ignore cambios efímeros
        # evite cortes nerviosos
        if self.detected_persistence < self.MIN_DETECTED_PERSISTENCE:
            return self.current_x
        
        # ================= HARD CUT ================= 
        if is_voice and abs(detected_x - self.current_x) > self.HARD_CUT_THRESHOLD:
            self.current_x = max(
                self.crop_w // 2,
                min(self.w - self.crop_w // 2, detected_x)
            )
            self.mode = "HOLD"
            self.hold_frames = 0
            self.frames_in_state = 0
            return self.current_x

        # ================= SAFE ZONE CHECK =================
        left  = self.current_x - self.crop_w // 2
        right = self.current_x + self.crop_w // 2

        margin = int(self.crop_w * 0.25)

        safe_left  = left + margin
        safe_right = right - margin

        if detected_x < safe_left or detected_x > safe_right:
            # subject outside secure focus zone → builds conscensus
            if self.possible_target is None:
                self.possible_target = detected_x
                self.possible_counter = 1
            else:
                if abs(detected_x - self.possible_target) < self.MOVE_THRESHOLD:
                    self.possible_counter += 1
                else:
                    self.possible_target = detected_x
                    self.possible_counter = 1
        else:
            # subject inside secure focus zone → cancels vars
            self.possible_target = None
            self.possible_counter = 0

        # ================= HOLD =================
        if self.mode == "HOLD":

            self.hold_frames += 1

            if (
                self.possible_counter > self.CONSENSUS and
                self.hold_frames > self.HOLD_MIN
            ):
                self.mode = "TRANSITION"
                self.target_x = self.possible_target
                self.frames_in_state = 0
                self.hold_frames = 0

        # ================= TRANSITION =================
        elif self.mode == "TRANSITION":

            self.frames_in_state += 1

            progress = min(
                1.0,
                self.frames_in_state / self.TRANSITION_MAX
            )

            self.current_x = int(
                self.current_x +
                (self.target_x - self.current_x) * progress
            )

            if (
                self.frames_in_state > self.TRANSITION_MIN and
                abs(self.current_x - self.target_x) < 5
            ):
                self.mode = "HOLD"
                self.current_x = self.target_x
                self.target_x = None
                self.frames_in_state = 0

        return self.current_x
#========================================================================


def get_video_metadata(video_path):
    """
    Extracts basic metadata from a video file.

    Retrieves video stream properties required for:
    - frame decoding
    - camera logic scaling
    - stream-based processing

    Parameters
    ----------
    video_path : str
        Path to the input video file.

    Returns
    -------
    tuple (int, int, float)
        width  : Frame width in pixels
        height : Frame height in pixels
        fps    : Frames per second (float)

    Notes
    -----
    This function does not modify the video.
    It only inspects stream metadata using ffmpeg probe.
    """
    probe = ffmpeg.probe(video_path)
    vstream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    w = int(vstream["width"])
    h = int(vstream["height"])
    num, den = map(int, vstream["r_frame_rate"].split("/"))
    fps = num / den if den != 0 else 0
    return w, h, fps


def init_stream_decoder(video_path):
    """Opens FFmpeg process that streams raw BGR frames."""
    return (
        ffmpeg
        .input(video_path)
        .output('pipe:', format='rawvideo', pix_fmt='bgr24')
        .run_async(pipe_stdout=True)
    )

def init_stream_encoder(output_path, actual_w, actual_h, fps):
    """Opens FFmpeg encoder process receiving raw frames via stdin."""
    return (
        ffmpeg
        .input('pipe:', format='rawvideo', pix_fmt='bgr24',
               s=f"{actual_w}x{actual_h}", framerate=fps)
        .output(
            output_path,
            vcodec='libx264',
            pix_fmt='yuv420p',
            movflags='+faststart'
        )
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )


def normalize_video_segment(video_path, start_sec, end_sec,
                            target_fps=TARGET_FPS,
                            target_max_width=TARGET_MAX_W):
    """
    Cuts and conditionally normalizes a video segment for stable downstream processing.

    The function analyzes the input video stream and only re-encodes if required.
    Normalization is triggered when at least one of the following conditions is met:

    - Video codec is not H.264
    - Frame rate differs significantly from target_fps (±2 fps tolerance)
    - Width exceeds target_max_width (video will be downscaled preserving aspect ratio)
    - Pixel format is not yuv420p (required for broad compatibility)

    If no normalization is needed, the segment is cut using stream copy
    (no re-encoding, lossless and fast).

    This function ensures the video is in a format suitable for:
    face detection, frame-by-frame decoding, and re-encoding.

    Parameters
    ----------
    video_path : str
        Path to input video file.
    start_sec : float
        Segment start time in seconds.
    end_sec : float
        Segment end time in seconds.
    target_fps : int
        Desired output frames per second.
    target_max_width : int
        Maximum allowed video width.

    Returns
    -------
    str
        Path to normalized (or copied) video segment.
    """
    print("\n🎬 VIDEO NORMALIZATION...", flush=True)

    probe = ffmpeg.probe(video_path)
    vstream = next(s for s in probe["streams"] if s["codec_type"] == "video")

    codec = vstream.get("codec_name")
    width = int(vstream["width"])
    height = int(vstream["height"])
    pix_fmt = vstream.get("pix_fmt", "")
    fps_str = vstream["r_frame_rate"]
    num, den = map(int, fps_str.split("/"))
    fps = num / den if den else 0

    print(f"📂 {video_path}")
    print(f"🎞  Codec: {codec}")
    print(f"📐 Resolución: {width}x{height}")
    print(f"🎨 Pixel format: {pix_fmt}")
    print(f"⏱  FPS: {fps:.2f}\n", flush=True)

    needs_codec = codec not in ("h264", "libx264")
    needs_fps = abs(fps - target_fps) > 2
    needs_scale = width > target_max_width
    needs_pixfmt = pix_fmt != "yuv420p"

    output_path = str(NORMALIZED_VIDEO / Path(video_path).name)
    
    if not any([needs_codec, needs_fps, needs_scale, needs_pixfmt]):

        print("\n⚙️  Video is already normalized. Only cutting segment.\n", flush=True)

        (
            ffmpeg
            .input(video_path)
            .output(
                output_path,
                ss=start_sec,
                to=end_sec,
                vcodec="copy",
                acodec="copy",
                map="0",
                avoid_negative_ts="make_zero"
            )
            .overwrite_output()
            .run()
        )
        return output_path

    print("\n⚙️  Normalization needed:\n", flush=True)
    print(f"   Codec ok? {not needs_codec}")
    print(f"   FPS ok? {not needs_fps}")
    print(f"   Resolution ok? {not needs_scale}")
    print(f"   Pixel format ok? {not needs_pixfmt}\n", flush=True)

    stream = ffmpeg.input(video_path, ss=start_sec, to=end_sec)

    if needs_scale:
        stream = stream.filter("scale", target_max_width, -2)

    stream = (
        stream.output(
            output_path,
            vcodec="libx264",
            pix_fmt="yuv420p",
            r=target_fps,
            acodec="aac",
            audio_bitrate="128k",
            preset="fast",
            crf=23,
            movflags="+faststart"
        )
        .overwrite_output()
    )

    print("🚀 Runnig FFmpeg...\n", flush=True)
    ffmpeg.run(stream)

    print(f"✅ VIDEO NORMALIZED: {output_path}\n", flush=True)

    return output_path


def merge_audio_track(processed_video_path,
                      normalized_video_path):
    """
    Merges the original audio track into a processed video file.

    The function:
    - Extracts the audio segment from the normalized_video_path(!)
    - Copies the processed video stream (no re-encoding)
    - Encodes audio to AAC
    - Produces a final output with synchronized streams

    Parameters
    ----------
    processed_video_path : str
        Path to the processed video (without audio).
    original_video_path : str
        Path to the original source video.

    Returns
    -------
    str
        Path to the final video with audio merged.

    Notes
    -----
    - Video stream is copied (vcodec="copy") to preserve quality.
    - Audio is encoded to AAC for compatibility.
    - The output duration matches the shortest stream.
    """
    output_path = str(RESULT_VIDEO / Path(processed_video_path).name)

    video_in = ffmpeg.input(processed_video_path)
    audio_in = ffmpeg.input(normalized_video_path)

    (
        ffmpeg
        .output(
            video_in.video,   # video del archivo procesado
            audio_in.audio,   # audio del original
            output_path,
            vcodec="copy",
            acodec="aac",
            shortest=None
        )
        .overwrite_output()
        .run()
    )
    print("\n🔊 Audio added\n")
    return output_path


def resize_with_letterbox(frame, final_w, final_h):
    h, w = frame.shape[:2]

    scale = min(final_w / w, final_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(frame, (new_w, new_h))

    canvas = np.zeros((final_h, final_w, 3), dtype=np.uint8)

    x_offset = (final_w - new_w) // 2
    y_offset = (final_h - new_h) // 2

    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

    return canvas


def reframe_vertical(frame, camera_x, final_w, final_h):
    """Crops frame to vertical 9:16 region centered on camera_x."""
    h, w = frame.shape[:2]

    if h != final_h:
        print(f"\n🚨 WARNING: HEIGHT MISMACHT\n CURRENT H: {h}, EXCPECTED: {final_h}\n")

    x1 = max(0, min(w - final_w, camera_x - final_w // 2))
    crop = frame[0:final_h, x1:x1 + final_w]

    return crop  # 👈 tamaño fijo


def close_streams(decoder, encoder):
    """Properly closes FFmpeg pipes."""
    decoder.stdout.close()
    encoder.stdin.close()
    decoder.wait()
    encoder.wait()
#========================================================================



def detect_face_centers(frame, gray, prev_gray):
    """
    Detects faces and returns their center coordinates, bounding box and area.

    This function performs raw face detection only.
    It does not decide which face to follow.

    Returns
    -------
    dict of 
        center: (x, y)
        bbox: x, y, w, h
        area: w * h
        motion: 
    """
    #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    detections = face_cascade.detectMultiScale(gray, 1.1, 5)

    height, width = frame.shape[:2]
    frame_area = height * width

    edge_margin = int(width * EDGE_MARGIN_RATIO)

    faces = []

    for (x, y, w, h) in detections:

        area = w * h
        center_x = x + w // 2
        center_y = y + h // 2
        aspect_ratio = w / h

        mouth_y1 = int(y + h * 0.6)
        mouth_y2 = int(y + h * 0.85)
        mouth_now = gray[mouth_y1:mouth_y2, x:x+w]
        mouth_prev = prev_gray[mouth_y1:mouth_y2, x:x+w]
        if mouth_now.shape == mouth_prev.shape:
            motion_score = np.mean(cv2.absdiff(mouth_now, mouth_prev))
        else:
            motion_score = 0

        
        ## ❌ filters by min size realted to frame w/h
        if area < frame_area * MIN_FACE_RATIO:
            continue
        ## ❌ filters by edge/margin proximity
        if center_x < edge_margin or center_x > width - edge_margin:
            continue
        ## ❌ filters by aspect ratio
        if aspect_ratio < 0.6 or aspect_ratio > 1.4:
            continue

        faces.append({
            "center": (center_x, center_y),
            "bbox": (x, y, w, h),
            "area": area,
            "motion": motion_score
        })


    return faces




def update_active_speaker(faces, active_center, candidate_center,
                          candidate_frames, active_lock_frames,
                          fps, w):
    """
    Determines which detected face should be considered the current main subject.

    This function implements temporal stability so the system does NOT rapidly
    jump between different faces. It keeps tracking the current subject,
    evaluates possible new subjects, and only switches after persistence.

    It does NOT control the camera. It only decides *who* the subject is.

    Parameters
    ----------
    faces : list[tuple[int, int]]
        List of detected face centers in the current frame.
        Each item is (x, y) in pixel coordinates.

    active_center : tuple[int, int] or None
        The center of the subject currently being tracked.
        None means no subject is currently active (scene mode).

    candidate_center : tuple[int, int] or None
        A potential new subject detected but not yet confirmed.
        Used to avoid instant switching when another face appears.

    candidate_frames : int
        Number of consecutive frames the candidate subject has been
        consistently detected near the same position.
        Used to require persistence before switching.

    active_lock_frames : int
        Counter representing how long the current subject has been
        continuously tracked (positive values) or missing (negative values).
        If this drops below -fps, the system abandons the subject.

    fps : float
        Video frames per second.
        Used to convert time-based logic (like 0.5 seconds) into frame counts.

    w : int
        Frame width in pixels.
        Used to compute distance thresholds relative to image size.

    Returns
    -------
    new_active_center : tuple[int, int] or None
        The subject that should now be tracked.

    new_candidate_center : tuple[int, int] or None
        Updated candidate subject (if any).

    new_candidate_frames : int
        Updated persistence counter for the candidate.

    new_active_lock_frames : int
        Updated lock counter for the active subject.

    Behavior Summary
    ----------------
    • Keeps the current subject if still spatially close  
    • Starts evaluating a new subject only if far enough  
    • Requires ~0.5 seconds of persistence before switching  
    • Abandons subject after ~1 second of absence  
    • Prevents rapid “ping-pong” switching between faces
    """

    # ================= NO FACES =================
    if not faces:
        active_lock_frames -= 1

        # Lost subject for too long → no active subject
        if active_lock_frames < -fps * SUBJECT_LOST_TIMEOUT_SEC :
            return None, None, 0, active_lock_frames

        return active_center, candidate_center, candidate_frames, active_lock_frames

    # ================= FIND NEAREST FACE =================
    if active_center:
        nearest = min(
            faces,
            key=lambda f: math.hypot(
                f["center"][0]-active_center[0],
                f["center"][1]-active_center[1]
            )
        )
        dist = math.hypot(
            nearest["center"][0]-active_center[0],
            nearest["center"][1]-active_center[1]
        )
    else:
        
        # elegir la cara más grande(?)
        # nearest = max(faces, key=lambda f: f["area"])
        
        # el más cerca del centrado
        #frame_center_x = w // 2
        #nearest = min(faces, key=lambda f: abs(f["center"][0] - frame_center_x))
        
        # elegir donde hay mayor 'movimiento'
        nearest = max(faces, key=lambda f: f["motion"])
        dist = 0

    # ================= SAME SUBJECT =================
    SWITCH_DIST = w * 0.25
    MNI_MOTION_SCORE = 15
    if dist < SWITCH_DIST * 0.6 and nearest["motion"] > MNI_MOTION_SCORE:
        return nearest["center"], None, 0, active_lock_frames + 1

    # ================= CANDIDATE SUBJECT =================
    if candidate_center is None:
        return active_center, nearest["center"], 1, active_lock_frames

    if math.hypot(
        nearest["center"][0]-candidate_center[0],
        nearest["center"][1]-candidate_center[1]
    ) < 50:
        candidate_frames += 1
    else:
        return active_center, None, 0, active_lock_frames

    # Switch only if persistent
    if candidate_frames > fps * 0.5:
        return nearest["center"], None, 0, active_lock_frames
        #return candidate_center, None, 0, active_lock_frames

    return active_center, candidate_center, candidate_frames, active_lock_frames




def analyze_speech_activity(video_segment_path):
    """
    Estimate speech activity from a normalized video segment.

    Audio is extracted in-memory via FFmpeg, converted to mono 16 kHz,
    and analyzed using RMS energy.

    Returns a boolean mask aligned with video frames.
    """

    # 🎧 Extraer audio RAW en memoria
    cmd = [
        "ffmpeg",
        "-i", video_segment_path,
        "-ac", "1",          # mono
        "-ar", str(AUDIO_SAMPLE_RATE),      # sample rate
        "-f", "f32le",       # float32 PCM
        "-"
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    audio_bytes = process.stdout.read()
    audio = np.frombuffer(audio_bytes, np.float32)

    sr = AUDIO_SAMPLE_RATE 
    hop = int(sr / TARGET_FPS)

    # 📈 Energía RMS por frame de video
    rms = librosa.feature.rms(y=audio, hop_length=hop)[0]

    # 🧠 Más robusto que percentil fijo
    threshold = np.median(rms) + 0.5 * np.std(rms)

    speech_mask = rms > threshold

    return speech_mask




def stream_processing(video_path):
    """
    Main video processing pipeline.
    Reads video frames via FFmpeg pipe, tracks active speaker,
    directs virtual camera, reframes to vertical, and encodes output.
    Audio is NOT processed here.
    """
    print("\n🎬 PROCESSING STREAM...\n", flush=True)

    # =============== SETUP ===============

    output_path = str(PROCESSED_VIDEO / Path(video_path).name)

    w, h, fps = get_video_metadata(video_path)
    # tamaño 9:16 que entra dentro del video original
    crop_w = int(h * OUTPUT_ASPECT)
    crop_w = min(crop_w, w)

    FINAL_W = crop_w
    FINAL_H = h

    director = CameraDirector(w, FINAL_H, fps)

    decoder = init_stream_decoder(video_path)
    if DEBUG:
        encoder = init_stream_encoder(output_path, w, h, fps)
    else:
        encoder = init_stream_encoder(output_path, FINAL_W, FINAL_H, fps)

    voice_mask = analyze_speech_activity(video_path)

    frame_size = w * h * 3
    frame_idx = 0

    active_center = None
    candidate_center = None
    candidate_frames = 0
    active_lock_frames = 0
    prev_gray = None

    # =============== LOOP BY FRAME ===============
    while True:
        in_bytes = decoder.stdout.read(frame_size)
        if not in_bytes:
            break

        # copy del array(frame del video) para poder alterarlo
        frame = np.frombuffer(in_bytes, np.uint8).reshape([h, w, 3]).copy()

        # escala de grises del frame actual
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_gray is None:
            prev_gray = gray.copy()

        faces = detect_face_centers(frame, gray, prev_gray)

        # decide QUIÉN
        active_center, candidate_center, candidate_frames, active_lock_frames = update_active_speaker(
            faces, active_center, candidate_center,
            candidate_frames, active_lock_frames,
            fps, w
        )
        
        detected_x = active_center[0] if active_center else None

        is_voice = frame_idx < len(voice_mask) and voice_mask[frame_idx]

        # decide COMO mover
        camera_x = director.update(detected_x, is_voice)

        # ===== DEBUG VISUAL =====
        """
        🔵 → ALL faces/subjects detected by Haar (candidate_center)
        🟢 → active_center
        🔴 → on evaluation subject
        🟡 → dirctor cut
        """
        if DEBUG:
            height, width = frame.shape[:2]
            # ===== FACES =====
            for f in faces:
                x, y, w_box, h_box = f["bbox"]
                cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), (255,0,0), 2) # red

            if active_center:
                cv2.circle(frame, active_center, 20, (0,255,0), 2) # green

            if candidate_center:
                cv2.circle(frame, candidate_center, 20, (0,0,255), 2) # blue
            # ===== Foco del director =====
            if camera_x is not None:
                h, w = frame.shape[:2]
                cx = int(camera_x)
                cy = h // 2  # centro vertical del frame
                size = 20  # tamaño de la cruz

                cv2.line(frame, (cx - size, cy), (cx + size, cy), (0,255,255), 2)
                cv2.line(frame, (cx, cy - size), (cx, cy + size), (0,255,255), 2)
                
                half_w = FINAL_W // 2
                x1 = int(max(0, camera_x - half_w))
                x2 = int(min(width, camera_x + half_w))
                y1 = 0
                y2 = FINAL_H
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,255), 2)  # amarillo

            # ===== Texto centrado arriba =====
            if director.mode:
                text = f"MODE: {director.mode}"

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6   # más chico
                thickness = 1      # más fino

                text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
                text_width = text_size[0]

                x = (width - text_width) // 2
                y = 30  # margen superior

                cv2.putText(frame, text, (x, y),
                            font, font_scale,
                            (255,255,255), thickness)

        if DEBUG:
            out_frame = frame.copy()
        else:
            out_frame = reframe_vertical(frame, camera_x, FINAL_W, FINAL_H)

        encoder.stdin.write(out_frame.tobytes())

        frame_idx += 1
        prev_gray = gray.copy()

    close_streams(decoder, encoder)

    print(f"\n✅ VIDEO PROCESSED: {output_path}\n", flush=True)
    return output_path




def generate_video(video_path):
    """
    Executes the full visual processing pipeline on a normalized segment
    and merges the original audio track at the end.

    Parameters
    ----------
    normalized_segment_path : str
        Path to the normalized and already-trimmed video segment.

    Returns
    -------
    str
        Final processed video with audio.
    """

    # 1. Reframe / crop / camera logic
    no_audio_out = stream_processing(video_path)

    # 2. Merge original audio track
    result_video = merge_audio_track(no_audio_out, video_path)
    print(f"✅ RESULT VIDEO: {result_video}\n", flush=True)

    return result_video




# ================= PIPELINE MAIN =================
def process(video_path, start, end):
    # check video_path
        # TODO...

    normalized_video_path = normalize_video_segment(video_path, start, end)
    generate_video(normalized_video_path)