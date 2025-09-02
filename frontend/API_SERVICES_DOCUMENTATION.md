# CBaaS Frontend APIs and Services

This document provides an overview of all the APIs and Services created for the CBaaS project, following the backend app structure.

## Project Structure

```
frontend/src/
├── apis/                          # API Layer - Direct backend communication
│   ├── auth/                      # Auth APIs grouped together
│   │   ├── LoginAPI.ts
│   │   ├── LogoutAPI.ts
│   │   ├── ResetAPI.ts
│   │   └── SignupAPI.ts
│   ├── configs/                   # Configuration files
│   │   └── axiosConfig.ts
│   ├── ApiKeysAPI.ts              # API Keys management
│   ├── ChatAPI.ts                 # Chat functionality
│   ├── ChatbotAPI.ts              # Chatbot configuration
│   ├── ChatbotProviderAPI.ts      # AI provider integration
│   ├── DocumentsAPI.ts            # Document management
│   ├── OpsAPI.ts                  # Operations (health checks)
│   ├── OrganizationsAPI.ts        # Organization management
│   ├── SearchAPI.ts               # Semantic search
│   ├── UsersAPI.ts                # User profile management
│   └── index.ts                   # Exports all APIs
│
└── services/                      # Service Layer - Business logic & data transformation
    ├── auth/                      # Auth service grouped
    │   └── AuthService.ts
    ├── ApiKeysService.ts          # API Keys business logic
    ├── ChatbotProviderService.ts  # Provider business logic
    ├── ChatbotService.ts          # Chatbot business logic
    ├── ChatService.ts             # Chat business logic
    ├── DocumentsService.ts        # Documents business logic
    ├── OrganizationsService.ts    # Organizations business logic
    ├── SearchService.ts           # Search business logic
    ├── UsersService.ts            # Users business logic
    └── index.ts                   # Exports all services
```

## API Modules

### 1. API Keys (`/apis/api_keys/`)
**Endpoints:**
- `GET /keys/` - List all API keys
- `POST /keys/` - Create new API key
- `POST /keys/{id}/revoke/` - Revoke API key
- `DELETE /keys/{id}/` - Delete API key

**Types:**
- `APIKeyDTO`, `CreateAPIKeyPayload`
- Status: `active` | `revoked`
- Scope: `full-access` | `read-only` | `upload-only`

### 2. Authentication (`/apis/auth/`)

#### Login (`/auth/login/`)
- `POST /auth/login/` - User login
- `POST /auth/token/refresh/` - Refresh access token

#### Signup (`/auth/signup/`)
- `POST /auth/signup/` - User registration

#### Logout (`/auth/logout/`)
- `POST /auth/logout/` - User logout

#### Reset (`/auth/reset/`)
- `POST /auth/forgot-password/` - Request password reset
- `POST /auth/verify-reset-token/` - Verify reset token
- `POST /auth/reset-password/` - Reset password

### 3. Organizations (`/apis/organizations/`)
**Endpoints:**
- `GET /user/organization/` - Get user's organization
- `PUT /user/organization/` - Update organization

### 4. Users (`/apis/users/`)
**Endpoints:**
- `GET /user/profile/` - Get user profile
- `PUT /user/profile/` - Update user profile

### 5. Documents (`/apis/documents/`)
**Endpoints:**
- `GET /documents/` - List documents
- `GET /documents/{id}/` - Get document by ID
- `POST /documents/` - Upload document (multipart/form-data)
- `POST /documents/{id}/reprocess/` - Reprocess document
- `DELETE /documents/{id}/` - Delete document

**File Types:** `pdf` | `docx` | `txt` | `md` | `csv`
**Status:** `processing` | `ready` | `failed`

### 6. Chatbot (`/apis/chatbot/`)
**Endpoints:**
- `GET /chatbot/` - Get chatbot configuration
- `POST /chatbot/` - Create chatbot
- `PUT /chatbot/` - Update chatbot
- `DELETE /chatbot/` - Delete chatbot

**Tones:** `Friendly` | `Technical` | `Formal`

### 7. Chatbot Provider (`/apis/chatbot_provider/`)
**Endpoints:**
- `GET /chatbot/provider/` - Get provider configuration
- `POST /chatbot/provider/` - Upsert provider configuration
- `POST /chatbot/test-key/` - Test API key validity

**Providers:** `openai` | `gemini` | `deepseek`

### 8. Search (`/apis/search/`)
**Endpoints:**
- `POST /search/` - Semantic search across documents

### 9. Chat (`/apis/chat/`)
**Endpoints:**
- `POST /chat/completions/` - Chat completions
- `POST /chat/stream/` - Streaming chat (SSE)

### 10. Operations (`/apis/ops/`)
**Endpoints:**
- `GET /healthz/` - Health check
- `GET /readyz/` - Readiness check

## Service Layer Features

### Enhanced Data Transformation
- **Date Normalization**: Converts ISO strings to Date objects
- **Computed Properties**: Adds derived fields (e.g., `full_name`, `size_formatted`)
- **Status Helpers**: Boolean flags for state checking (e.g., `is_processing`, `is_ready`)

### Business Logic
- **File Size Formatting**: Human-readable file sizes
- **Search Result Enhancement**: Similarity percentages, content previews
- **Error Handling**: Consistent error handling with user-friendly messages
- **Authentication Flow**: Token management, refresh logic

### Singleton Pattern
All services use singleton instances for app-wide usage:
```typescript
import { documentsService, authService } from '../services';

// Usage
const documents = await documentsService.list();
const loginResult = await authService.login({ email, password });
```

## Key Features

### 1. Type Safety
- Full TypeScript support with proper type definitions
- Separate types for DTOs, payloads, and domain models

### 2. Error Handling
- Consistent error handling across all APIs
- User-friendly error messages
- Proper HTTP status code handling

### 3. Authentication Integration
- Uses the robust API client from `lib/api.ts`
- Automatic token refresh
- Request/response interceptors

### 4. Environment Configuration
- Uses Vite environment variables (`VITE_API_BASE_URL`)
- Proper fallbacks for development

### 5. Stream Support
- Real-time chat streaming with SSE
- Async generators for streaming data

## Usage Examples

### API Layer (Raw backend communication)
```typescript
import { DocumentsAPI, ChatAPI } from '../apis';

// Upload document
const response = await DocumentsAPI.upload({ name: 'doc.pdf', file });

// Send chat message
const completion = await ChatAPI.completions({ messages });
```

### Service Layer (Recommended for components)
```typescript
import { documentsService, chatService } from '../services';

// Upload and get normalized document
const document = await documentsService.upload({ name: 'doc.pdf', file });
console.log(document.size_formatted); // "2.5 MB"
console.log(document.is_ready); // boolean

// Send chat message
const message = await chatService.sendMessage(messages);
```

### Import Examples
```typescript
// Import specific APIs
import { ApiKeysAPI } from '../apis/ApiKeysAPI';
import { LoginAPI, SignupAPI } from '../apis/auth/LoginAPI';

// Import specific services
import { apiKeysService } from '../services/ApiKeysService';
import { authService } from '../services/auth/AuthService';

// Import everything
import { DocumentsAPI, ChatAPI, SearchAPI } from '../apis';
import { documentsService, chatService, searchService } from '../services';
```

This simplified structure provides cleaner imports and better organization while keeping related auth functionality grouped together. Single-file modules are easier to locate and maintain.
