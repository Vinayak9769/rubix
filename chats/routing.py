from django.urls import path
from .consumers import GeneralChatConsumer, TeamChatConsumer, DMConsumer, TeamFinderConsumer

websocket_urlpatterns = [
    path('ws/hackathons/<int:hackathon_id>/general/', GeneralChatConsumer.as_asgi()),
    path('ws/teams/<int:team_id>/', TeamChatConsumer.as_asgi()),
    path('ws/dm/<int:user1_id>/<int:user2_id>/', DMConsumer.as_asgi()),
    path('ws/team-finder/', TeamFinderConsumer.as_asgi()),
]
