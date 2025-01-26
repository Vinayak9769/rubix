from rest_framework.viewsets import ModelViewSet
from .models import ChatRoom
from .serializers import ChatRoomSerializer

class ChatRoomViewSet(ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
