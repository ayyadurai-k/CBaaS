# Phase 1: Modular Monolith Implementation Plan

> **Objective**: Prepare the monolith for extraction by decoupling apps and defining clear service boundaries without breaking existing functionality.

---

## 1. Cross-App Dependency Audit

### 1.1 Identify All Foreign Key Relationships

Audit each app's `models.py` to document FK relationships that cross proposed service boundaries:

| Source App | Model | FK Field | Target App | Target Model | Crosses Boundary? |
|------------|-------|----------|------------|--------------|-------------------|
| `chatbot` | `Chatbot` | `organization` | `organizations` | `Organization` | ✅ Chat → Identity |
| `chatbot` | `Chatbot` | `created_by` | `users` | `User` | ✅ Chat → Identity |
| `chat` | `ChatSession` | `chatbot` | `chatbot` | `Chatbot` | ❌ Same service |
| `chat` | `ChatSession` | `user` | `users` | `User` | ✅ Chat → Identity |
| `documents` | `Document` | `organization` | `organizations` | `Organization` | ✅ Knowledge → Identity |
| `documents` | `Document` | `chatbot` | `chatbot` | `Chatbot` | ✅ Knowledge → Chat |
| `documents` | `Document` | `uploaded_by` | `users` | `User` | ✅ Knowledge → Identity |
| `llm_providers` | `LLMProvider` | `organization` | `organizations` | `Organization` | ✅ Chat → Identity |
| `api_keys` | `APIKey` | `organization` | `organizations` | `Organization` | ❌ Same service |
| `api_keys` | `APIKey` | `created_by` | `users` | `User` | ❌ Same service |

> **Action**: Complete this table by reviewing all models in the codebase.

### 1.2 Identify Import Dependencies

Audit Python imports across apps to find:
- Direct model imports across service boundaries
- Service/utility function calls across boundaries
- Shared constants or enums

---

## 2. Decoupling Strategy

### 2.1 Replace Foreign Keys with UUID References

For each FK that crosses service boundaries:

| Current State | Target State |
|---------------|--------------|
| `organization = ForeignKey(Organization)` | `organization_id = UUIDField()` |
| `chatbot.organization.name` | Fetch via service call or cache |

**Rules**:
- Keep the FK column name but remove the FK constraint
- Add database index on UUID fields for query performance
- Document which fields are "soft references" to other services

### 2.2 Introduce Service Layer Interfaces

Create internal service classes that encapsulate cross-boundary data access:

| Service Interface | Location | Purpose |
|-------------------|----------|---------|
| `IdentityServiceInterface` | `common/services/identity.py` | Fetch user/org data |
| `ChatServiceInterface` | `common/services/chat.py` | Fetch chatbot configs |
| `KnowledgeServiceInterface` | `common/services/knowledge.py` | Trigger document processing |

**Phase 1 Implementation**: These interfaces call internal Django ORM directly. In Phase 2+, they will call external HTTP/gRPC endpoints.

### 2.3 Event-Driven Decoupling Preparation

Identify operations that should become async events:

| Current Flow | Future Event |
|--------------|--------------|
| Document upload → immediate embedding | `DocumentUploadedEvent` → Knowledge Service processes |
| User deleted → cascade delete chatbots | `UserDeletedEvent` → Chat Service cleans up |
| Org settings changed → update chatbot defaults | `OrgSettingsChangedEvent` → Chat Service updates |

**Phase 1 Implementation**: Define event schemas (Pydantic models). Emit events to local handlers. Prepare for message broker in Phase 2.

---

## 3. Shared Library (`cbaas-common`)

### 3.1 Structure

```
cbaas-common/
├── auth/
│   ├── jwt_utils.py          # JWT encode/decode/validate
│   └── permissions.py        # Permission constants, decorators
├── events/
│   ├── base.py               # BaseEvent class
│   ├── schemas.py            # Event Pydantic models
│   └── publisher.py          # Local event bus (upgradeable to RabbitMQ)
├── exceptions/
│   └── handlers.py           # Standardized error responses
├── logging/
│   └── setup.py              # Structured logging config
├── models/
│   └── mixins.py             # Shared model mixins (timestamps, UUID PK)
└── validators/
    └── common.py             # Reusable validators
```

### 3.2 Migration Tasks

1. Extract existing utilities from `backend/common/` into the new package
2. Ensure backward compatibility (import aliases in old locations)
3. Version the package with semantic versioning

---

## 4. Database Schema Changes

### 4.1 Add UUID Reference Columns

For each FK being converted:
1. Add new `*_id` UUID column (nullable initially)
2. Backfill data from existing FK
3. Remove FK constraint (keep column for rollback safety)
4. Make UUID column non-nullable
5. Add index on UUID column

### 4.2 Migration Safety

- **Reversible migrations only** - every migration must have a rollback path
- **Feature flags** - wrap new service layer calls behind flags
- **Dual-write period** - write to both old FK and new UUID during transition

---

## 5. API Contract Definition

### 5.1 Internal API Contracts

Define the API surface each service will expose:

#### Identity Service API
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/internal/users/{id}` | GET | Fetch user details |
| `/internal/users/bulk` | POST | Fetch multiple users |
| `/internal/orgs/{id}` | GET | Fetch organization |
| `/internal/orgs/{id}/members` | GET | List org members |
| `/internal/api-keys/validate` | POST | Validate API key |

#### Chat Service API
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/internal/chatbots/{id}` | GET | Fetch chatbot config |
| `/internal/chatbots/by-org/{org_id}` | GET | List org's chatbots |
| `/internal/sessions/{id}` | GET | Fetch session details |

#### Knowledge Service API
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/internal/documents/{id}` | GET | Fetch document metadata |
| `/internal/documents/search` | POST | Semantic search |
| `/internal/documents/by-chatbot/{chatbot_id}` | GET | List chatbot's documents |

### 5.2 Contract Testing Strategy

- Define OpenAPI specs for internal APIs
- Create contract tests that verify service layer matches spec
- These tests will validate external services in Phase 2+

---

## 6. Task Breakdown

### Sprint 1: Audit & Planning (1 week)

| Task | Owner | Priority | Done |
|------|-------|----------|------|
| Complete FK dependency audit table | AI | P0 | ✅ |
| Document all Python import dependencies | AI | P0 | ✅ |
| Identify high-risk coupling points | AI | P0 | ✅ |
| Finalize service boundary definitions | AI | P0 | ✅ |

### Sprint 2: Shared Library Setup (1 week)

| Task | Owner | Priority | Done |
|------|-------|----------|------|
| Create `cbaas-common` package structure | AI | P0 | ✅ |
| Extract JWT utilities | AI | P0 | ✅ |
| Extract logging setup | AI | P1 | ✅ |
| Extract exception handlers | AI | P1 | ✅ |
| Extract model mixins | AI | P1 | ✅ |
| Setup package versioning | AI | P2 | ✅ |

### Sprint 3: Service Layer Implementation (2 weeks)

| Task | Owner | Priority | Done |
|------|-------|----------|------|
| Create `IdentityServiceInterface` | AI | P0 | ✅ |
| Create `ChatServiceInterface` | AI | P0 | ✅ |
| Create `KnowledgeServiceInterface` | AI | P0 | ✅ |
| Replace direct ORM calls with service calls | AI | P0 | ✅ |
| Add feature flags for service layer | - | P1 | ☐ |

### Sprint 4: Database Decoupling (2 weeks)

| Task | Owner | Priority | Done |
|------|-------|----------|------|
| Create migration: Add UUID columns | AI | P0 | ✅ |
| Create data backfill script | N/A | P0 | ✅ (No data) |
| Create migration: Drop FK constraints | AI | P0 | ✅ |
| Update serializers for UUID fields | AI | P0 | ✅ |
| Update tests for new schema | - | P0 | ☐ |

### Sprint 5: Event System Foundation (1 week)

| Task | Owner | Priority | Done |
|------|-------|----------|------|
| Define event schemas | AI | P1 | ✅ |
| Implement local event bus | AI | P1 | ✅ |
| Add event emission points | AI | P1 | ✅ |
| Create event handler registry | AI | P1 | ✅ |

### Sprint 6: Validation & Hardening (1 week)

| Task | Owner | Priority | Done |
|------|-------|----------|------|
| Full regression testing | - | P0 | ☐ |
| Performance benchmarking | - | P1 | ☐ |
| Update API documentation | - | P1 | ☐ |
| Create rollback runbook | - | P0 | ☐ |

---

## 7. Success Criteria

### Phase 1 Complete When:

- [ ] No FK constraints exist between service boundaries
- [ ] All cross-boundary data access goes through service interfaces
- [ ] `cbaas-common` package is extracted and versioned
- [ ] Event schemas are defined for all cross-service operations
- [ ] All existing tests pass
- [ ] API response times are within 10% of baseline

---

## 8. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Data inconsistency after FK removal | High | Medium | Implement application-level integrity checks, audit logs |
| Performance degradation from service calls | Medium | Low | Cache frequently accessed data, batch requests |
| Developer confusion during transition | Medium | High | Clear documentation, feature flags, gradual rollout |
| Incomplete dependency identification | High | Medium | Automated import analysis tools, code review |

---

## 9. Rollback Plan

If critical issues are discovered:

1. **Feature flags** - Disable service layer, revert to direct ORM calls
2. **Database** - FK constraint migrations are reversible
3. **Package** - Keep import aliases in original locations for backward compatibility

---

## 10. Next Steps

1. ☐ Review and approve this plan
2. ☐ Assign owners to Sprint 1 tasks
3. ☐ Schedule kick-off meeting
4. ☐ Set up tracking board (GitHub Projects / Jira)
