import os
import json
import re

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

# Postman Collection structure
postman_collection = {
    "info": {
        "_postman_id": "YOUR_POSTMAN_COLLECTION_ID",
        "name": "CBaaS API Collection",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "item": [],
    "event": [
        {
            "listen": "prerequest",
            "script": {
                "type": "text/javascript",
                "exec": [
                    "// Add your pre-request script here, e.g., for authentication",
                    "// pm.environment.set(\"jwt_token\", \"YOUR_JWT_TOKEN\");"
                ]
            }
        },
        {
            "listen": "test",
            "script": {
                "type": "text/javascript",
                "exec": [
                    "// Add your test script here"
                ]
            }
        }
    ]
}

def create_postman_request(name, method, url_path, body=None, headers=None):
    request_item = {
        "name": name,
        "request": {
            "method": method,
            "header": [],
            "url": {
                "raw": f"{{{{base_url}}}}{url_path}",
                "host": ["{{base_url}}"],
                "path": url_path.split('/'),
            },
            "description": f"Request for {name}",
        },
        "response": [],
    }

    if headers:
        for key, value in headers.items():
            request_item["request"]["header"].append({"key": key, "value": value})
    
    # Add default Content-Type for POST/PUT/PATCH if a body is present and not explicitly set
    if method in ["POST", "PUT", "PATCH"] and body and not any(h.get("key", "").lower() == "content-type" for h in request_item["request"]["header"]):
        request_item["request"]["header"].append({"key": "Content-Type", "value": "application/json"})

    if body:
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
        "/keys",
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)
add_endpoint(
    "api_keys",
    "API Keys",
    create_postman_request(
        "Create API Key",
        "POST",
        "/keys",
        body={"name": "My New API Key", "quota": 1000, "scope": "FULL"},
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)
add_endpoint(
    "api_keys",
    "API Keys",
    create_postman_request(
        "Revoke API Key",
        "PATCH",
        "/keys/:pk/revoke",
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)
add_endpoint(
    "api_keys",
    "API Keys",
    create_postman_request(
        "Delete API Key",
        "DELETE",
        "/keys/:pk",
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)

# --- apps/auth/signup ---
add_endpoint(
    "auth",
    "Auth - Signup",
    create_postman_request(
        "Signup User",
        "POST",
        "/auth/signup",
        body={"email": "user@example.com", "password": "password123", "name": "Test User", "organization_name": "Test Org"},
        headers={"Content-Type": "application/json"}
    )
)

# --- apps/auth/login ---
add_endpoint(
    "auth",
    "Auth - Login",
    create_postman_request(
        "Login User",
        "POST",
        "/auth/login",
        body={"email": "user@example.com", "password": "password123"},
        headers={"Content-Type": "application/json"}
    )
)

# --- apps/auth/logout ---
add_endpoint(
    "auth",
    "Auth - Logout",
    create_postman_request(
        "Logout User",
        "POST",
        "/auth/logout",
        body={"refresh": "{{refresh_token}}"},
        headers={"Authorization": "Bearer {{jwt_token}}", "Content-Type": "application/json"}
    )
)

# --- apps/auth/reset ---
add_endpoint(
    "auth",
    "Auth - Reset Password",
    create_postman_request(
        "Forgot Password",
        "POST",
        "/auth/forgot-password",
        body={"email": "user@example.com"},
        headers={"Content-Type": "application/json"}
    )
)
add_endpoint(
    "auth",
    "Auth - Reset Password",
    create_postman_request(
        "Verify Reset Token",
        "POST",
        "/auth/verify-reset-token",
        body={"email": "user@example.com", "token": "YOUR_RESET_TOKEN"},
        headers={"Content-Type": "application/json"}
    )
)
add_endpoint(
    "auth",
    "Auth - Reset Password",
    create_postman_request(
        "Reset Password",
        "POST",
        "/auth/reset-password",
        body={"email": "user@example.com", "token": "YOUR_RESET_TOKEN", "new_password": "newpassword123"},
        headers={"Content-Type": "application/json"}
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
            "messages": [{"role": "user", "content": "Hello, how are you?"}],
            "max_tokens": 512,
            "temperature": 0.2,
            "top_k": 6
        },
        headers={"Authorization": "Bearer {{jwt_token}}", "Idempotency-Key": "{{$guid}}"}
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
            "messages": [{"role": "user", "content": "Tell me a story."}],
            "max_tokens": 512,
            "temperature": 0.2,
            "top_k": 6
        },
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)

# --- apps/chatbot ---
add_endpoint(
    "chatbot",
    "Chatbot",
    create_postman_request(
        "Get Chatbot Config",
        "GET",
        "/chatbot",
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)
add_endpoint(
    "chatbot",
    "Chatbot",
    create_postman_request(
        "Update Chatbot Config",
        "PUT",
        "/chatbot",
        body={"name": "My Custom Chatbot", "tone": "Friendly", "system_instructions": "Always be helpful."},
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)

# --- apps/chatbot_provider ---
add_endpoint(
    "chatbot_provider",
    "Chatbot Provider",
    create_postman_request(
        "Test Chatbot Provider Key",
        "POST",
        "/chatbot/test-key",
        body={"api_key": "YOUR_PROVIDER_API_KEY"},
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)
add_endpoint(
    "chatbot_provider",
    "Chatbot Provider",
    create_postman_request(
        "Upsert Chatbot Provider",
        "PUT",
        "/chatbot/provider",
        body={"provider": "openai", "model_name": "gpt-3.5-turbo", "api_key": "YOUR_PROVIDER_API_KEY"},
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)

# --- apps/documents ---
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "List Documents",
        "GET",
        "/documents",
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "Upload Document",
        "POST",
        "/documents",
        body={"name": "My Document", "file": "SELECT_FILE_FROM_DISK"}, # Postman will handle file upload via form-data
        headers={"Authorization": "Bearer {{jwt_token}}", "Content-Type": "multipart/form-data"} # Note: Postman handles multipart/form-data automatically when 'file' is present
    )
)
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "Get Document Details",
        "GET",
        "/documents/:pk",
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "Update Document",
        "PATCH",
        "/documents/:pk",
        body={"name": "Updated Document Name"},
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "Delete Document",
        "DELETE",
        "/documents/:pk",
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)
add_endpoint(
    "documents",
    "Documents",
    create_postman_request(
        "Reprocess Document",
        "POST",
        "/documents/:pk/reprocess",
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)

# --- apps/ops ---
add_endpoint(
    "ops",
    "Operational Endpoints",
    create_postman_request(
        "Health Check",
        "GET",
        "/healthz"
    )
)
add_endpoint(
    "ops",
    "Operational Endpoints",
    create_postman_request(
        "Readiness Check",
        "GET",
        "/readyz"
    )
)

# --- apps/organizations ---
add_endpoint(
    "organizations",
    "Organizations",
    create_postman_request(
        "Update Organization",
        "PUT",
        "/user/organization",
        body={"name": "My New Org Name", "logo_url": "http://example.com/logo.png"},
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)
add_endpoint(
    "organizations",
    "Organizations",
    create_postman_request(
        "Delete Organization",
        "DELETE",
        "/user/organization",
        headers={"Authorization": "Bearer {{jwt_token}}"}
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
        body={"query": "What is the capital of France?", "top_k": 5, "filters": {"document_ids": [], "file_types": ["pdf"]}},
        headers={"Authorization": "Bearer {{jwt_token}}"}
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
        headers={"Authorization": "Bearer {{jwt_token}}"}
    )
)

# Build the final Postman collection structure
for app_name, folders in api_endpoints.items():
    app_items = []
    for folder_name, requests in folders.items():
        app_items.append(create_postman_folder(folder_name, requests))
    
    # If an app has sub-folders (like auth), create a top-level folder for it
    if app_name == "auth":
        postman_collection["item"].append(create_postman_folder("Auth", app_items))
    else:
        # For other apps, just add their items directly or in a single folder if needed
        # For simplicity, I'm adding them directly to the root if they don't have sub-folders
        # or if they are already grouped by folder_name
        for folder_name, requests in folders.items():
            postman_collection["item"].append(create_postman_folder(folder_name, requests))


# Save the collection to a JSON file
output_file_path = "postman_collection.json"
with open(output_file_path, "w") as f:
    json.dump(postman_collection, f, indent=2)

print(f"Postman collection saved to {output_file_path}")
