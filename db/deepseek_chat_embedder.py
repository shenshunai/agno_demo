"""Embedder that uses DeepSeek *chat* models (no official /v1/embeddings on api.deepseek.com).

Official DeepSeek HTTP returns 404 for POST /v1/embeddings. This class calls
``/v1/chat/completions`` with your configured DeepSeek model and parses a JSON
vector from the reply. Slower and more costly than a real embedding API; use
only when you must stay on DeepSeek keys alone.
"""

from __future__ import annotations

import asyncio
import json
import math
import re
import struct
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Dict, List, Optional, Tuple

from agno.knowledge.embedder.base import Embedder
from agno.utils.log import log_debug, log_warning

try:
    from openai import AsyncOpenAI
    from openai import OpenAI
except ImportError as e:  # pragma: no cover
    raise ImportError("`openai` not installed") from e


def _l2_normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _fallback_from_text(text: str, dim: int) -> List[float]:
    """Deterministic pseudo-vector so inserts never see length 0."""
    out: List[float] = []
    seed = text.encode("utf-8", errors="replace")
    i = 0
    while len(out) < dim:
        digest = sha256(seed + i.to_bytes(4, "big")).digest()
        for j in range(0, len(digest) - 3, 4):
            u = struct.unpack("!I", digest[j : j + 4])[0]
            out.append((u / 2**32) * 2.0 - 1.0)
            if len(out) >= dim:
                break
        i += 1
    return _l2_normalize(out[:dim])


def _strip_markdown_fence(content: str) -> str:
    c = content.strip()
    if c.startswith("```"):
        c = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", c)
        c = re.sub(r"\s*```$", "", c)
    return c.strip()


_FLOAT_RE = re.compile(r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


def _resample_floats(nums: List[float], dim: int) -> List[float]:
    """Stretch or compress nums to length dim (linear interpolation on index)."""
    if dim <= 0 or not nums:
        return []
    if len(nums) == 1:
        return [nums[0]] * dim
    if len(nums) == dim:
        return list(nums)
    out: List[float] = []
    last = len(nums) - 1
    for i in range(dim):
        if dim == 1:
            t = 0.0
        else:
            t = i * last / (dim - 1)
        lo = int(math.floor(t))
        hi = min(lo + 1, last)
        frac = t - lo
        out.append(nums[lo] * (1.0 - frac) + nums[hi] * frac)
    return out


def _parse_vector_json(content: str, dim: int) -> Optional[List[float]]:
    try:
        data = json.loads(_strip_markdown_fence(content))
    except json.JSONDecodeError:
        return None
    arr: Optional[List[Any]] = None
    if isinstance(data, dict):
        for key in ("e", "embedding", "vec", "v", "vector", "values", "data"):
            val = data.get(key)
            if isinstance(val, list):
                arr = val
                break
    elif isinstance(data, list):
        arr = data
    if not arr:
        return None
    try:
        nums = [float(x) for x in arr]
    except (TypeError, ValueError):
        return None
    if len(nums) == 0:
        return None
    if sum(abs(x) for x in nums) < 1e-15:
        return None
    if len(nums) < dim:
        nums = nums + [0.0] * (dim - len(nums))
    elif len(nums) > dim:
        nums = nums[:dim]
    out = _l2_normalize(nums)
    if not any(abs(x) > 1e-12 for x in out):
        return None
    return out


def _parse_vector_regex(content: str, dim: int) -> Optional[List[float]]:
    """Recover floats from truncated JSON or prose-wrapped numbers."""
    stripped = _strip_markdown_fence(content)
    nums: List[float] = []
    for m in _FLOAT_RE.finditer(stripped):
        try:
            nums.append(float(m.group(0)))
        except ValueError:
            continue
        if len(nums) >= dim * 2:
            break
    if len(nums) >= dim:
        nums = nums[:dim]
    elif len(nums) >= max(8, min(dim // 4, 64)):
        nums = _resample_floats(nums, dim)
    else:
        return None
    out = _l2_normalize(nums)
    if not any(abs(x) > 1e-12 for x in out):
        return None
    return out


def _parse_embedding_content(content: str, dim: int) -> Optional[List[float]]:
    parsed = _parse_vector_json(content, dim)
    if parsed is not None:
        return parsed
    return _parse_vector_regex(content, dim)


@dataclass
class DeepSeekChatEmbedder(Embedder):
    """Chat-completions based pseudo-embeddings for DeepSeek-only setups."""

    dimensions: int = 256
    chat_model: str = "deepseek-v4-flash"
    api_key: Optional[str] = None
    base_url: str = "https://api.deepseek.com/v1"
    max_input_chars: int = 12000
    max_tokens: int = 8192
    enable_batch: bool = False
    _sync_client: Optional[OpenAI] = field(default=None, repr=False)
    _async_client: Optional[AsyncOpenAI] = field(default=None, repr=False)

    @property
    def client(self) -> OpenAI:
        if self._sync_client is None:
            params: Dict[str, Any] = {"api_key": self.api_key, "base_url": self.base_url}
            params = {k: v for k, v in params.items() if v is not None}
            self._sync_client = OpenAI(**params)
        return self._sync_client

    @property
    def aclient(self) -> AsyncOpenAI:
        if self._async_client is None:
            params: Dict[str, Any] = {"api_key": self.api_key, "base_url": self.base_url}
            params = {k: v for k, v in params.items() if v is not None}
            self._async_client = AsyncOpenAI(**params)
        return self._async_client

    def _complete_chat(
        self,
        messages: List[Dict[str, str]],
        *,
        use_json_object: bool,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "model": self.chat_model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": self.max_tokens,
        }
        if use_json_object:
            kwargs["response_format"] = {"type": "json_object"}
        return self.client.chat.completions.create(**kwargs)

    def _chat_vector(self, text: str) -> Tuple[List[float], Optional[Dict[str, Any]]]:
        clipped = text[: self.max_input_chars]
        user = f"Text to index:\n{clipped}"
        dim = self.dimensions
        systems = (
            (
                "You output JSON only for vector search indexing. "
                f'Format: {{"e":[{dim} floats in [-1,1]]}}. '
                "The array length must be exactly that number. No markdown, no explanation."
            ),
            (
                f'Reply with one JSON object only: {{"e":[{dim} numbers in [-1,1]]}}. '
                "Match the array length exactly. Single line, valid JSON, no markdown."
            ),
        )

        for system in systems:
            messages: List[Dict[str, str]] = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
            for use_json_object in (True, False):
                try:
                    resp = self._complete_chat(messages, use_json_object=use_json_object)
                except Exception as e:
                    if use_json_object:
                        continue
                    log_warning(f"DeepSeek chat embedding request failed: {e}")
                    log_debug("DeepSeek chat embedding: hash fallback after request error.")
                    return _fallback_from_text(text, dim), None

                choice = resp.choices[0].message
                raw = (choice.content or "").strip()
                parsed = _parse_embedding_content(raw, dim)
                if parsed is not None and any(abs(x) > 1e-12 for x in parsed):
                    usage = resp.usage.model_dump() if resp.usage else None
                    return parsed, usage
                if use_json_object:
                    continue

        log_debug(
            "DeepSeek chat embedding: invalid or incomplete vector after retries; "
            "using hash fallback."
        )
        return _fallback_from_text(text, dim), None

    def get_embedding(self, text: str) -> List[float]:
        return self._chat_vector(text)[0]

    def get_embedding_and_usage(self, text: str) -> Tuple[List[float], Optional[Dict]]:
        return self._chat_vector(text)

    async def async_get_embedding(self, text: str) -> List[float]:
        emb, _u = await self.async_get_embedding_and_usage(text)
        return emb

    async def async_get_embedding_and_usage(self, text: str) -> Tuple[List[float], Optional[Dict]]:
        return await asyncio.to_thread(self.get_embedding_and_usage, text)
