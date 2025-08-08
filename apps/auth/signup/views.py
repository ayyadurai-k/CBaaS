from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, throttling, serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from apps.users.models import User
from apps.organizations.models import Organization

class ScopedThrottle(throttling.ScopedRateThrottle):
    scope = None

class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(max_length=100)
    organization_name = serializers.CharField(max_length=100)
    @transaction.atomic
    def create(self, validated):
        org = Organization.objects.create(name=validated["organization_name"]) 
        user = User.objects.create_user(email=validated["email"], password=validated["password"],
                                        name=validated["name"], organization=org, role=User.Role.OWNER)
        return user

class SignupView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedThrottle]
    throttle_scope = "login"
    def post(self, request):
        s = SignupSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)}, status=201)