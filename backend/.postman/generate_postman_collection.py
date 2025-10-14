import os
import json
import re
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

# Postman Collection structure
postman_collection = {
    "info": {
        "_postman_id": "cbaas-api-collection-2025",
        "name": "CBaaS API Collection",
        "description": "Complete API collection for CBaaS (Chatbot-as-a-Service) - Multi-tenant RAG SaaS platform\n\nGenerated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        "version": "2.0.0"
    },
    "item": [],
    "variable": [
        {
            "key": "base_url",
            "value": "http://localhost:8000/api",
            "type": "string"
        },
        {
            "key": "jwt_token",
            "value": "",
            "type": "string"
        },
        {
            "key": "refresh_token",
            "value": "",
            "type": "string"
        }
    ],
    "event": [
        {
            "listen": "prerequest",
            "script": {
                "type": "text/javascript",
                "exec": [
                    "// Auto-set authorization header if jwt_token exists",
                    "const jwtToken = pm.collectionVariables.get('jwt_token');",
                    "if (jwtToken && pm.request.headers.has('Authorization')) {",
                    "    pm.request.headers.upsert({key: 'Authorization', value: 'Bearer ' + jwtToken});",
                    "}"
                ]
            }
        },
        {
            "listen": "test",
            "script": {
                "type": "text/javascript",
                "exec": [
                    "// Auto-extract tokens from login response",
                    "if (pm.response.code === 200 && pm.request.url.path.includes('login')) {",
                    "    const jsonData = pm.response.json();",
                    "    if (jsonData.data && jsonData.data.access) {",
                    "        pm.collectionVariables.set('jwt_token', jsonData.data.access);",
                    "        pm.collectionVariables.set('refresh_token', jsonData.data.refresh);",
                    "        console.log('✓ Tokens saved to collection variables');",
                    "    }",
                    "}"
                ]
            }
        }
    ]
}

def create_postman_request(name, method, url_path, body=None, headers=None, description=None, is_multipart=False):
    """
    Create a Postman request item.
    
    Args:
        name: Display name for the request
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        url_path: API endpoint path (will be appended to {{base_url}})
        body: Request body (dict for JSON, or special handling for multipart)
        headers: Dict of headers to include
        description: Detailed description of the endpoint
        is_multipart: If True, use form-data instead of raw JSON
    """
    # Ensure url_path starts with /
    if not url_path.startswith('/'):
        url_path = '/' + url_path
    
    # Split path into segments for Postman URL structure
    path_segments = [seg for seg in url_path.split('/') if seg]
    
    request_item = {
        "name": name,
        "request": {
            "method": method,
            "header": [],
            "url": {
                "raw": f"{{{{base_url}}}}{url_path}",
                "host": ["{{base_url}}"],
                "path": path_segments,
            },
            "description": description or f"Request for {name}",
        },
        "response": [],
    }

    # Add headers
    if headers:
        for key, value in headers.items():
            request_item["request"]["header"].append({
                "key": key,
                "value": value,
                "type": "text"
            })
    
    # Add default Content-Type for non-multipart requests
    if method in ["POST", "PUT", "PATCH"] and not is_multipart:
        if not any(h.get("key", "").lower() == "content-type" for h in request_item["request"]["header"]):
            request_item["request"]["header"].append({
                "key": "Content-Type",
                "value": "application/json",
                "type": "text"
            })

    # Add body
    if body:
        if is_multipart:
            # For file uploads
            request_item["request"]["body"] = {
                "mode": "formdata",
                "formdata": []
            }
            for key, value in body.items():
                if key == "file":
                    request_item["request"]["body"]["formdata"].append({
                        "key": key,
                        "type": "file",
                        "src": []
                    })
                else:
                    request_item["request"]["body"]["formdata"].append({
                        "key": key,
                        "value": value,
                        "type": "text"
                    })
        else:
            request_item["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(body, indent=2),
                "options": {"raw": {"language": "json"}},
            }
    
    # Convert Django path parameters to Postman variables
    # e.g., <uuid:pk> to :pk
    request_item["request"]["url"]["raw"] = re.sub(r"<(\w+):(\w+)>", r":\2", request_item["request"]["url"]["raw"])
    request_item["request"]["url"]["path"] = [re.sub(r"<(\w+):(\w+)>", r":\2", p) for p in request_item["request"]["url"]["path"]]

    return request_item

def create_postman_folder(name, items):
    return {
        "name": name,
        "item": items,
    }

# --- API Endpoints Information ---
# This dictionary will store the extracted API information
# Structure: { "app_name": { "folder_name": [request_items] } }
api_endpoints = {}

# Helper to add endpoints to the structure
def add_endpoint(app_name, folder_name, request_item):
    if app_name not in api_endpoints:
        api_endpoints[app_name] = {}
    if folder_name not in api_endpoints[app_name]:
        api_endpoints[app_name][folder_name] = []
    api_endpoints[app_name][folder_name].append(request_item)

# --- apps/api_keys ---
add_endpoint(
    "api_keys",
    "API Keys",
    create_postman_request(
        "List API Keys",
        "GET",
        "/keys/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Get all API keys for the authenticated user's organization."
    )
)
add_endpoint(
    "api_keys",
    "API Keys",
    create_postman_request(
        "Create API Key",
        "POST",
        "/keys/",
        body={"name": "My New API Key", "quota": 1000, "scope": "FULL"},
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Create a new API key for programmatic access to the API."
    )
)
add_endpoint(
    "api_keys",
    "API Keys",
    create_postman_request(
        "Revoke API Key",
        "PATCH",
        "/keys/<uuid:pk>/revoke/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Revoke an API key to prevent further use without deleting it."
    )
)
add_endpoint(
    "api_keys",
    "API Keys",
    create_postman_request(
        "Delete API Key",
        "DELETE",
        "/keys/<uuid:pk>/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Permanently delete an API key."
    )
)

# --- apps/auth/signup ---
add_endpoint(
    "auth",
    "Auth - Signup",
    create_postman_request(
        "Signup User",
        "POST",
        "/auth/signup/",
        body={
            "email": "user@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "name": "Test User",
            "phone_number": "+1234567890",
            "organization_name": "Test Org"
        },
        description="Create a new user account with organization. Password must be at least 8 characters and match confirm_password."
    )
)

# --- apps/auth/login ---
add_endpoint(
    "auth",
    "Auth - Login",
    create_postman_request(
        "Login User",
        "POST",
        "/auth/login/",
        body={"email": "user@example.com", "password": "password123"},
        description="Authenticate user and receive JWT access and refresh tokens. Tokens are auto-saved to collection variables."
    )
)
add_endpoint(
    "auth",
    "Auth - Login",
    create_postman_request(
        "Refresh Token",
        "POST",
        "/auth/token/refresh/",
        body={"refresh": "{{refresh_token}}"},
        description="Refresh an expired access token using the refresh token."
    )
)

# --- apps/auth/logout ---
add_endpoint(
    "auth",
    "Auth - Logout",
    create_postman_request(
        "Logout User",
        "POST",
        "/auth/logout/",
        body={"refresh": "{{refresh_token}}"},
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Logout user and blacklist the refresh token. Requires authentication."
    )
)

# --- apps/auth/reset ---
add_endpoint(
    "auth",
    "Auth - Reset Password",
    create_postman_request(
        "Forgot Password",
        "POST",
        "/auth/forgot-password/",
        body={"email": "user@example.com"},
        description="Request a password reset token to be sent to the user's email."
    )
)
add_endpoint(
    "auth",
    "Auth - Reset Password",
    create_postman_request(
        "Verify Reset Token",
        "POST",
        "/auth/verify-reset-token/",
        body={"email": "user@example.com", "token": "YOUR_RESET_TOKEN"},
        description="Verify that a password reset token is valid before allowing password change."
    )
)
add_endpoint(
    "auth",
    "Auth - Reset Password",
    create_postman_request(
        "Reset Password",
        "POST",
        "/auth/reset-password/",
        body={"email": "user@example.com", "token": "YOUR_RESET_TOKEN", "new_password": "newpassword123"},
        description="Complete password reset with verified token and new password."
    )
)

# --- apps/auth/status ---
add_endpoint(
    "auth",
    "Auth - Status",
    create_postman_request(
        "Check Auth Status",
        "GET",
        "/auth/status/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Verify if the current JWT token is valid and get user info."
    )
)

# --- apps/chat ---
add_endpoint(
    "chat",
    "Chat",
    create_postman_request(
        "Chat Completions",
        "POST",
        "/chat/completions",
        body={
            "session_id": None,
            "messages": [{"role": "user", "content": "Hello, how are you?"}],
            "max_tokens": 512,
            "temperature": 0.2,
            "top_k": 6,
            "filters": {"document_ids": [], "file_types": []},
            "metadata": {}
        },
        headers={"Authorization": "Bearer {{jwt_token}}", "Idempotency-Key": "{{$guid}}"},
        description="Send a chat message and get RAG-enhanced response. Supports document filtering and session management. Max 40 messages, 8000 chars per message, 20000 total chars."
    )
)
add_endpoint(
    "chat",
    "Chat",
    create_postman_request(
        "Chat Stream",
        "POST",
        "/chat/stream",
        body={
            "session_id": None,
            "messages": [{"role": "user", "content": "Tell me a story."}],
            "max_tokens": 512,
            "temperature": 0.2,
            "top_k": 6,
            "filters": {"document_ids": []},
            "metadata": {}
        },
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Stream chat responses in real-time using Server-Sent Events (SSE)."
    )
)

# --- apps/chatbot ---
add_endpoint(
    "chatbot",
    "Chatbot Configuration",
    create_postman_request(
        "Get Chatbot Config",
        "GET",
        "/chatbot",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Get the chatbot configuration including LLM provider, model, and system instructions."
    )
)
add_endpoint(
    "chatbot",
    "Chatbot Configuration",
    create_postman_request(
        "Update Chatbot Config",
        "PUT",
        "/chatbot",
        body={
            "name": "My Custom Chatbot",
            "tone": "Friendly",
            "system_instructions": "Always be helpful.",
            "llm_provider": "openai",
            "llm_model": "gpt-3.5-turbo",
            "llm_api_key": "sk-...",
            "llm_system_prompt": "You are a helpful assistant.",
            "llm_is_active": True,
            "documents_connected": []
        },
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Update chatbot configuration. API key is encrypted on save. Use documents_connected to link specific documents."
    )
)
add_endpoint(
    "chatbot",
    "Chatbot Configuration",
    create_postman_request(
        "Test LLM Provider API Key",
        "POST",
        "/chatbot/test-api-key",
        body={
            "api_key": "YOUR_PROVIDER_API_KEY",
            "provider": "openai",
            "model_name": "gpt-3.5-turbo"
        },
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Test if an LLM provider API key is valid before saving it to config. Supports: openai, gemini, deepseek."
    )
)
add_endpoint(
    "chatbot",
    "Chatbot Configuration",
    create_postman_request(
        "Send Chatbot Message",
        "POST",
        "/chatbot/message",
        body={
            "message": "What services do you offer?",
            "session_id": None
        },
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Send a message directly to the chatbot using the organization's configured LLM and RAG settings."
    )
)

# --- apps/documents ---
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "List Documents",
        "GET",
        "/documents/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Get all documents for the authenticated user's organization. Includes metadata and processing status."
    )
)
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "Upload Document",
        "POST",
        "/documents/",
        body={"name": "My Document", "file": None},
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Upload a document for RAG processing. Supports PDF, DOCX, TXT, etc. File is processed async via Celery (chunking + embeddings).",
        is_multipart=True
    )
)
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "Get Document Details",
        "GET",
        "/documents/<uuid:pk>/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Get detailed information about a specific document including chunks and processing status."
    )
)
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "Update Document",
        "PATCH",
        "/documents/<uuid:pk>/",
        body={"name": "Updated Document Name"},
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Update document metadata (name, etc.). Does not reprocess the file."
    )
)
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "Delete Document",
        "DELETE",
        "/documents/<uuid:pk>/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Permanently delete a document and all associated chunks/embeddings."
    )
)
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "Download Document",
        "GET",
        "/documents/<uuid:pk>/download/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Download the original document file. Returns file from S3 (prod) or local storage (dev)."
    )
)
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "Reprocess Document",
        "POST",
        "/documents/<uuid:pk>/reprocess/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Trigger reprocessing of a document (re-chunk and regenerate embeddings). Useful after embedding model changes."
    )
)

# --- apps/llm_providers ---
add_endpoint(
    "llm_providers",
    "LLM Providers",
    create_postman_request(
        "List LLM Providers",
        "GET",
        "/providers/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Get all available LLM providers with their models and capabilities."
    )
)
add_endpoint(
    "llm_providers",
    "LLM Providers",
    create_postman_request(
        "List Providers (Simple)",
        "GET",
        "/providers/simple/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Get simplified provider list for dropdown/select components (frontend-friendly)."
    )
)
add_endpoint(
    "llm_providers",
    "LLM Providers",
    create_postman_request(
        "Get Provider Models",
        "GET",
        "/providers/<str:provider_name>/models/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Get all available models for a specific provider (e.g., 'openai', 'gemini', 'deepseek')."
    )
)
add_endpoint(
    "llm_providers",
    "LLM Providers",
    create_postman_request(
        "Get Provider Config",
        "GET",
        "/providers/config/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Get frontend-compatible provider configuration (matches old hardcoded structure for backwards compatibility)."
    )
)
add_endpoint(
    "llm_providers",
    "LLM Providers",
    create_postman_request(
        "Get Model Details",
        "GET",
        "/providers/<str:provider_name>/models/<str:model_name>/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Get detailed information about a specific model including context length, capabilities, and pricing."
    )
)
add_endpoint(
    "llm_providers",
    "LLM Providers",
    create_postman_request(
        "Clear Provider Cache",
        "POST",
        "/providers/cache/clear/",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Clear the cached provider data (admin only). Forces refresh from LiteLLM on next request."
    )
)

# --- apps/ops ---
add_endpoint(
    "ops",
    "Operational Endpoints",
    create_postman_request(
        "Health Check",
        "GET",
        "/healthz",
        description="Basic health check endpoint. Returns 200 if service is running. Used by load balancers."
    )
)
add_endpoint(
    "ops",
    "Operational Endpoints",
    create_postman_request(
        "Readiness Check",
        "GET",
        "/readyz",
        description="Readiness probe. Checks DB connectivity and critical dependencies. Used by Kubernetes/ECS."
    )
)
add_endpoint(
    "ops",
    "Operational Endpoints",
    create_postman_request(
        "Static Files Debug",
        "GET",
        "/debug/static",
        description="Debug endpoint to check static files configuration (SERVE_STATIC_FILES, storage backends, etc.)."
    )
)

# --- apps/organizations ---
add_endpoint(
    "organizations",
    "Organizations",
    create_postman_request(
        "Get Organization",
        "GET",
        "/user/organization",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Get the current user's organization details including name, logo, and settings."
    )
)
add_endpoint(
    "organizations",
    "Organizations",
    create_postman_request(
        "Update Organization",
        "PUT",
        "/user/organization",
        body={"name": "My New Org Name"},
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Update organization information (name, settings). Only organization owners can update."
    )
)
add_endpoint(
    "organizations",
    "Organizations",
    create_postman_request(
        "Update Organization",
        "PATCH",
        "/user/organization",
        body={"name": "My New Org Name"},
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Partial update of organization information."
    )
)
add_endpoint(
    "organizations",
    "Organizations",
    create_postman_request(
        "Delete Organization",
        "DELETE",
        "/user/organization",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Delete the organization and all associated data (users, documents, chatbot config). Cannot be undone."
    )
)
add_endpoint(
    "organizations",
    "Organizations",
    create_postman_request(
        "Upload Organization Logo",
        "POST",
        "/user/organization/logo",
        body={"logo": None},
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Upload or update the organization logo. Stored in S3 (prod) or local media folder (dev).",
        is_multipart=True
    )
)

# --- apps/search ---
add_endpoint(
    "search",
    "Search",
    create_postman_request(
        "Search Documents",
        "POST",
        "/search",
        body={
            "query": "What is the capital of France?",
            "top_k": 5,
            "filters": {
                "document_ids": [],
                "file_types": ["pdf"]
            }
        },
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Semantic search across document chunks using pgvector. Returns relevant chunks with similarity scores. Max top_k: 50."
    )
)

# --- apps/users ---
add_endpoint(
    "users",
    "Users",
    create_postman_request(
        "Get User Profile",
        "GET",
        "/user/profile",
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Get the authenticated user's profile including name, email, phone, role, and organization."
    )
)
add_endpoint(
    "users",
    "Users",
    create_postman_request(
        "Update User Profile",
        "PUT",
        "/user/profile",
        body={
            "name": "Updated Name",
            "phone_number": "+1234567890"
        },
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Update user profile information. Email cannot be changed."
    )
)
add_endpoint(
    "users",
    "Users",
    create_postman_request(
        "Update User Profile",
        "PATCH",
        "/user/profile",
        body={"name": "Updated Name"},
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Partial update of user profile."
    )
)
add_endpoint(
    "users",
    "Users",
    create_postman_request(
        "Upload Profile Picture",
        "POST",
        "/user/profile/picture",
        body={"picture": None},
        headers={"Authorization": "Bearer {{jwt_token}}"},
        description="Upload or update user profile picture. Stored in S3 (prod) or local media folder (dev).",
        is_multipart=True
    )
)

# Build the final Postman collection structure
# Apps with multiple sub-folders get grouped together
grouped_apps = ["auth"]

# Order for the main collection items (for better UX)
app_order = [
    "auth",
    "users", 
    "organizations",
    "chatbot",
    "llm_providers",
    "documents",
    "search",
    "chat",
    "api_keys",
    "ops"
]

# Build collection in defined order
for app_name in app_order:
    if app_name not in api_endpoints:
        continue
        
    folders = api_endpoints[app_name]
    
    # Apps with multiple sub-folders get grouped under a main folder
    if app_name in grouped_apps:
        app_items = []
        for folder_name, requests in folders.items():
            app_items.append(create_postman_folder(folder_name, requests))
        
        # Capitalize app name for display
        display_name = app_name.replace("_", " ").title()
        postman_collection["item"].append(create_postman_folder(display_name, app_items))
    else:
        # For single-folder apps, add directly to root
        for folder_name, requests in folders.items():
            postman_collection["item"].append(create_postman_folder(folder_name, requests))

# Add any remaining apps not in the predefined order
for app_name, folders in api_endpoints.items():
    if app_name not in app_order:
        for folder_name, requests in folders.items():
            postman_collection["item"].append(create_postman_folder(folder_name, requests))

# Save the collection to a JSON file
output_file_path = "postman_collection.json"
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, output_file_path)

with open(output_path, "w", encoding='utf-8') as f:
    json.dump(postman_collection, f, indent=2, ensure_ascii=False)

print(f"✓ Postman collection generated successfully!")
print(f"  Location: {output_path}")
print(f"  Total endpoints: {sum(len(requests) for folders in api_endpoints.values() for requests in folders.values())}")
print(f"  Apps covered: {len(api_endpoints)}")
print(f"\nTo use:")
print(f"  1. Import '{output_file_path}' into Postman")
print(f"  2. Set collection variables (base_url, jwt_token, refresh_token)")
print(f"  3. Run 'Login User' to auto-populate tokens")
print(f"  4. Other requests will use tokens automatically")
