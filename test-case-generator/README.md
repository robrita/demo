# msai-landscape

This workspace contains a small Python sample and a test generator that uses the GitHub Copilot Python SDK to produce pytest test cases from source files. The SDK wrapper now loads the generation behavior from a Copilot agent skill under `.github/skills`, while the Python script handles configuration, validation, and file output. It can use either the default Copilot model path or a Microsoft Foundry model through the SDK's custom provider support.

## Project layout

- `test-case-generator/src/math_utils.py`: sample module to test
- `.github/skills/python-pytest-test-generation/SKILL.md`: agent skill that defines the pytest generation workflow
- `test-case-generator/generate_test_cases.py`: Copilot SDK-based wrapper that loads the skill, sends source context, and writes validated output
- `test-case-generator/pyproject.toml`: uv project metadata and dependencies

## Prerequisites

- Python 3.8 or later
- Access to GitHub Copilot for the SDK runtime
- Optionally, `GITHUB_TOKEN` if you want to pass an explicit token to the Copilot SDK instead of using the logged-in CLI session
- For Foundry in the Copilot SDK, a deployed model, a compatible base URL, and an API key

## Setup

From the repository root:

```powershell
uv sync
```

## Configuration

The generator can read optional defaults from `test-case-generator/.env`.
Start from the sample file:

```powershell
Copy-Item .\test-case-generator\.env.example .\test-case-generator\.env
```

Supported variables:

- `PROJECT_DIR`: base directory for path resolution. Default: `.` relative to `generate_test_cases.py`
- `SOURCE_FILE`: source module path relative to `PROJECT_DIR`. Default: `src/math_utils.py`
- `OUTPUT_FILE`: destination path relative to `PROJECT_DIR`. Default: `tests/test_math_utils.py`
- `OVERWRITE_OUTPUT`: replaces an existing output file when set to `true`. Default: `false`
- `MODEL_PROVIDER`: SDK path to use, either `copilot` or `foundry`. Default: `copilot`
- `COPILOT_MODEL`: default model name used for the normal Copilot path. Default: `gpt-5`
- `GITHUB_TOKEN`: optional GitHub token passed directly to the Copilot SDK. Default example: `your-github-token`
- `FOUNDRY_MODEL_NAME`: deployed Microsoft Foundry model name. Default example: `gpt-4.1`
- `FOUNDRY_BASE_URL`: base URL used by the Copilot SDK custom provider. Default example: `https://your-resource.openai.azure.com`
- `FOUNDRY_API_KEY`: Foundry API key. Default example: `replace-with-foundry-api-key`
- `FOUNDRY_PROVIDER_TYPE`: custom provider type, `azure` or `openai`. Default: `azure`
- `FOUNDRY_WIRE_API`: Copilot SDK wire API, `completions` or `responses`. Default: `completions`
- `FOUNDRY_API_VERSION`: API version for `azure` provider type. Default: `2024-10-21`
- `GENERATION_TIMEOUT_SECONDS`: how long to wait for the Copilot session to become idle. Default: `180`
- `LOG_LEVEL`: Python logging level for the generator. Default: `INFO`
- `LOG_COPILOT_EVENTS`: when `true`, logs every Copilot session event type. Default: `false`

The script is env-only. It does not accept runtime flags.

If you copy `.env.example` to `.env` and leave the sample credential values unchanged, the script ignores those placeholders instead of treating them as real credentials.

The generator expects the skill file at `.github/skills/python-pytest-test-generation/SKILL.md`. If that file is missing, the script fails fast instead of silently falling back to a weaker prompt.

For Foundry, the script still uses `CopilotClient.create_session(...)`, but now adds both the SDK `skill_directories` config and the optional `provider` config. That keeps the Foundry path inside the GitHub Copilot SDK instead of switching to a separate Azure SDK.

Foundry config shape in the SDK:

- Use `FOUNDRY_PROVIDER_TYPE=azure` when the deployment is exposed as an Azure endpoint and set `FOUNDRY_BASE_URL` to the host URL.
- Use `FOUNDRY_PROVIDER_TYPE=openai` when your Foundry deployment exposes an OpenAI-compatible base URL.

## Generate tests

From the repository root:

```powershell
uv run python .\test-case-generator\generate_test_cases.py
```

During generation, the SDK session loads the workspace skill directory at `.github/skills` and applies the `python-pytest-test-generation` skill.

This defaults to:

- source file: `test-case-generator/src/math_utils.py`
- output file: `test-case-generator/tests/test_math_utils.py`
- provider: `copilot`
- model: `gpt-5`

Model selection is provider-specific:

- `MODEL_PROVIDER=copilot` uses `COPILOT_MODEL` or falls back to `gpt-5`
- `MODEL_PROVIDER=foundry` uses `FOUNDRY_MODEL_NAME` or falls back to `gpt-4.1`

To change behavior, edit `test-case-generator/.env`. Example:

```powershell
PROJECT_DIR=.
SOURCE_FILE=src/math_utils.py
OUTPUT_FILE=tests/test_math_utils.py
OVERWRITE_OUTPUT=true
MODEL_PROVIDER=foundry
FOUNDRY_MODEL_NAME=gpt-4.1
FOUNDRY_PROVIDER_TYPE=azure
FOUNDRY_BASE_URL=https://my-resource.openai.azure.com
FOUNDRY_API_KEY=your-api-key
GENERATION_TIMEOUT_SECONDS=300
LOG_LEVEL=DEBUG
LOG_COPILOT_EVENTS=true
```

The script now writes structured logs to stderr so you can see path resolution, SDK startup, session creation, prompt submission, and timeout diagnostics. If generation appears stuck, set `LOG_LEVEL=DEBUG` and optionally `LOG_COPILOT_EVENTS=true` to see the last Copilot event before the timeout.

## Run tests

After generating tests:

```powershell
uv run pytest .\test-case-generator\tests
```

## Notes

- The GitHub Copilot SDK is in technical preview and generated tests should be reviewed before committing them.
- The Foundry path uses the GitHub Copilot SDK custom `provider` configuration rather than a separate inference client.
- Both Copilot and Foundry modes send the source code directly in the prompt, while the detailed generation policy lives in the skill so it can be reused by Copilot agent workflows.
- If the output file already exists, set `OVERWRITE_OUTPUT=true` to replace it.
