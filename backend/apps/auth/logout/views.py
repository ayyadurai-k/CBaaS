from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

class LogoutView(APIView):
    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"detail": "refresh token required"}, status=400)
        RefreshToken(token).blacklist()
        return Response(status=204)