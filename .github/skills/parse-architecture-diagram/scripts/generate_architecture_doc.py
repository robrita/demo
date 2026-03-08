"""Generate a structured architecture markdown document from a JSON description.

Reads a JSON file describing architecture components and produces a formatted
markdown document following the architecture document template.

Usage:
    python generate_architecture_doc.py <input.json> [--output <output.md>]

Expected JSON schema:
{
    "overview": "One paragraph system summary",
    "region": "Cloud region or environment",
    "component_groups": [
        {
            "name": "CI/CD",
            "components": [
                {
                    "name": "GitHub Actions",
                    "resource_name": "gh-actions-prod",
                    "description": "Handles build and deployment pipelines"
                }
            ]
        }
    ],
    "data_flow": "User -> CDN -> App -> DB (ASCII-art or text description)",
    "decisions": [
        "Containerized deployment using Azure Container Apps",
        "OpenTelemetry for distributed tracing"
    ]
}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def generate(input_path: str, output_path: str | None = None) -> str:
    """Read *input_path* JSON and produce a markdown architecture document."""
    path = Path(input_path)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if output_path is None:
        output_path = str(path.with_name("architecture-document.md"))

    lines: list[str] = []

    # Title
    lines.append("# Architecture Document")
    lines.append("")

    # Overview
    lines.append("## Overview")
    lines.append("")
    lines.append(data.get("overview", "*TODO: Add system overview*"))
    lines.append("")

    # Region / Environment
    lines.append("## Region / Environment")
    lines.append("")
    lines.append(data.get("region", "*TODO: Add region or environment*"))
    lines.append("")

    # Components
    lines.append("## Components")
    lines.append("")
    for group in data.get("component_groups", []):
        lines.append(f"### {group['name']}")
        lines.append("")
        lines.append("| Component | Resource Name | Description |")
        lines.append("|-----------|---------------|-------------|")
        for comp in group.get("components", []):
            name = comp.get("name", "")
            resource = comp.get("resource_name", "—")
            desc = comp.get("description", "")
            # Escape pipe characters in cell values
            name = name.replace("|", "\\|")
            resource = resource.replace("|", "\\|")
            desc = desc.replace("|", "\\|")
            lines.append(f"| {name} | `{resource}` | {desc} |")
        lines.append("")

    # Data Flow Summary
    lines.append("## Data Flow Summary")
    lines.append("")
    lines.append("```")
    lines.append(data.get("data_flow", "TODO: Add data flow diagram"))
    lines.append("```")
    lines.append("")

    # Key Architectural Decisions
    lines.append("## Key Architectural Decisions")
    lines.append("")
    for decision in data.get("decisions", []):
        lines.append(f"- {decision}")
    lines.append("")

    content = "\n".join(lines)
    Path(output_path).write_text(content, encoding="utf-8")
    print(f"Architecture document saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate architecture document from JSON"
    )
    parser.add_argument("input_path", help="Path to JSON file with architecture components")
    parser.add_argument(
        "--output", "-o",
        help="Output markdown file path (default: architecture-document.md next to input)"
    )
    args = parser.parse_args()
    generate(args.input_path, args.output)
