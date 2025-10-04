from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


class AuthStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Check if the user is authenticated and return user info
        """
        user = request.user
        return Response({
            "authenticated": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
            }
        }, status=status.HTTP_200_OK)
