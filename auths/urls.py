from rest_framework.routers import DefaultRouter
from django.urls import path
from auths.views import UserViewSet, user_hackathon_participation_count

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    *router.urls,
    path('hackathons/count/', user_hackathon_participation_count, name='hackathon-participation-count'),
]