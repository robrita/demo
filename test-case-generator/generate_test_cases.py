"""Automated pytest test-file generator powered by the GitHub Copilot SDK.

Reads a Python source module, extracts its public API, builds a prompt using
a Copilot skill, sends it to either the Copilot or Microsoft Foundry backend,
and writes a validated pytest file to disk.
"""

from __future__ import annotations

import ast
import asyncio
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Default configuration constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "gpt-5"
SUPPORTED_PROVIDERS = ("copilot", "foundry")
DEFAULT_FOUNDRY_PROVIDER_TYPE = "azure"
DEFAULT_FOUNDRY_WIRE_API = "completions"
DEFAULT_FOUNDRY_API_VERSION = "2024-10-21"
DEFAULT_PROJECT_DIR = "."
DEFAULT_SOURCE = "src/math_utils.py"
DEFAULT_OUTPUT = "tests/test_math_utils.py"
DEFAULT_MODEL_PROVIDER = "copilot"
DEFAULT_FOUNDRY_MODEL = "gpt-4.1"
DEFAULT_GENERATION_TIMEOUT_SECONDS = 180.0
DEFAULT_LOG_LEVEL = "INFO"
SKILL_NAME = "python-pytest-test-generation"
SKILL_FILE = "SKILL.md"

# Regex to extract Python code from Markdown-fenced blocks in model responses
CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
logger = logging.getLogger("test_case_generator")


# ---------------------------------------------------------------------------
# Settings dataclass — immutable snapshot of all resolved configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    project_dir: Path
    source: str
    output: str | None
    provider: str
    model: str
    overwrite: bool
    github_token: str | None
    foundry_endpoint: str | None
    foundry_api_key: str | None
    foundry_provider_type: str
    foundry_wire_api: str
    foundry_api_version: str
    generation_timeout_seconds: float
    log_level: str
    log_copilot_events: bool


# ---------------------------------------------------------------------------
# Environment & configuration helpers
# ---------------------------------------------------------------------------


def parse_bool(value: str | None, default: bool = False) -> bool:
    """Interpret truthy string values ('1', 'true', 'yes', 'on')."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_float(value: str | None, default: float) -> float:
    """Safely convert a string to float, returning *default* on failure."""
    if value is None:
        return default

    try:
        return float(value.strip())
    except ValueError:
        return default


def get_env(name: str, default: str | None = None) -> str | None:
    """Read an env var, treating blank strings as missing."""
    value = os.environ.get(name)
    if value is None:
        return default

    value = value.strip()
    if value == "":
        return default

    return value


def resolve_project_dir(script_dir: Path) -> Path:
    """Resolve the project root, defaulting to the script's own directory."""
    configured_dir = Path(get_env("PROJECT_DIR", DEFAULT_PROJECT_DIR))
    if not configured_dir.is_absolute():
        configured_dir = script_dir / configured_dir
    return configured_dir.resolve()


def configure_logging(log_level: str) -> None:
    """Set up root logging with a timestamped format."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def sanitize_endpoint(endpoint: str | None) -> str | None:
    """Normalize an endpoint URL by stripping trailing slashes from the path."""
    if not endpoint:
        return None

    parsed = urlparse(endpoint)
    if parsed.scheme and parsed.netloc:
        path = parsed.path.rstrip("/")
        return f"{parsed.scheme}://{parsed.netloc}{path}"
    return endpoint


def preview_text(value: str | None, max_length: int = 160) -> str:
    """Return a truncated, single-line preview suitable for log messages."""
    if not value:
        return "<none>"

    normalized = re.sub(r"\s+", " ", value).strip()
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 3] + "..."


def log_settings(settings: Settings) -> None:
    """Emit a single INFO line summarizing the resolved configuration."""
    logger.info(
        "Loaded settings: project_dir=%s source=%s output=%s provider=%s model=%s overwrite=%s timeout_seconds=%.1f github_token=%s foundry_endpoint=%s foundry_provider_type=%s foundry_wire_api=%s foundry_api_version=%s log_copilot_events=%s",
        settings.project_dir,
        settings.source,
        settings.output,
        settings.provider,
        settings.model,
        settings.overwrite,
        settings.generation_timeout_seconds,
        bool(settings.github_token),
        sanitize_endpoint(settings.foundry_endpoint),
        settings.foundry_provider_type,
        settings.foundry_wire_api,
        settings.foundry_api_version,
        settings.log_copilot_events,
    )


def load_settings() -> Settings:
    """Build a Settings object from environment variables and .env file."""
    script_dir = Path(__file__).resolve().parent
    load_dotenv(script_dir / ".env", override=False)

    # Determine which backend to use: "copilot" (default) or "foundry"
    default_provider = (get_env("MODEL_PROVIDER", DEFAULT_MODEL_PROVIDER) or DEFAULT_MODEL_PROVIDER).lower()
    if default_provider not in SUPPORTED_PROVIDERS:
        default_provider = DEFAULT_MODEL_PROVIDER

    # Each provider has its own model name env var
    if default_provider == "foundry":
        model = get_env("FOUNDRY_MODEL_NAME") or DEFAULT_FOUNDRY_MODEL
    else:
        model = get_env("COPILOT_MODEL") or DEFAULT_MODEL

    return Settings(
        project_dir=resolve_project_dir(script_dir),
        source=get_env("SOURCE_FILE", DEFAULT_SOURCE) or DEFAULT_SOURCE,
        output=get_env("OUTPUT_FILE", DEFAULT_OUTPUT),
        provider=default_provider,
        model=model,
        overwrite=parse_bool(get_env("OVERWRITE_OUTPUT"), default=False),
        github_token=get_env("GITHUB_TOKEN"),
        foundry_endpoint=(
            get_env("FOUNDRY_BASE_URL")
            or get_env("FOUNDRY_MODEL_ENDPOINT")
            or None
        ),
        foundry_api_key=get_env("FOUNDRY_API_KEY") or get_env("AZURE_API_KEY") or None,
        foundry_provider_type=(
            get_env("FOUNDRY_PROVIDER_TYPE", DEFAULT_FOUNDRY_PROVIDER_TYPE)
            or DEFAULT_FOUNDRY_PROVIDER_TYPE
        ).lower(),
        foundry_wire_api=(
            get_env("FOUNDRY_WIRE_API", DEFAULT_FOUNDRY_WIRE_API)
            or DEFAULT_FOUNDRY_WIRE_API
        ).lower(),
        foundry_api_version=get_env("FOUNDRY_API_VERSION", DEFAULT_FOUNDRY_API_VERSION)
        or DEFAULT_FOUNDRY_API_VERSION,
        generation_timeout_seconds=parse_float(
            get_env("GENERATION_TIMEOUT_SECONDS"),
            DEFAULT_GENERATION_TIMEOUT_SECONDS,
        ),
        log_level=(get_env("LOG_LEVEL", DEFAULT_LOG_LEVEL) or DEFAULT_LOG_LEVEL).upper(),
        log_copilot_events=parse_bool(get_env("LOG_COPILOT_EVENTS"), default=False),
    )


# ---------------------------------------------------------------------------
# Source analysis & path resolution
# ---------------------------------------------------------------------------


def extract_public_functions(source_code: str) -> list[str]:
    """Use the AST to find all top-level, non-private function names."""
    module = ast.parse(source_code)
    functions: list[str] = []
    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            functions.append(node.name)
    return functions


def resolve_paths(settings: Settings) -> tuple[Path, Path, Path]:
    """Return (project_dir, source_path, output_path) as absolute paths."""
    project_dir = settings.project_dir
    source_path = (project_dir / settings.source).resolve()

    if settings.output:
        output_path = (project_dir / settings.output).resolve()
    else:
        output_path = (project_dir / "tests" / f"test_{source_path.stem}.py").resolve()

    return project_dir, source_path, output_path


def resolve_skill_directory(script_dir: Path) -> Path:
    """Locate the .github/skills directory containing the generation skill."""
    skills_dir = (script_dir.parent / ".github" / "skills").resolve()
    skill_path = skills_dir / SKILL_NAME / SKILL_FILE
    if not skill_path.exists():
        raise FileNotFoundError(f"Required Copilot skill not found: {skill_path}")
    return skills_dir


# ---------------------------------------------------------------------------
# Prompt construction & response processing
# ---------------------------------------------------------------------------


def build_prompt(
    source_path: Path,
    output_path: Path,
    module_name: str,
    public_functions: list[str],
    source_code: str,
) -> str:
    """Assemble the LLM prompt including the import block and source code."""
    imported_functions = ", ".join(public_functions)
    import_block = f'''from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from {module_name} import {imported_functions}
'''

    return f'''Use the configured {SKILL_NAME} skill to generate a complete pytest test file for the provided Python module.

Return only raw Python source code.
Do not include Markdown fences.
Do not include any explanation before or after the code.

Request context:
- source module path: {source_path}
- destination path: {output_path}
- module name: {module_name}
- public functions: {", ".join(public_functions)}

Use this import/bootstrap block exactly as written at the top of the file:

{import_block}

Source module contents:

{source_code}
'''


def extract_python_code(response_text: str) -> str:
    """Strip Markdown fences from the model response, keeping the longest block."""
    matches = CODE_BLOCK_RE.findall(response_text)
    if matches:
        response_text = max(matches, key=len)
    return response_text.strip()


def validate_generated_code(code: str, module_name: str, public_functions: list[str]) -> None:
    """Ensure the generated code is syntactically valid and covers all public functions."""
    if not code:
        raise ValueError("The model returned an empty response.")
    if "import pytest" not in code:
        raise ValueError("Generated output does not look like a pytest test file.")
    if "def test_" not in code and "@pytest.mark.parametrize" not in code:
        raise ValueError("Generated output does not define any test cases.")

    # Check that the source module is actually imported
    has_direct_import = f"from {module_name} import" in code
    has_module_import = f"import {module_name}" in code
    if not has_direct_import and not has_module_import:
        raise ValueError(f"Generated output does not import {module_name}.")

    # Every public function must be referenced somewhere in the test file
    missing_functions = [name for name in public_functions if name not in code]
    if missing_functions:
        raise ValueError(
            "Generated output is missing references to expected functions: "
            + ", ".join(missing_functions)
        )

    # Final sanity check: can Python actually parse the output?
    try:
        ast.parse(code)
    except SyntaxError as exc:
        raise ValueError(f"Generated output is not valid Python syntax: {exc}") from exc


# ---------------------------------------------------------------------------
# Copilot SDK integration
# ---------------------------------------------------------------------------


def load_copilot_sdk() -> tuple[type, object, object]:
    """Lazily import the Copilot SDK so the rest of the module stays testable."""
    try:
        from copilot import CopilotClient, PermissionHandler
        from copilot.generated.session_events import SessionEventType
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'github-copilot-sdk'. Install project dependencies with 'uv sync --project .\\test-case-generator'."
        ) from exc
    return CopilotClient, PermissionHandler, SessionEventType


async def send_prompt_and_wait(
    session: object,
    prompt: str,
    timeout: float,
    session_event_type: object,
    log_copilot_events: bool,
) -> str:
    """Send a prompt to the Copilot session and block until it goes idle.

    Subscribes to session events to capture the assistant reply, surface
    errors, and detect when processing is complete (SESSION_IDLE).
    """
    idle_event = asyncio.Event()
    error_event: RuntimeError | None = None
    last_assistant_content: str | None = None
    last_event_type = "<none>"
    event_count = 0

    # Event callback — runs for every SDK event on this session
    def handler(event: object) -> None:
        nonlocal error_event, event_count, last_assistant_content, last_event_type
        event_count += 1
        last_event_type = getattr(event.type, "value", str(event.type))

        if log_copilot_events:
            logger.info("Copilot session event: %s", last_event_type)

        if event.type == session_event_type.ASSISTANT_MESSAGE:
            last_assistant_content = getattr(event.data, "content", None)
            logger.info(
                "Received assistant message event. content_length=%d preview=%s",
                len(last_assistant_content or ""),
                preview_text(last_assistant_content),
            )
        elif event.type == session_event_type.SESSION_ERROR:
            message = getattr(event.data, "message", str(event.data))
            logger.error("Copilot session error event: %s", message)
            error_event = RuntimeError(f"Session error: {message}")
            idle_event.set()
        elif event.type == session_event_type.SESSION_IDLE:
            logger.info("Copilot session is idle.")
            idle_event.set()

    # Subscribe to session events; unsubscribe in the finally block
    unsubscribe = session.on(handler)
    started_at = time.perf_counter()

    try:
        logger.info(
            "Sending prompt to Copilot session. timeout_seconds=%.1f prompt_chars=%d",
            timeout,
            len(prompt),
        )
        message_id = await session.send({"prompt": prompt})
        logger.info("Prompt accepted by Copilot session. message_id=%s", message_id)
        await asyncio.wait_for(idle_event.wait(), timeout=timeout)
    except TimeoutError as exc:
        elapsed = time.perf_counter() - started_at
        logger.error(
            "Timed out waiting for Copilot session to become idle after %.1f seconds. events_seen=%d last_event=%s last_assistant_preview=%s",
            elapsed,
            event_count,
            last_event_type,
            preview_text(last_assistant_content),
        )
        raise TimeoutError(
            "Timed out waiting for Copilot session to become idle. "
            f"last_event={last_event_type}; last_assistant_preview={preview_text(last_assistant_content)}"
        ) from exc
    finally:
        unsubscribe()

    if error_event:
        raise error_event

    logger.info(
        "Copilot session completed in %.1f seconds with %d events.",
        time.perf_counter() - started_at,
        event_count,
    )

    if last_assistant_content is None:
        raise RuntimeError("Copilot session became idle without returning an assistant message.")

    return last_assistant_content


def build_custom_provider(settings: Settings) -> dict[str, object]:
    """Build a Foundry provider config dict for the Copilot SDK session."""
    if not settings.foundry_endpoint:
        raise ValueError(
            "Microsoft Foundry in the Copilot SDK requires FOUNDRY_BASE_URL."
        )
    if not settings.foundry_api_key:
        raise ValueError(
            "Microsoft Foundry requires FOUNDRY_API_KEY."
        )
    if not settings.model:
        raise ValueError(
            "Microsoft Foundry requires FOUNDRY_MODEL_NAME."
        )

    provider: dict[str, object] = {
        "type": settings.foundry_provider_type,
        "base_url": settings.foundry_endpoint,
        "api_key": settings.foundry_api_key,
        "wire_api": settings.foundry_wire_api,
    }
    # Azure-specific: attach the API version required by Azure OpenAI
    if settings.foundry_provider_type == "azure":
        provider["azure"] = {"api_version": settings.foundry_api_version}

    return provider


async def generate_with_copilot(settings: Settings, project_dir: Path, prompt: str) -> str:
    """Spin up a Copilot client, open a session, send the prompt, and return the response."""
    CopilotClient, PermissionHandler, SessionEventType = load_copilot_sdk()
    skill_directory = resolve_skill_directory(Path(__file__).resolve().parent)
    logger.info("Resolved skill directory: %s", skill_directory)

    # When a personal token is provided, skip the default browser-based auth
    client_options: dict[str, object] = {"cwd": str(project_dir)}
    if settings.github_token:
        client_options["github_token"] = settings.github_token
        client_options["use_logged_in_user"] = False

    logger.info("Starting Copilot client. cwd=%s provider=%s model=%s", project_dir, settings.provider, settings.model)
    client = CopilotClient(client_options)
    session = None

    try:
        await client.start()
        logger.info("Copilot client started.")

        # Configure the session: model, skills, auto-approve permissions
        session_config = {
            "model": settings.model,
            "available_tools": [],
            "skill_directories": [str(skill_directory)],
            "on_permission_request": PermissionHandler.approve_all,
            "system_message": {
                "mode": "replace",
                "content": (
                    "You generate reviewable Python pytest files using loaded Copilot skills. "
                    "Return only Python code and nothing else."
                ),
            },
        }
        # Attach Foundry credentials when using a non-Copilot backend
        if settings.provider == "foundry":
            session_config["provider"] = build_custom_provider(settings)

        logger.info("Creating Copilot session.")
        session = await client.create_session(session_config)
        logger.info("Copilot session created. session_id=%s", getattr(session, "session_id", "<unknown>"))
        response = await send_prompt_and_wait(
            session=session,
            prompt=prompt,
            timeout=settings.generation_timeout_seconds,
            session_event_type=SessionEventType,
            log_copilot_events=settings.log_copilot_events,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Copilot SDK runtime could not be started. Ensure the SDK is installed and authenticated."
        ) from exc
    finally:
        if session is not None:
            logger.info("Disconnecting Copilot session.")
            await session.disconnect()
        logger.info("Stopping Copilot client.")
        await client.stop()

    return response


# ---------------------------------------------------------------------------
# Orchestration — ties everything together
# ---------------------------------------------------------------------------


async def generate_tests(settings: Settings) -> int:
    """End-to-end pipeline: read source → build prompt → call model → write tests."""
    project_dir, source_path, output_path = resolve_paths(settings)
    logger.info("Resolved paths: project_dir=%s source_path=%s output_path=%s", project_dir, source_path, output_path)

    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")
    if output_path.exists() and not settings.overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}. Set OVERWRITE_OUTPUT=true to replace it."
        )

    source_code = source_path.read_text(encoding="utf-8")
    public_functions = extract_public_functions(source_code)
    if not public_functions:
        raise ValueError(f"No public functions found in {source_path}")

    logger.info(
        "Loaded source module. bytes=%d public_functions=%s",
        len(source_code.encode("utf-8")),
        ", ".join(public_functions),
    )

    prompt = build_prompt(
        source_path=source_path,
        output_path=output_path,
        module_name=source_path.stem,
        public_functions=public_functions,
        source_code=source_code,
    )
    logger.info("Built generation prompt. chars=%d", len(prompt))

    # Send the prompt to the model (Copilot or Foundry) and get the raw reply
    raw_response = await generate_with_copilot(settings, project_dir, prompt)
    logger.info("Received raw model response. chars=%d preview=%s", len(raw_response), preview_text(raw_response))

    # Extract the code block from the response and validate it
    code = extract_python_code(raw_response)
    logger.info("Extracted Python code block. chars=%d", len(code))
    validate_generated_code(code, source_path.stem, public_functions)
    logger.info("Validated generated pytest file successfully.")

    # Write the validated test file to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code.rstrip() + "\n", encoding="utf-8")
    logger.info("Wrote generated tests to %s", output_path)

    print(f"Generated tests for {source_path.relative_to(project_dir)}")
    print(f"Wrote {output_path.relative_to(project_dir)}")
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Parse settings, configure logging, and run the async generation pipeline."""
    settings = load_settings()
    configure_logging(settings.log_level)
    log_settings(settings)

    try:
        return asyncio.run(generate_tests(settings))
    except KeyboardInterrupt:
        print("Generation cancelled.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())