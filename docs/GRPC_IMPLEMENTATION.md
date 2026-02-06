# gRPC Implementation Guide

> **Objective**: Enable high-performance inter-service communication for CBaaS microservices using gRPC with Django Socio gRPC.

---

## Overview

CBaaS uses [Django Socio gRPC](https://github.com/socotecio/django-socio-grpc) to integrate gRPC with Django REST Framework patterns. This provides:

- **Automatic proto generation** from Django models/serializers
- **Familiar DRF patterns** (serializers, generic views, mixins)
- **Async support** with Python 3.10+ async/await
- **Authentication** via JWT tokens in gRPC metadata

---

## Architecture

### Service Domains

| Domain | gRPC Services | Port (default) |
|--------|---------------|----------------|
| **Identity** | UserGRPCService, OrganizationGRPCService, APIKeyGRPCService | 50051 |
| **Chat** | ChatbotGRPCService | 50052 |
| **Knowledge** | DocumentGRPCService, DocumentChunkGRPCService, SearchGRPCService | 50053 |

### File Structure

```
backend/
├── common/
│   └── grpc/
│       ├── __init__.py              # Module exports
│       ├── authentication.py        # JWT + Service Account auth
│       ├── clients.py               # gRPC client utilities
│       ├── serializers/
│       │   ├── __init__.py
│       │   ├── identity.py          # User, Org, APIKey serializers
│       │   ├── chat.py              # Chatbot serializers
│       │   └── knowledge.py         # Document, Chunk, Search serializers
│       └── services/
│           ├── __init__.py
│           ├── identity.py          # Identity domain services
│           ├── chat.py              # Chat domain services
│           └── knowledge.py         # Knowledge domain services
├── config/
│   ├── grpc_handlers.py             # Service registration
│   └── environments/
│       └── base.py                  # GRPC_FRAMEWORK settings
└── grpc_generated/                  # Auto-generated proto files
    ├── __init__.py
    └── README.md
```

---

## Configuration

### Settings (config/environments/base.py)

```python
GRPC_FRAMEWORK = {
    # Root handlers hook - registers all gRPC services
    "ROOT_HANDLERS_HOOK": "config.grpc_handlers.grpc_handlers",
    
    # gRPC server port
    "GRPC_CHANNEL_PORT": int(os.environ.get("GRPC_PORT", 50051)),
    
    # Enable async gRPC
    "GRPC_ASYNC": True,
    
    # Root folder for generated proto files
    "ROOT_GRPC_FOLDER": "grpc_generated",
    
    # Authentication
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "common.grpc.authentication.JWTGRPCAuthentication",
    ],
    
    # Filtering and pagination
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    
    # Middleware
    "GRPC_MIDDLEWARE": [
        "django_socio_grpc.middlewares.log_requests_middleware",
        "django_socio_grpc.middlewares.close_old_connections_middleware",
    ],
    
    # Health check
    "ENABLE_HEALTH_CHECK": True,
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GRPC_PORT` | 50051 | gRPC server port |
| `GRPC_IDENTITY_ADDRESS` | localhost:50051 | Identity service address |
| `GRPC_CHAT_ADDRESS` | localhost:50052 | Chat service address |
| `GRPC_KNOWLEDGE_ADDRESS` | localhost:50053 | Knowledge service address |
| `GRPC_USE_TLS` | false | Enable TLS for gRPC channels |
| `GRPC_ROOT_CERT_PATH` | None | Path to root CA certificate |
| `INTERNAL_SERVICE_KEY` | None | Pre-shared key for internal service calls |

---

## Usage

### Running the gRPC Server

```bash
# Development mode (with hot reload)
python manage.py grpcrunaioserver --dev

# Production mode
python manage.py grpcrunaioserver --address [::]:50051
```

### Generating Proto Files

```bash
# Generate/update proto files from serializers and services
python manage.py generateproto

# This creates files in grpc_generated/:
# - identity_pb2.py, identity_pb2_grpc.py
# - chat_pb2.py, chat_pb2_grpc.py
# - knowledge_pb2.py, knowledge_pb2_grpc.py
```

---

## Service APIs

### Identity Service

#### UserGRPCService

| Method | Request | Response | Description |
|--------|---------|----------|-------------|
| `List` | Empty | UserListResponse | List all users |
| `Retrieve` | `{id: string}` | UserResponse | Get user by ID |
| `Create` | UserCreateRequest | UserResponse | Create new user |
| `Update` | UserUpdateRequest | UserResponse | Update user |
| `Destroy` | `{id: string}` | Empty | Delete user |
| `GetByEmail` | `{email: string}` | UserResponse | Find by email |
| `ListByOrganization` | `{organization_id: string}` | stream UserResponse | List org users |
| `Exists` | `{user_id: string}` | `{exists: bool}` | Check existence |

#### OrganizationGRPCService

| Method | Request | Response | Description |
|--------|---------|----------|-------------|
| `List` | Empty | OrganizationListResponse | List all orgs |
| `Retrieve` | `{id: string}` | OrganizationResponse | Get org by ID |
| `Create` | OrganizationCreateRequest | OrganizationResponse | Create org |
| `Update` | OrganizationUpdateRequest | OrganizationResponse | Update org |
| `GetBySlug` | `{slug: string}` | OrganizationResponse | Find by slug |
| `Exists` | `{organization_id: string}` | `{exists: bool}` | Check existence |

#### APIKeyGRPCService

| Method | Request | Response | Description |
|--------|---------|----------|-------------|
| `Validate` | `{api_key: string}` | ValidateAPIKeyResponse | Validate key |

### Chat Service

#### ChatbotGRPCService

| Method | Request | Response | Description |
|--------|---------|----------|-------------|
| `List` | Empty | ChatbotListResponse | List all chatbots |
| `Retrieve` | `{id: string}` | ChatbotResponse | Get chatbot by ID |
| `Create` | ChatbotCreateRequest | ChatbotResponse | Create chatbot |
| `Update` | ChatbotUpdateRequest | ChatbotResponse | Update chatbot |
| `Destroy` | `{id: string}` | Empty | Delete chatbot |
| `ListByOrganization` | `{organization_id: string}` | stream ChatbotResponse | List org chatbots |
| `Exists` | `{chatbot_id: string}` | ChatbotExistsResponse | Check existence |
| `ConnectDocuments` | ConnectDocumentRequest | ConnectDocumentResponse | Link documents |
| `DisconnectDocuments` | DisconnectDocumentRequest | ConnectDocumentResponse | Unlink documents |
| `ListByDocument` | `{document_id: string}` | stream ChatbotResponse | Find by document |

### Knowledge Service

#### DocumentGRPCService

| Method | Request | Response | Description |
|--------|---------|----------|-------------|
| `List` | Empty | DocumentListResponse | List all documents |
| `Retrieve` | `{id: string}` | DocumentResponse | Get document by ID |
| `Create` | DocumentCreateRequest | DocumentResponse | Create document |
| `Destroy` | `{id: string}` | Empty | Delete document |
| `ListByOrganization` | `{organization_id: string}` | stream DocumentResponse | List org documents |
| `ListByIds` | `{document_ids: repeated string}` | stream DocumentResponse | Get by IDs |
| `Exists` | `{document_id: string}` | `{exists: bool, status: string}` | Check existence |
| `TriggerProcessing` | TriggerProcessingRequest | TriggerProcessingResponse | Start processing |

#### SearchGRPCService

| Method | Request | Response | Description |
|--------|---------|----------|-------------|
| `SemanticSearch` | SemanticSearchRequest | SemanticSearchResponse | Vector search |

---

## Client Usage

### Python gRPC Client

```python
from common.grpc.clients import (
    get_identity_client,
    get_chat_client,
    get_knowledge_client,
)

# Get user from Identity service
client = get_identity_client()
user = client.get_user(user_id="uuid-here")

# Get chatbot from Chat service
client = get_chat_client()
chatbot = client.get_chatbot(chatbot_id="uuid-here")

# Semantic search via Knowledge service
client = get_knowledge_client()
results = client.semantic_search(
    query="How do I reset my password?",
    organization_id="uuid-here",
    top_k=5,
)
```

### Direct gRPC Client (after proto generation)

```python
import grpc
from grpc_generated.identity_pb2 import UserRetrieveRequest
from grpc_generated.identity_pb2_grpc import UserGRPCServiceStub

# Create channel and stub
channel = grpc.insecure_channel('localhost:50051')
stub = UserGRPCServiceStub(channel)

# Make request with metadata (JWT)
metadata = (('authorization', 'Bearer your-jwt-token'),)
request = UserRetrieveRequest(id='user-uuid')
response = stub.Retrieve(request, metadata=metadata)

print(response.email)
```

---

## Authentication

### JWT Authentication

gRPC requests include JWT tokens in metadata:

```python
# Client sends token in metadata
metadata = (('authorization', 'Bearer eyJ...'),)
stub.SomeMethod(request, metadata=metadata)
```

The `JWTGRPCAuthentication` class extracts and validates the token using SimpleJWT.

### Service Account Authentication

For internal service-to-service calls:

```python
# Service sends internal key
metadata = (('x-service-key', 'internal-service-key'),)
stub.SomeMethod(request, metadata=metadata)
```

Configure valid keys in settings:

```python
INTERNAL_SERVICE_KEYS = {
    'chat-service': 'secret-key-for-chat',
    'knowledge-service': 'secret-key-for-knowledge',
}
```

---

## Testing

### Unit Testing with FakeFullAIOGRPC

```python
from django.test import TestCase
from django_socio_grpc.test import FakeFullAIOGRPC

from common.grpc.services import UserGRPCService
from grpc_generated.identity_pb2_grpc import (
    UserGRPCServiceStub,
    add_UserGRPCServiceServicer_to_server,
)

class TestUserGRPCService(TestCase):
    def setUp(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_UserGRPCServiceServicer_to_server,
            UserGRPCService.as_servicer(),
        )
        self.stub = self.fake_grpc.get_fake_stub(UserGRPCServiceStub)
    
    async def test_list_users(self):
        response = await self.stub.List(empty_pb2.Empty())
        self.assertIsNotNone(response)
```

---

## Monitoring & Debugging

### Logging

gRPC requests are logged via `django_socio_grpc.request` logger:

```python
LOGGING = {
    "loggers": {
        "django_socio_grpc.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        }
    }
}
```

### Health Checks

Health check endpoint is enabled via `ENABLE_HEALTH_CHECK: True`:

```bash
grpcurl -plaintext localhost:50051 grpc.health.v1.Health/Check
```

---

## Migration Path

### Phase 1: Monolith (Current)

- All gRPC services run in the same process
- Clients use localhost connections
- Service interfaces fall back to direct ORM

### Phase 2: Microservices (Future)

1. Deploy each domain as separate service
2. Update environment variables for remote addresses
3. Update client classes to use generated stubs
4. Configure service mesh (Istio) for TLS and routing

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: grpc_generated` | Proto not generated | Run `python manage.py generateproto` |
| `Connection refused` | Server not running | Start with `grpcrunaioserver` |
| `UNAUTHENTICATED` | Missing/invalid token | Check JWT token in metadata |
| `NOT_FOUND` | Resource doesn't exist | Verify ID and permissions |

---

## References

- [Django Socio gRPC Documentation](https://django-socio-grpc.readthedocs.io/)
- [gRPC Python Documentation](https://grpc.io/docs/languages/python/)
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers)
