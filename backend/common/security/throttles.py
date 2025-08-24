from rest_framework.throttling import ScopedRateThrottle

class ChatRateThrottle(ScopedRateThrottle):
    scope = "chat"

class SearchRateThrottle(ScopedRateThrottle):
    scope = "search"

class DocumentsRateThrottle(ScopedRateThrottle):
    scope = "documents"