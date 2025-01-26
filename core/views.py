from django.db import models
from django.core.mail import send_mail
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from .models import Hackathon, Project, ProjectPitch
from .serializers import HackathonSerializer, ProjectSerializer
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import render
from django.db.models import Q
from .models import Hackathon, Team, Invitation
from .serializers import HackathonSerializer, TeamSerializer, InvitationSerializer
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
import time
import subprocess
import os
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Team.objects.filter(hackathon__created_by=self.request.user)
        return Team.objects.filter(members=self.request.user)

    @action(detail=True, methods=['post'], url_path='shortlist', permission_classes=[IsAuthenticated])
    def shortlist_team(self, request, pk=None):
        try:
            team = Team.objects.get(id=pk)
        except Team.DoesNotExist:
            return Response({"error": "No team matches the given query."}, status=status.HTTP_404_NOT_FOUND)
        team.decision = 'shortlisted'
        team.save()
        return Response({"message": "Team shortlisted successfully!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_team(self, request, pk=None):
        try:
            team = Team.objects.get(id=pk)
        except Team.DoesNotExist:
            return Response({"error": "No team matches the given query."}, status=status.HTTP_404_NOT_FOUND)
        if team.hackathon.created_by != request.user:
            raise PermissionDenied("Only the organizer can reject teams.")
        team.decision = 'rejected'
        team.save()
        return Response({"message": "Team rejected successfully!"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='my')
    def my_team(self, request):
        hackathon_id = request.query_params.get('hackathon_id')
        if not hackathon_id:
            return Response({"error": "hackathon_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        team = Team.objects.filter(hackathon_id=hackathon_id, members=request.user).first()
        if not team:
            return Response({"error": "You are not part of any team for this hackathon"},
                            status=status.HTTP_404_NOT_FOUND)

        return Response({"team_id": team.id}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='my')
    def my_team(self, request):
        hackathon_id = request.query_params.get('hackathon_id')
        if not hackathon_id:
            return Response({"error": "hackathon_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        team = Team.objects.filter(hackathon_id=hackathon_id, members=request.user).first()
        if not team:
            return Response({"error": "You are not part of any team for this hackathon"},
                            status=status.HTTP_404_NOT_FOUND)

        return Response({"team_id": team.id}, status=status.HTTP_200_OK)

class InvitationViewSet(ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Invitation.objects.filter(models.Q(inviter=user) | models.Q(invitee=user))

    def perform_create(self, serializer):
        invitations = serializer.save()
        for invitation in invitations:
            self.send_invitation_email(invitation)

        self.created_invitations = invitations

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serialized_invitations = InvitationSerializer(self.created_invitations, many=True)
        return Response(serialized_invitations.data, status=status.HTTP_201_CREATED)

    def send_invitation_email(self, invitation):
        link = f"http://localhost:8000/api/core/invitations/{invitation.id}/accept/"

        send_mail(
            subject="You're invited to join a Hackathon!",
            message=f"Hello {invitation.invitee.first_name},\n\nYou have been invited by {invitation.inviter.first_name} to join the hackathon: {invitation.hackathon.name}. \n\nClick the following link to accept the invitation:\n{link}",
            from_email="vinayak97696@gmail.com",
            recipient_list=[invitation.invitee.email],
        )

    @action(detail=True, methods=['get'], url_path='accept', permission_classes=[AllowAny])
    def accept_invitation(self, request, pk=None):
        invitation = get_object_or_404(Invitation, pk=pk)
        if invitation.status != 'pending':
            return Response({"error": "This invitation has already been processed."}, status=status.HTTP_400_BAD_REQUEST)

        invitation.status = 'accepted'
        invitation.save()

        team = Team.objects.get(hackathon=invitation.hackathon, leader=invitation.inviter)
        team.members.add(invitation.invitee)

        return Response({"message": "Invitation accepted successfully!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='decline')
    def decline_invitation(self, request, pk=None):
        invitation = self.get_object()
        if invitation.status != 'pending':
            return Response({"error": "This invitation has already been processed."},
                            status=status.HTTP_400_BAD_REQUEST)

        invitation.decline()

        return Response({"message": "Invitation declined."}, status=status.HTTP_200_OK)


class HackathonViewSet(ModelViewSet):
    queryset = Hackathon.objects.all()
    serializer_class = HackathonSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Hackathon.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['patch'], url_path='register')
    def register_user(self, request, pk=None):
        hackathon = self.get_object()
        user = request.user
        print(request.data)
        team_name = request.data
        # if hackathon.participants.filter(id=user.id).exists():
        #     return Response({"detail": "You are already a participant."}, status=status.HTTP_400_BAD_REQUEST)

        team = Team.objects.create(hackathon=hackathon, leader=user, name=team_name)
        team.members.add(user)
        hackathon.participants.add(user)

        return Response({
            "message": "You have successfully registered for the hackathon.",
            "team": TeamSerializer(team).data
        }, status=status.HTTP_201_CREATED)
    @action(detail=True, methods=['get'], url_path='teams')
    def hackathon_teams(self, request, pk=None):
        hackathon = self.get_object()
        teams = Team.objects.filter(hackathon=hackathon)
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='me')
    def hosted_by_me(self, request):
        user = request.user
        hackathons = Hackathon.objects.filter(created_by=user)
        serializer = self.get_serializer(hackathons, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='participated')
    def participated_hackathons(self, request):
        user = request.user
        hackathons = Hackathon.objects.filter(
            models.Q(participants=user) |
            models.Q(teams__leader=user) |
            models.Q(teams__members=user)
        ).distinct()
        serializer = self.get_serializer(
            hackathons,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)



class UserDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        participating_hackathons = Hackathon.objects.filter(participants=user)
        hackathon_serializer = HackathonSerializer(participating_hackathons, many=True)
        user_teams = Team.objects.filter(members=user)
        team_serializer = TeamSerializer(user_teams, many=True)
        user_invitations = Invitation.objects.filter(
            Q(inviter=user) | Q(invitee=user)
        )
        invitation_serializer = InvitationSerializer(user_invitations, many=True)
        return Response({
            'hackathons': hackathon_serializer.data,
            'teams': team_serializer.data,
            'invitations': invitation_serializer.data
        }, status=status.HTTP_200_OK
    )

class HackathonDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, hackathon_id):
        user = request.user
        hackathon = get_object_or_404(Hackathon, id=hackathon_id)
        if not hackathon.participants.filter(id=user.id).exists():
            raise PermissionDenied("You are not a participant of this hackathon")
        hackathon_serializer = HackathonSerializer(hackathon)
        teams = Team.objects.filter(hackathon=hackathon, members=user)
        team_serializer = TeamSerializer(teams, many=True)
        invitations = Invitation.objects.filter(
            Q(hackathon=hackathon) &
            (Q(inviter=user) | Q(invitee=user))
        )
        invitation_serializer = InvitationSerializer(invitations, many=True)
        return Response({
            'hackathon': hackathon_serializer.data,
            'teams': team_serializer.data,
            'invitations': invitation_serializer.data,
            'is_organizer': hackathon.created_by == user
        }, status=status.HTTP_200_OK)


class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [AllowAny]
    queryset = Project.objects.all()

    def get_queryset(self):
        hackathon_id = self.kwargs.get('hackathon_id')
        return Project.objects.filter(hackathon_id=hackathon_id)

    def perform_create(self, serializer):
        hackathon = get_object_or_404(Hackathon, id=self.kwargs['hackathon_id'])
        team = get_object_or_404(
            Team,
            id=self.request.data.get('team'),
            hackathon=hackathon
        )

        if not team.members.filter(id=self.request.user.id).exists():
            raise PermissionDenied("You are not a member of this team")

        serializer.save(hackathon=hackathon, team=team)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # if not instance.team.members.filter(id=request.user.id).exists():
        #     return Response({"error": "You are not a member of this project's team"},
        #                     status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

from rest_framework import generics

class UserProjectsAPIView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_teams = Team.objects.filter(members=self.request.user)
        return Project.objects.filter(team__in=user_teams)



SCRIPT_DIR = os.path.join(settings.BASE_DIR, 'scripts')
REACT_SCRIPT_PATH = os.path.join(SCRIPT_DIR, 'run_react_project.sh')

class RunReactProjectAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        github_url = request.data.get("github_url")
        env = os.environ.copy()
        print(env)
        subprocess.Popen(['/home/vin/PycharmProjects/rubix/scripts/run_react_project.sh', github_url])
        time.sleep(5)
        return JsonResponse({
            "success": "ok"
        }, status=200)



def home_view(request):
    return render(request, 'chat.html')


