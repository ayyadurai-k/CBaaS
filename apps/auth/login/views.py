from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, throttling, serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class ScopedThrottle(throttling.ScopedRateThrottle):
    scope = None

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])
        if not user or not user.is_active:
            raise serializers.ValidationError("Invalid credentials")
        data["user"] = user
        return data

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedThrottle]
    throttle_scope = "login"
    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})