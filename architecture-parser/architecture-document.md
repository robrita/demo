# Architecture Document

## Overview

TechPulse is a full-stack web application built with FastAPI (backend) and React SPA (frontend), deployed as a containerized service on Azure Container Apps in the East US 2 region. It leverages Azure AI Foundry with GPT-5.2 and GPT-Image-1.5 models via the Responses API, backed by Cosmos DB for data persistence, a Vector Store for embeddings, and AI Search (Foundry IQ) for intelligent retrieval. Observability is provided through Application Insights using OpenTelemetry. CI/CD is handled by GitHub Actions, which builds container images in Azure Container Registry and deploys updates to the Container App.

## Region / Environment

Azure – East US 2

## Components

### CI/CD

| Component | Resource Name | Description |
|-----------|---------------|-------------|
| GitHub Repository | `—` | Source code repository; triggers CI/CD pipelines on push |
| GitHub Actions | `—` | CI / Deploy / Security pipelines; runs `az acr build` and `az containerapp update` |

### Compute

| Component | Resource Name | Description |
|-----------|---------------|-------------|
| Azure Container Registry | `crtechpulseprod` | Stores container images built by GitHub Actions via `az acr build` |
| Azure Container Apps | `ca-techpulse-prod` | Runs the main application (FastAPI + React SPA); pulls images from ACR |

### Data & Observability

| Component | Resource Name | Description |
|-----------|---------------|-------------|
| Azure Cosmos DB | `—` | Primary data store for application data |
| Vector Store | `—` | Stores vector embeddings for semantic search and retrieval |
| AI Search (Foundry IQ) | `—` | Provides intelligent search and retrieval capabilities |
| Application Insights | `—` | Collects telemetry from the Container App via OpenTelemetry (OTel) |

### AI Services

| Component | Resource Name | Description |
|-----------|---------------|-------------|
| AI Foundry + Project | `—` | Central AI orchestration platform; accessed via the Responses API from the Container App |
| Bing Grounding | `—` | Provides web grounding capabilities for AI responses |
| Content Safety | `—` | Filters and moderates AI-generated content for safety |
| GPT-5.2 | `gpt-5.2` | Large language model deployment for text generation |
| GPT-Image-1.5 | `gpt-image-1.5` | Image generation model deployment |

### External

| Component | Resource Name | Description |
|-----------|---------------|-------------|
| MCP Server | `learn.microsoft.com` | External MCP server providing access to Microsoft Learn documentation |

## Data Flow Summary

```
Developer --push--> GitHub Repository --trigger--> GitHub Actions
                                                          |
                                         az acr build --> ACR (crtechpulseprod)
                                         az containerapp update -->
                                                          |
                                              Container App (ca-techpulse-prod)
                                              FastAPI + React SPA
                                                    |         |
                                              pull from ACR   |
                                                              |
                               +------------------------------+-------------------------------+
                               |                |              |              |                |
                          Cosmos DB      Vector Store    AI Search      App Insights     Responses API
                                                        (Foundry IQ)     (OTel)              |
                                                                                     AI Foundry + Project
                                                                                        |        |
                                                                                  Bing Grounding  Content Safety
                                                                                        |
                                                                                 gpt-5.2  gpt-image-1.5
                                                                                        |
                                                                                   MCP Server
                                                                              (learn.microsoft.com)
```

## Key Architectural Decisions

- Containerized deployment using Azure Container Apps for serverless scaling with FastAPI + React SPA bundled in a single container
- Azure Container Registry (ACR) for private container image storage with `az acr build` for cloud-native builds
- GitHub Actions for CI/CD with integrated security scanning, direct ACR build, and Container App deployment via `az containerapp update`
- OpenTelemetry (OTel) for distributed tracing and observability, forwarded to Application Insights
- Azure AI Foundry as the central AI orchestration layer, accessed via the Responses API
- Multi-model strategy with GPT-5.2 for text generation and GPT-Image-1.5 for image generation
- Bing Grounding for web-augmented AI responses and Content Safety for moderation
- Cosmos DB for scalable NoSQL data persistence alongside a dedicated Vector Store for embedding-based retrieval
- AI Search (Foundry IQ) for intelligent search and retrieval-augmented generation (RAG)
- MCP Server integration with learn.microsoft.com for external documentation access
