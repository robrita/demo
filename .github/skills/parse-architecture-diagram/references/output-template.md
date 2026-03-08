# Architecture Document

## Overview

{One paragraph summary: what the system does, its primary tech stack, and deployment target.}

## Region / Environment

{Cloud region or deployment environment visible in the diagram, e.g., "Azure East US 2", "AWS us-east-1", "Production Environment".}

## Components

### {Category 1, e.g., CI/CD}

| Component | Resource Name | Description |
|-----------|---------------|-------------|
| {Service name} | `{exact-resource-name}` | {Brief description of what it does} |

### {Category 2, e.g., Compute}

| Component | Resource Name | Description |
|-----------|---------------|-------------|
| {Service name} | `{exact-resource-name}` | {Brief description of what it does} |

### {Category 3, e.g., Data}

| Component | Resource Name | Description |
|-----------|---------------|-------------|
| {Service name} | `{exact-resource-name}` | {Brief description of what it does} |

### {Category 4, e.g., AI Services}

| Component | Resource Name | Description |
|-----------|---------------|-------------|
| {Service name} | `{exact-resource-name}` | {Brief description of what it does} |

### {Category 5, e.g., Networking / External}

| Component | Resource Name | Description |
|-----------|---------------|-------------|
| {Service name} | `{exact-resource-name}` | {Brief description of what it does} |

## Data Flow Summary

```
{ASCII-art or text-based flow showing how data moves end to end}

Example:
  Developer --push--> GitHub Actions --deploy--> Container Registry --pull--> Container Apps
                                                                                  |
                                                                          OpenAI (Responses API)
                                                                                  |
                                                                          Cosmos DB (store)
                                                                                  |
                                                                          App Insights (OTel)
```

## Key Architectural Decisions

- {Decision 1: e.g., "Containerized deployment using Azure Container Apps for serverless scaling"}
- {Decision 2: e.g., "OpenTelemetry-based observability via Application Insights"}
- {Decision 3: e.g., "Managed identity for service-to-service authentication"}
- {Decision 4: e.g., "GitHub Actions for CI/CD with direct container registry push"}
