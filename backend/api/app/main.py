from fastapi import FastAPI
import psycopg2
import redis
import os
import threading
import json

app = FastAPI()

@app.get("/")
def health_check():
    """
    Verificar rápidamente que el servidor FastAPI
    está levantado y respondiendo requests HTTP.
    No valida dependencias externas (DB, Redis), solo el estado de la API.
    """
    return {"status": "API running"}


@app.get("/env")
def environment_check():
    """
    Verifica conectividad en tiempo real con:
      • PostgreSQL (usando DATABASE_URL)
      • Redis (usando REDIS_HOST)
    Devuelve el estado de cada servicio para debugging de infraestructura.
    No debe exponerse públicamente en producción sin autenticación.
    """
    db_status = "down"
    redis_status = "down"

    # --- Check Postgres connection ---
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = str(e)

    # --- Check Redis connection ---
    try:
        r = redis.Redis(host=os.getenv("REDIS_HOST"), port=6379)
        r.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = str(e)

    return {
        "api": "ok",
        "postgres": db_status,
        "redis": redis_status
    }


def redis_listener():
    """
    Listener de eventos asíncrono para Redis (Pub/Sub).

    Este proceso:
      • Se conecta al servidor Redis
      • Se suscribe al canal "video_events"
      • Escucha eventos enviados por el worker de procesamiento de video

    Cada evento recibido representa un cambio de estado de un video
    (por ejemplo: procesamiento finalizado).

    Corre en un hilo separado para no bloquear el servidor FastAPI.
    """
    print("🎧 API conectando a Redis...", flush=True)

    r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)
    pubsub = r.pubsub()
    pubsub.subscribe("video_events")

    print("✅ API escuchando eventos de video...", flush=True)

    # Loop infinito esperando mensajes
    for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                print("📩 Evento recibido del worker:", data, flush=True)
                # 👉 Acá luego pse podria:
                # - disparar cambios en la DB
                # - notificar websockets
                # - disparar otro proceso...
            except Exception as e:
                print("⚠️ Error procesando mensaje Redis:", e, flush=True)


@app.on_event("startup")
def start_redis_listener():
    """
    Evento de arranque de FastAPI:
        • Mensaje de arranque
        • Listener de Redis en un hilo daemon
    """
    print("\n--------------")
    print("   FAST API")
    print("--------------")
    
    print("\n🚀 FastAPI arrancando listener Redis...", flush=True)
    thread = threading.Thread(target=redis_listener, daemon=True)
    thread.start()