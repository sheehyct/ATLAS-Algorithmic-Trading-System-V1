from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Cfg:
    """Settings bundle driving VectorBT Pro's OpenAI provider config."""

    api_key: str
    base_url: str | None
    use_responses: bool
    reasoning_effort: str | None
    hide_thoughts: bool
    batch_size: int
    client_timeout: float
    chat_model: str
    chat_quick_model: str
    embedding_model: str


def _get_vbt() -> Any:
    try:
        import vectorbtpro as vbt  # type: ignore
    except Exception as exc:  # pragma: no cover - clear error if dependency missing
        raise RuntimeError("VectorBT Pro must be installed to use vbt_bootstrap") from exc
    return vbt


def apply_vbt_settings(cfg: Cfg) -> None:
    """Apply OpenAI provider settings for embeddings and completions."""

    vbt = _get_vbt()

    # --- Embeddings (OpenAI) ---
    vbt.settings.set("knowledge.chat.embeddings", "openai")
    vbt.settings.set("knowledge.chat.embeddings_configs.openai.model", cfg.embedding_model)
    vbt.settings.set("knowledge.chat.embeddings_configs.openai.dimensions", None)
    vbt.settings.set("knowledge.chat.embeddings_configs.openai.batch_size", cfg.batch_size)
    vbt.settings.set(
        "knowledge.chat.embeddings_configs.openai.client_kwargs.timeout",
        cfg.client_timeout,
    )

    # --- Completions (OpenAI) ---
    vbt.settings.set("knowledge.chat.completions", "openai")
    vbt.settings.set("knowledge.chat.completions_configs.openai.model", cfg.chat_model)
    vbt.settings.set(
        "knowledge.chat.completions_configs.openai.quick_model", cfg.chat_quick_model
    )
    vbt.settings.set("knowledge.chat.completions_configs.openai.client_kwargs.timeout", cfg.client_timeout)

    if cfg.reasoning_effort:
        vbt.settings.set(
            "knowledge.chat.completions_configs.openai.reasoning.effort",
            cfg.reasoning_effort,
        )

    vbt.settings.set(
        "knowledge.chat.completions_configs.openai.hide_thoughts",
        bool(cfg.hide_thoughts),
    )
    vbt.settings.set(
        "knowledge.chat.completions_configs.openai.use_responses",
        bool(cfg.use_responses),
    )

    if cfg.base_url:
        vbt.settings.set("knowledge.chat.completions_configs.openai.base_url", cfg.base_url)
        vbt.settings.set("knowledge.chat.completions_configs.openai.api_key", cfg.api_key)
        # Keep embeddings in sync with the same gateway/key if you override base_url
        vbt.settings.set("knowledge.chat.embeddings_configs.openai.base_url", cfg.base_url)
        vbt.settings.set("knowledge.chat.embeddings_configs.openai.api_key", cfg.api_key)
