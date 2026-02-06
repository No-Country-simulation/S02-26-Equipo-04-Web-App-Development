from fastapi import FastAPI

app = FastAPI(title="Video Shorts API")

@app.get("/")
def health():
    return {"API funcionando"}
