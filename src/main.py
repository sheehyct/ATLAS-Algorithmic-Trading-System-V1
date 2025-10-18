from __future__ import annotations

import os

import typer
from dotenv import load_dotenv
from openai import OpenAI
from rich import box
from rich.console import Console
from rich.table import Table

try:
    import vectorbtpro as vbt  # type: ignore

    HAS_VBTP = True
except Exception:
    vbt = None  # type: ignore[assignment]
    HAS_VBTP = False

from src.vbt_bootstrap import Cfg, apply_vbt_settings

console = Console()
app = typer.Typer(help="OpenAI + VectorBT Pro utilities")


def load_cfg() -> Cfg:
    """Load configuration from environment variables into a config dataclass."""

    load_dotenv(override=False)
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY in environment/.env")
    base_url = os.getenv("OPENAI_BASE_URL")
    use_responses = os.getenv("USE_RESPONSES", "true").lower() == "true"
    reasoning_effort = os.getenv("REASONING_EFFORT")
    hide_thoughts = os.getenv("HIDE_THOUGHTS", "false").lower() == "true"
    batch_size = int(os.getenv("VBT_EMBED_BATCH", "64"))
    client_timeout = float(os.getenv("VBT_CLIENT_TIMEOUT", "20.0"))
    chat_model = os.getenv("CHAT_MODEL", "gpt-5")
    chat_quick_model = os.getenv("CHAT_QUICK_MODEL", "gpt-5-mini")
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    return Cfg(
        api_key=api_key,
        base_url=base_url,
        use_responses=use_responses,
        reasoning_effort=reasoning_effort,
        hide_thoughts=hide_thoughts,
        batch_size=batch_size,
        client_timeout=client_timeout,
        chat_model=chat_model,
        chat_quick_model=chat_quick_model,
        embedding_model=embedding_model,
    )


def make_client(cfg: Cfg) -> OpenAI:
    """Instantiate the OpenAI SDK client with optional base URL override."""

    kwargs: dict[str, object] = {"api_key": cfg.api_key}
    if cfg.base_url:
        kwargs["base_url"] = cfg.base_url
    return OpenAI(**kwargs)


@app.command()
def hello(text: str = "Say hello in 7 words.") -> None:
    """Run a minimal OpenAI Responses API call to validate credentials."""

    cfg = load_cfg()
    client = make_client(cfg)
    max_output_tokens_env = os.getenv("MAX_OUTPUT_TOKENS", "64")
    try:
        max_output_tokens = int(max_output_tokens_env)
    except ValueError:
        max_output_tokens = 64  # safe default
    resp = client.responses.create(
        model=cfg.chat_quick_model,
        input=[{"role": "user", "content": [{"type": "input_text", "text": text}]}],
        max_output_tokens=max_output_tokens,
        reasoning={"effort": cfg.reasoning_effort} if cfg.reasoning_effort else None,
    )
    console.print("[bold]Response[/bold]:", resp.output_text)
    usage = getattr(resp, "usage", None)
    if usage:
        table = Table(title="Token Usage", box=box.SIMPLE)
        table.add_column("input")
        table.add_column("output")
        table.add_column("total")
        table.add_row(
            str(getattr(usage, "input_tokens", "?")),
            str(getattr(usage, "output_tokens", "?")),
            str(getattr(usage, "total_tokens", "?")),
        )
        console.print(table)


@app.command()
def vbt_smoke() -> None:
    """Preview VectorBT Pro settings after applying OpenAI configuration."""

    if not HAS_VBTP or vbt is None:
        raise SystemExit("VectorBT Pro not installed. Install and retry.")
    cfg = load_cfg()
    apply_vbt_settings(cfg)
    keys = [
        "knowledge.chat.embeddings",
        "knowledge.chat.embeddings_configs.openai.model",
        "knowledge.chat.embeddings_configs.openai.dimensions",
        "knowledge.chat.embeddings_configs.openai.batch_size",
        "knowledge.chat.embeddings_configs.openai.client_kwargs.timeout",
        "knowledge.chat.completions",
        "knowledge.chat.completions_configs.openai.model",
        "knowledge.chat.completions_configs.openai.quick_model",
        "knowledge.chat.completions_configs.openai.reasoning.effort",
        "knowledge.chat.completions_configs.openai.hide_thoughts",
        "knowledge.chat.completions_configs.openai.use_responses",
        "knowledge.chat.completions_configs.openai.base_url",
    ]
    table = Table(title="VBT Pro provider config (OpenAI)", box=box.SIMPLE)
    table.add_column("key")
    table.add_column("value")
    for key in keys:
        try:
            value = vbt.settings.get(key)
        except Exception:
            value = "<unset>"
        table.add_row(key, str(value))
    console.print(table)


if __name__ == "__main__":
    app()
