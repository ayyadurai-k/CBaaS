from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from apps.users.serializers import ProfileSerializer, UpdateProfileSerializer, ProfilePictureUploadSerializer

User = get_user_model()


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user profile"""
        return Response(ProfileSerializer(request.user).data)
    
    def put(self, request):
        """Update user profile"""
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Return the updated profile using ProfileSerializer
            return Response(ProfileSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfilePictureUploadView(APIView):
    """Upload or update user profile picture"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """Upload new profile picture"""
        serializer = ProfilePictureUploadSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            # Delete old profile picture if exists
            if request.user.profile_picture:
                request.user.profile_picture.delete(save=False)
            
            serializer.save()
            # Return updated profile data
            return Response(ProfileSerializer(request.user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Remove current profile picture"""
        if request.user.profile_picture:
            request.user.profile_picture.delete(save=False)
            request.user.profile_picture = None
            request.user.save()
            return Response(ProfileSerializer(request.user).data, status=status.HTTP_200_OK)
        return Response({"detail": "No profile picture to delete"}, status=status.HTTP_404_NOT_FOUND)
