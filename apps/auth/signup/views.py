from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, throttling
from rest_framework_simplejwt.tokens import RefreshToken
from apps.auth.signup.serializers import SignupSerializer


class ScopedThrottle(throttling.ScopedRateThrottle):
    scope = None


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {"access": str(refresh.access_token), "refresh": str(refresh)}, status=201
        )
