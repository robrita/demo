---
name: parse-architecture-diagram
description: "Parse architecture diagram images into detailed markdown architecture documents. Use when: analyzing architecture diagrams, generating architecture docs from images, documenting system components from diagrams, reverse-engineering architecture from screenshots, creating component inventories from visual diagrams."
argument-hint: "path/to/diagram.png"
---

# Parse Architecture Diagram

Analyze architecture diagram images and produce comprehensive markdown architecture documents with components, data flows, and design decisions.

## When to Use

- Converting visual architecture diagrams to documentation
- Analyzing system design from diagram images
- Generating component inventories from architecture screenshots
- Creating structured architecture documents from visual references

## Procedure

### Step 1: View the Image

The user will provide a file path to an architecture diagram image (e.g., `architecture-parser/sample-arch.png`). Image files are binary and **cannot** be read with `read_file`. Instead, open the image in a browser page using `open_browser_page` with a `file:///` URL, then capture it with `screenshot_page`:

```
open_browser_page  url=file:///<absolute-path-to-image>
screenshot_page    pageId=<returned-page-id>
```

### Step 2: Analyze the Diagram

Examine the image and identify every visible element:

- **Components and services**: names, types, icons, cloud provider symbols
- **Connection lines and labels**: e.g., `OTel`, `Responses API`, `pull`, `push`, arrows
- **Boundary boxes**: groupings like "Compute", "AI Services", "Data", "Networking"
- **Region / environment labels**: cloud region, subscription, resource group
- **Exact resource names**: e.g., `ca-techpulse-prod`, `crtechpulseprod`, `kv-app-prod`

### Step 3: Generate the Architecture Document

Create `architecture-document.md` in the **same directory** as the source image.

**Option A — Direct creation**: Use `create_file` to write the markdown directly following the output structure below.

**Option B — Script-based generation**: Structure your findings as JSON and run:

```shell
uv run python .github/skills/parse-architecture-diagram/scripts/generate_architecture_doc.py <components.json> --output <path/to/architecture-document.md>
```

See [JSON input format](./scripts/generate_architecture_doc.py) for the expected schema, and [output template](./references/output-template.md) for a reference.

## Output Structure

The generated `architecture-document.md` must include these sections:

### 1. Overview

One-paragraph summary of the system: what it does, primary tech stack, and deployment target.

### 2. Region / Environment

Cloud region or deployment environment shown in the diagram.

### 3. Components

Group components by logical category (e.g., CI/CD, Compute, Data, AI, Networking, External). For each group, provide a table:

| Component | Resource Name | Description |
|-----------|---------------|-------------|
| Azure Container Apps | `ca-techpulse-prod` | Runs the main application container |

### 4. Data Flow Summary

An ASCII-art or text-based flow diagram showing how data moves through the system end to end.

### 5. Key Architectural Decisions

Bullet list of notable design choices inferred from the diagram (e.g., containerization strategy, observability approach, security patterns, networking choices).

## Formatting Guidelines

- Use **tables** for component inventories.
- Capture **exact resource names** visible in the diagram.
- Note **connection labels** between services.
- Reflect **boundary-box groupings** in document structure.
- Keep descriptions **factual** — describe what is shown, not what is assumed.
