import asyncio
import logging
import uuid
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import GEMINI_MODELS, VIDEO_FRAME_COUNT, DEFAULT_KEYWORD_COUNT, MIN_KEYWORD_COUNT, MAX_KEYWORD_COUNT, AS_CATEGORIES
from gemini_service import key_manager, analyze_image, analyze_video_frames
from video_service import extract_frames, check_ffmpeg
from queue_manager import queue_manager, JobStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Shutterstock AI", version="2.0.0")
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

file_store: dict = {}
selected_model: str = GEMINI_MODELS[0]
active_platforms: List[str] = ["shutterstock", "adobe_stock"]
keyword_count: int = DEFAULT_KEYWORD_COUNT

class KeysPayload(BaseModel):
    keys_text: str

class ModelPayload(BaseModel):
    model: str

class PlatformsPayload(BaseModel):
    platforms: List[str]

class KeywordCountPayload(BaseModel):
    count: int

class RetryPayload(BaseModel):
    job_ids: Optional[List[str]] = None  # None = retry all failed

async def process_job(job_id: str, job: dict) -> dict:
    file_bytes = file_store.get(job_id)
    if not file_bytes:
        raise Exception("File data not found")
    media_type = job.get("media_type", "image")
    mime_type = job.get("mime_type", "image/jpeg")
    model = job.get("model", selected_model)
    platforms = job.get("platforms", active_platforms)
    kw_count = job.get("keyword_count", keyword_count)

    if media_type == "video":
        frames = await extract_frames(file_bytes, frame_count=VIDEO_FRAME_COUNT)
        if not frames:
            raise Exception("Failed to extract video frames. Is ffmpeg installed?")
        ai_data = await analyze_video_frames(model, frames, platforms, kw_count)
    else:
        ai_data = await analyze_image(model, file_bytes, mime_type, platforms, kw_count)

    file_store.pop(job_id, None)

    result = {
        "title": ai_data.get("title", ""),
        "keywords": ai_data.get("keywords", ""),
        "ss_category1": ai_data.get("ss_category1", ""),
        "ss_category2": ai_data.get("ss_category2", ""),
        "as_category1": str(ai_data.get("as_category1", "0")),
        "as_category2": str(ai_data.get("as_category2", "0")),
    }
    return result

queue_manager.set_processor(process_job)

@app.get("/health")
async def health():
    ffmpeg_ok = await check_ffmpeg()
    return {"status": "ok", "ffmpeg": ffmpeg_ok, "keys_loaded": len(key_manager.keys), "model": selected_model, "platforms": active_platforms, "keyword_count": keyword_count}

@app.get("/models")
async def get_models():
    return {"models": GEMINI_MODELS}

@app.get("/categories")
async def get_categories():
    from config import SS_CATEGORIES
    return {"shutterstock": SS_CATEGORIES, "adobe_stock": AS_CATEGORIES}

@app.post("/keys")
async def set_keys(payload: KeysPayload):
    lines = [l.strip() for l in payload.keys_text.splitlines() if l.strip()]
    if not lines:
        raise HTTPException(400, "No valid API keys provided")
    key_manager.set_keys(lines)
    return {"message": f"{len(lines)} key(s) loaded", "count": len(lines)}

@app.get("/keys/status")
async def keys_status():
    return {"keys": key_manager.get_keys_info()}

@app.post("/model")
async def set_model(payload: ModelPayload):
    global selected_model
    if payload.model not in GEMINI_MODELS:
        raise HTTPException(400, f"Unknown model: {payload.model}")
    selected_model = payload.model
    return {"model": selected_model}

@app.post("/platforms")
async def set_platforms(payload: PlatformsPayload):
    global active_platforms
    active_platforms = payload.platforms
    return {"platforms": active_platforms}

@app.post("/keyword-count")
async def set_keyword_count(payload: KeywordCountPayload):
    global keyword_count
    if not (MIN_KEYWORD_COUNT <= payload.count <= MAX_KEYWORD_COUNT):
        raise HTTPException(400, f"Count must be between {MIN_KEYWORD_COUNT} and {MAX_KEYWORD_COUNT}")
    keyword_count = payload.count
    return {"count": keyword_count}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    if not key_manager.keys:
        raise HTTPException(400, "No API keys loaded. Please add keys first.")
    job_ids = []
    for file in files:
        job_id = str(uuid.uuid4())
        file_bytes = await file.read()
        file_store[job_id] = file_bytes
        media_type = "video" if (file.content_type or "").startswith("video/") else "image"
        queue_manager.add_job(job_id, {
            "filename": file.filename,
            "mime_type": file.content_type,
            "media_type": media_type,
            "model": selected_model,
            "platforms": list(active_platforms),
            "keyword_count": keyword_count,
            "title": "", "keywords": "",
            "ss_category1": "", "ss_category2": "",
            "as_category1": "0", "as_category2": "0",
            "editorial": "no", "mature_content": "no",
            "illustration": "no", "releases": "",
        })
        job_ids.append(job_id)
    return {"job_ids": job_ids, "count": len(job_ids)}

@app.get("/queue/status")
async def queue_status():
    return queue_manager.get_status()

@app.get("/queue/jobs")
async def queue_jobs():
    jobs_out = []
    for job_id in queue_manager.queue:
        job = queue_manager.jobs.get(job_id, {})
        jobs_out.append({
            "id": job_id,
            "filename": job.get("filename",""),
            "media_type": job.get("media_type","image"),
            "status": job.get("status","pending"),
            "title": job.get("title",""),
            "keywords": job.get("keywords",""),
            "ss_category1": job.get("ss_category1",""),
            "ss_category2": job.get("ss_category2",""),
            "as_category1": job.get("as_category1","0"),
            "as_category2": job.get("as_category2","0"),
            "editorial": job.get("editorial","no"),
            "mature_content": job.get("mature_content","no"),
            "illustration": job.get("illustration","no"),
            "releases": job.get("releases",""),
            "error": job.get("error",""),
            "platforms": job.get("platforms", ["shutterstock"]),
        })
    return {"jobs": jobs_out}

@app.post("/queue/start")
async def queue_start():
    await queue_manager.start()
    return {"state": queue_manager.state}

@app.post("/queue/pause")
async def queue_pause():
    await queue_manager.pause()
    return {"state": queue_manager.state}

@app.post("/queue/stop")
async def queue_stop():
    await queue_manager.stop()
    return {"state": queue_manager.state}

@app.post("/queue/reset")
async def queue_reset():
    file_store.clear()
    await queue_manager.reset()
    return {"state": queue_manager.state}

@app.post("/queue/retry")
async def queue_retry(payload: RetryPayload):
    """Retry failed/error/cancelled jobs. Preserves done jobs."""
    target_ids = payload.job_ids
    if target_ids is None:
        target_ids = [jid for jid, j in queue_manager.jobs.items() if j.get("status") in ("error","cancelled")]
    
    retried = 0
    for job_id in target_ids:
        if job_id in queue_manager.jobs:
            job = queue_manager.jobs[job_id]
            if job.get("status") in ("error", "cancelled"):
                # Re-store file if needed (won't be there for retry, re-upload needed)
                # Just reset status so user can re-upload or we mark for re-queue
                queue_manager.jobs[job_id]["status"] = "pending"
                queue_manager.jobs[job_id]["error"] = ""
                retried += 1
    return {"retried": retried}

@app.patch("/queue/jobs/{job_id}")
async def update_job(job_id: str, data: dict):
    if job_id not in queue_manager.jobs:
        raise HTTPException(404, "Job not found")
    allowed = {"title","keywords","ss_category1","ss_category2","as_category1","as_category2","editorial","mature_content","illustration","releases"}
    queue_manager.update_job(job_id, **{k:v for k,v in data.items() if k in allowed})
    return {"ok": True}

@app.delete("/queue/jobs/{job_id}")
async def delete_job(job_id: str):
    if job_id not in queue_manager.jobs:
        raise HTTPException(404, "Job not found")
    queue_manager.jobs.pop(job_id, None)
    file_store.pop(job_id, None)
    if job_id in queue_manager.queue:
        queue_manager.queue.remove(job_id)
    return {"ok": True}

@app.delete("/queue/jobs")
async def delete_jobs(ids: List[str]):
    for job_id in ids:
        queue_manager.jobs.pop(job_id, None)
        file_store.pop(job_id, None)
        if job_id in queue_manager.queue:
            queue_manager.queue.remove(job_id)
    return {"ok": True, "deleted": len(ids)}
