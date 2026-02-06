# CBaaS Common

Shared utilities package for CBaaS microservices.

## Installation

```bash
# From the packages directory
pip install -e ./cbaas_common
```

## Features

- **Events**: Domain event schemas and local event publisher
- **Auth**: JWT validation utilities
- **Models**: Pydantic DTOs for cross-service communication
- **Validators**: Common validation functions

## Usage

### Events

```python
from cbaas_common.events import EventPublisher, DocumentUploadedEvent

publisher = EventPublisher()

# Subscribe to events
@publisher.subscribe(DocumentUploadedEvent)
def handle_document_uploaded(event: DocumentUploadedEvent):
    print(f"Document {event.document_id} uploaded!")

# Publish events
publisher.publish(DocumentUploadedEvent(
    document_id="123",
    organization_id="456",
    file_name="doc.pdf",
    file_type="pdf",
    size_bytes=1024
))
```

### JWT Validation

```python
from cbaas_common.auth.jwt_utils import JWTValidator

validator = JWTValidator(secret_key="your-secret")
payload = validator.validate_token(token)
print(f"User: {payload.user_id}, Org: {payload.organization_id}")
```

### DTOs

```python
from cbaas_common.models.mixins import UserDTO, OrganizationDTO

user = UserDTO(
    email="user@example.com",
    name="John Doe",
    role="member",
    organization_id="org-123"
)
```
