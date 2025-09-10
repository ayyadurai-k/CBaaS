# Enhanced TestKeyView API Documentation

## Overview
The `TestKeyView` has been enhanced to actually test LLM provider API keys by making real API calls to the respective providers (OpenAI, Gemini, DeepSeek) instead of just validating the request format.

## API Endpoints

### POST /api/chatbot/test-key
Tests the provided API key by making a real call to the LLM provider.

**Request Body:**
```json
{
    "provider": "openai|gemini|deepseek",
    "model_name": "<model_name>",
    "api_key": "<api_key>"
}
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "OpenAI API key and model are working correctly",
    "details": {
        "response": "Hello",
        "usage": {
            "total_tokens": 5,
            "prompt_tokens": 3,
            "completion_tokens": 2
        },
        "model_used": "gpt-4"
    }
}
```

**Error Response (400):**
```json
{
    "success": false,
    "message": "Invalid OpenAI API key",
    "details": {
        "error": "401 Unauthorized"
    }
}
```

## Provider-Specific Testing

### OpenAI
- Tests with a simple "Hello" prompt
- Validates API key authentication
- Checks model availability
- Returns usage statistics

**Common Error Messages:**
- "Invalid OpenAI API key" - 401 Unauthorized
- "Model 'gpt-5' not found or not accessible" - Model doesn't exist
- "OpenAI quota exceeded or billing issue" - Account limitations

### Gemini
- Tests with Google's Gemini API
- Validates API key with `x-goog-api-key` header
- Checks model access permissions

**Common Error Messages:**
- "Invalid Gemini API key" - 401/403 errors
- "Gemini quota exceeded or rate limit hit" - Rate limiting
- Model not found errors

### DeepSeek
- Tests with DeepSeek's chat completion API
- Similar to OpenAI format but different endpoint
- Validates model and key combination

**Common Error Messages:**
- "Invalid DeepSeek API key" - Authentication failure
- "DeepSeek quota exceeded or billing issue" - Account issues

## Integration with Provider Upsert

The `ChatbotProviderUpsertView` now also automatically tests the provider configuration when creating or updating:

**PUT /api/chatbot/provider Response:**
```json
{
    "id": "uuid-here",
    "provider": "openai",
    "model_name": "gpt-4",
    "created_at": "2025-09-10T12:00:00Z",
    "updated_at": "2025-09-10T12:00:00Z",
    "test_result": {
        "success": true,
        "message": "OpenAI API key and model are working correctly",
        "details": {
            "response": "Hello",
            "usage": {...},
            "model_used": "gpt-4"
        }
    }
}
```

## Security Features

1. **API keys are encrypted at rest** - Never stored in plain text
2. **Minimal test prompt** - Uses simple "Hello" test to minimize token usage
3. **Timeout protection** - 30-second timeout on provider calls
4. **Permission enforcement** - Only organization owners/admins can test keys
5. **No key exposure** - API keys are never returned in responses

## Error Handling

The service provides detailed error categorization:
- **Authentication errors** - Invalid API keys
- **Authorization errors** - Model access issues  
- **Quota/billing errors** - Account limitations
- **Network errors** - Connection timeouts
- **Model errors** - Non-existent models

## Example Usage

```bash
# Test OpenAI key
curl -X POST http://localhost:8000/api/chatbot/test-key \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "provider": "openai",
    "model_name": "gpt-4",
    "api_key": "sk-your-openai-key"
  }'

# Test Gemini key  
curl -X POST http://localhost:8000/api/chatbot/test-key \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "provider": "gemini", 
    "model_name": "gemini-pro",
    "api_key": "your-gemini-key"
  }'

# Test DeepSeek key
curl -X POST http://localhost:8000/api/chatbot/test-key \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "provider": "deepseek",
    "model_name": "deepseek-chat", 
    "api_key": "your-deepseek-key"
  }'
```
