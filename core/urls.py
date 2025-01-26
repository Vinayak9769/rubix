from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    TeamViewSet,
    InvitationViewSet,
    HackathonViewSet,
    UserDashboardAPIView,
    HackathonDetailAPIView,
    ProjectViewSet,
    RunReactProjectAPIView,
    home_view,
)
from .interviews import InterviewQuestionAPIView, BulkScoringAPIView
from .github import calculate_github_score
main_router = DefaultRouter()
main_router.register(r'teams', TeamViewSet, basename='team')
main_router.register(r'invitations', InvitationViewSet, basename='invitation')
main_router.register(r'hackathons', HackathonViewSet, basename='hackathon')

projects_router = DefaultRouter()
projects_router.register(r'projects', ProjectViewSet, basename='project')

urlpatterns = [
    path('', include(main_router.urls)),
    path('hackathons/<int:hackathon_id>/', include(projects_router.urls)),
    path('interview/questions/', InterviewQuestionAPIView.as_view(), name='interview-questions'),
    path('interview/', BulkScoringAPIView.as_view(), name='bulk-scoring'),
    path('dashboard/', UserDashboardAPIView.as_view(), name='user-dashboard'),
    path('hackathon/<int:hackathon_id>/dashboard/', HackathonDetailAPIView.as_view(), name='hackathon-dashboard'),
    path("run/", RunReactProjectAPIView.as_view(), name="run_project"),
    path("home/", home_view, name="home"),
]
urlpatterns += [
    path('github-score/<str:username>/', calculate_github_score),
]