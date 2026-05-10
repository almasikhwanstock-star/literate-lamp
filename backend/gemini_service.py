import httpx
import asyncio
import base64
import json
import logging
import time
from typing import List, Optional, Dict
from config import GEMINI_API_BASE, SS_CATEGORIES, AS_CATEGORIES

logger = logging.getLogger(__name__)

class KeyStatus:
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"

class ApiKeyManager:
    def __init__(self):
        self.keys: List[str] = []
        self.statuses: Dict[str, str] = {}
        self.current_index: int = 0
        self._lock = asyncio.Lock()
        self._rate_limit_reset: Dict[str, float] = {}

    def set_keys(self, keys: List[str]):
        self.keys = [k.strip() for k in keys if k.strip()]
        self.statuses = {k: KeyStatus.ACTIVE for k in self.keys}
        self.current_index = 0
        self._rate_limit_reset = {}

    def get_keys_info(self) -> List[Dict]:
        return [{"key": f"...{k[-6:]}", "status": self.statuses.get(k, KeyStatus.ACTIVE)} for k in self.keys]

    async def get_next_key(self) -> Optional[str]:
        async with self._lock:
            now = time.time()
            for k, reset_time in list(self._rate_limit_reset.items()):
                if now > reset_time:
                    self.statuses[k] = KeyStatus.ACTIVE
                    del self._rate_limit_reset[k]
            for _ in range(len(self.keys)):
                key = self.keys[self.current_index % len(self.keys)]
                self.current_index = (self.current_index + 1) % len(self.keys)
                if self.statuses.get(key) == KeyStatus.ACTIVE:
                    return key
            return None

    async def mark_rate_limited(self, key: str):
        async with self._lock:
            self.statuses[key] = KeyStatus.RATE_LIMITED
            self._rate_limit_reset[key] = time.time() + 65

    async def mark_error(self, key: str):
        async with self._lock:
            self.statuses[key] = KeyStatus.ERROR

key_manager = ApiKeyManager()

async def call_gemini(model: str, parts: List[Dict], max_retries: int = None) -> Dict:
    max_retries = max_retries or max(len(key_manager.keys) * 2, 3)
    for attempt in range(max_retries):
        key = await key_manager.get_next_key()
        if not key:
            raise Exception("All API keys exhausted or rate-limited. Please wait or add more keys.")
        url = f"{GEMINI_API_BASE}/{model}:generateContent?key={key}"
        payload = {"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json"}}
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
            if response.status_code == 429:
                await key_manager.mark_rate_limited(key)
                await asyncio.sleep(1)
                continue
            if response.status_code == 200:
                result = response.json()
                raw = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw)
            if response.status_code in (400, 403):
                await key_manager.mark_error(key)
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Request error: {e}")
            await asyncio.sleep(2)
    raise Exception(f"Failed after {max_retries} attempts")

def build_prompt(media_label: str, platforms: List[str], keyword_count: int) -> str:
    ss_cats = ", ".join(SS_CATEGORIES)
    as_cats = ", ".join([f"{k}={v}" for k, v in AS_CATEGORIES.items()])
    
    fields = {
        "title": "max 200 chars, English, descriptive",
        "keywords": f"exactly {keyword_count} comma-separated English keywords ordered by relevance"
    }
    
    if "shutterstock" in platforms:
        fields["ss_category1"] = f"one from: {ss_cats}"
        fields["ss_category2"] = f"another from same list or empty string"
    
    if "adobe_stock" in platforms:
        fields["as_category1"] = f"numeric code only, from: {as_cats}"
        fields["as_category2"] = f"another numeric code or 0 for none"

    fields_str = json.dumps(fields, indent=2)
    return (
        f"Analyze this {media_label} and generate stock metadata. "
        f"Return ONLY a JSON object with these fields:\n{fields_str}"
    )

async def analyze_image(model: str, image_data: bytes, mime_type: str, platforms: List[str], keyword_count: int) -> Dict:
    b64 = base64.b64encode(image_data).decode()
    parts = [
        {"text": build_prompt("image", platforms, keyword_count)},
        {"inlineData": {"mimeType": mime_type, "data": b64}}
    ]
    return await call_gemini(model, parts)

async def analyze_video_frames(model: str, frames: List[bytes], platforms: List[str], keyword_count: int) -> Dict:
    parts = [{"text": build_prompt("video (frames shown)", platforms, keyword_count)}]
    for frame in frames:
        b64 = base64.b64encode(frame).decode()
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": b64}})
    return await call_gemini(model, parts)
