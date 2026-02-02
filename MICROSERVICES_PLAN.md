# Microservices Migration Plan for CBaaS

This document outlines the strategy for decomposing the existing monolithic CBaaS (Chatbot-as-a-Service) application into a microservices architecture.

## 1. Executive Summary

The goal is to transition from a monolithic Django application to a distributed system of specialized services. This will improve scalability, fault isolation, and development velocity by allowing independent deployment and technology choices for each domain.

## 2. Proposed Architecture

We will decompose the application into three core domain services and one infrastructure service.

### 2.1 Service Boundaries

#### 1. Identity Service (The "Core")
**Responsibilities:**
- User Authentication & Authorization (JWT issuance/validation)
- User Profile Management
- Organization & Tenant Management
- API Key Management & Validation
- Role-Based Access Control (RBAC)

**Components involved:**
- `apps/auth`
- `apps/users`
- `apps/organizations`
- `apps/api_keys`

#### 2. Chat Service (The "Brain")
**Responsibilities:**
- Chatbot Configuration (Personality, Tone, Instructions)
- Chat Session Management
- Message History & Persistence
- LLM Integration (OpenAI, Gemini, DeepSeek)
- Real-time Communication (WebSockets/SSE)

**Components involved:**
- `apps/chatbot`
- `apps/chat`
- `apps/llm_providers`

#### 3. Knowledge Service (The "Memory")
**Responsibilities:**
- Document Upload & Storage (S3)
- Text Extraction (PDF, DOCX parsing)
- Chunking & Embedding Generation
- Vector Database Management (pgvector)
- Semantic Search & Retrieval

**Components involved:**
- `apps/documents`
- `apps/search`

### 2.2 Shared Infrastructure

- **API Gateway**: Entry point for all client requests. Routes traffic to appropriate services. (e.g., Nginx, Kong, or a lightweight Go/Node proxy).
- **Event Bus**: Asynchronous communication for decoupled events (e.g., "Document Uploaded" -> trigger "Embedding Generation"). RabbitMQ or Redis Pub/Sub.
- **Shared Library**: A Python package containing common utilities:
    - JWT verification middleware
    - Logging & Tracing setup
    - Error handling standards
    - Shared Pydantic models/DTOs

## 3. Technology Stack Changes

| Component | Current (Monolith) | Future (Microservices) |
| :--- | :--- | :--- |
| **Backend** | Django + DRF | Service 1: Django/FastAPI<br>Service 2: Django/FastAPI<br>Service 3: Python (FastAPI recommended for high-perf vector ops) |
| **Database** | Single PostgreSQL | Database per Service:<br>Identity: PostgreSQL (Relational)<br>Chat: PostgreSQL or NoSQL (Cassandra/Mongo for chat logs)<br>Knowledge: PostgreSQL + pgvector (or dedicated Vector DB like Qdrant/Weaviate) |
| **Communication** | Direct Function Calls | Synchronous: REST/gRPC<br>Asynchronous: RabbitMQ/Kafka |
| **Deployment** | Docker Compose (All-in-one) | Kubernetes (Helm Charts) or ECS Services |

## 4. Migration Strategy (Phased Approach)

We will use the **Strangler Fig Pattern** to incrementally replace the monolith.

### Phase 1: Modular Monolith (Preparation)
1.  **Strict Decoupling**: Refactor existing apps to remove direct model dependencies across proposed service boundaries.
    - *Example*: `Chatbot` model currently has a Foreign Key to `Organization`. Change this to store `organization_id` (UUID) only.
    - *Action*: Replace cross-app Foreign Keys with loosely coupled ID references.
2.  **Service Interface Definition**: Define clear internal APIs (Service Layer) that mimic the future external APIs.

### Phase 2: Extract Knowledge Service
The "Document/Search" domain is compute-heavy and distinct. It's the best candidate for the first extraction.
1.  Create a new repository/folder for `knowledge-service`.
2.  Move `apps/documents` and `apps/search` logic there.
3.  Set up a dedicated database for it.
4.  Expose REST endpoints for uploading and searching.
5.  Update the Monolith to call these endpoints instead of internal function calls.

### Phase 3: Extract Chat Service
1.  Create `chat-service`.
2.  Move `apps/chat`, `apps/chatbot`, `apps/llm_providers`.
3.  Implement the LLM interaction logic here.
4.  Update the Monolith to proxy chat requests to this service.

### Phase 4: Identity Service & Final Cleanup
1.  The remaining Monolith effectively becomes the `identity-service`.
2.  Refine it to focus solely on Auth/User/Org management.
3.  Deploy the API Gateway to sit in front of all three services.

## 5. Data Migration Plan

- **Foreign Keys**: As we split databases, Foreign Key constraints will be lost. We must implement application-level integrity checks.
- **Data Transfer**:
    - Use ETL scripts to move `Document` and `Embedding` data to the Knowledge Service's new DB.
    - Use ETL to move `ChatSession` and `Message` data to the Chat Service's new DB.

## 6. Development Workflow

- **Local Development**: `docker-compose.yml` will be updated to spin up multiple service containers instead of one.
- **Shared Code**: Create a private PyPI package or git submodule `cbaas-common` for shared code.

## 7. Next Steps

1.  Review and approve this plan.
2.  Begin **Phase 1: Modular Monolith** refactoring.
    - Task: Audit `backend/apps` for cross-app dependencies.
    - Task: Create `cbaas-common` library.
