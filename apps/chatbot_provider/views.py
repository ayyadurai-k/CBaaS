from rest_framework.views import APIView
from rest_framework.response import Response
from common.security.permissions import IsOwnerOrAdmin
from apps.chatbot.models import Chatbot
from .models import ChatbotProvider
from .serializers import ProviderSerializer

class TestKeyView(APIView):
    permission_classes = [IsOwnerOrAdmin]
    def post(self, request):
        bot = Chatbot.objects.filter(organization=request.user.organization).first()
        if not bot:
            return Response({"detail": "Chatbot not configured"}, status=400)
        s = ProviderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        # (Optional) ping provider here
        return Response({"ok": True})
