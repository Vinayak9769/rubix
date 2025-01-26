from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from auths.serializers import UserSerializer
from rest_framework.decorators import action
import json
from rest_framework import status
from .models import CustomUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from core.models import Hackathon


class UserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'me', 'me_partial_update']:
            return [AllowAny()]
        elif self.action in ['create']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return CustomUser.objects.all()

    @action(detail=False, methods=['patch'], url_path='me')
    def me_partial_update(self, request):
        instance = request.user
        profile_data = request.data.get('profile')

        if profile_data:
            profile_data = json.loads(profile_data)
            profile_data.pop('skills', None)
            serializer = self.get_serializer(instance, data=profile_data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return Response({"error": "Profile data not provided"}, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=False, methods=['get'], url_path='me/get')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_hackathon_participation_count(request):
    print("ok")
    user = request.user
    participation_count = Hackathon.objects.filter(participants=user).count()
    return Response({'participation_count': participation_count})