---
name: python-pytest-test-generation
description: "Generate or regenerate pytest test files for Python modules. Use this when asked to create unit tests, expand Python test coverage, or rewrite brittle pytest tests from source code."
argument-hint: "[source file] [output file]"
---

# Python Pytest Test Generation

Use this skill when the task is to generate a complete pytest file for a Python module.

## Goals

- Produce a single reviewable pytest file.
- Cover normal behavior, edge cases, and explicit error behavior present in the source.
- Stay faithful to the actual implementation instead of inventing helpers, fixtures, or unsupported APIs.

## Procedure

1. Read the source module included in the request.
2. Identify the public functions, their observable behavior, and any explicit exception messages.
3. Generate one complete pytest file only.
4. Use the exact import/bootstrap block provided in the request when one is supplied.
5. Prefer `@pytest.mark.parametrize` when it makes coverage clearer and reduces repetition.
6. Assert explicit exception messages when the source code defines them.
7. Return raw Python source only, with no Markdown fences and no commentary.

## Constraints

- Use pytest only.
- Do not invent fixtures, helper utilities, or dependencies that are not already available.
- Keep assertions behavior-focused and specific.
- Do not leave TODOs, placeholders, or pseudocode.
- If the request names an output path, generate content suitable for that destination as a full file.

## Test Design Checklist

- Happy-path cases are covered.
- Boundary and edge cases are covered.
- Invalid inputs are covered when behavior is explicit in the source.
- Every named public function is exercised at least once.
- The final output is valid Python syntax.