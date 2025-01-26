from .models import Team
from .models import Invitation, Hackathon, Project
from auths.models import CustomUser
from rest_framework import serializers
from .models import ProjectPitch
from rest_framework import serializers
from .models import Hackathon
from django.utils import timezone

class TeamMemberSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='full_name')
    role = serializers.SerializerMethodField()
    githubLink = serializers.URLField(source='github')
    resumeLink = serializers.FileField(source='resume')
    githubScore = serializers.IntegerField(source='github_score', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['name', 'role', 'githubLink', 'resumeLink', 'githubScore']

    def get_role(self, obj):
        return "Member"

class TeamSerializer(serializers.ModelSerializer):
    teamName = serializers.CharField(source='name')
    teamLead = serializers.SerializerMethodField()
    members = TeamMemberSerializer(
        many=True,
        source='members.exclude',
        read_only=True
    )
    domainPreference = serializers.SerializerMethodField()
    status = serializers.CharField(source='decision')

    class Meta:
        model = Team
        fields = [
            'id',
            'teamName',
            'teamLead',
            'members',
            'domainPreference',
            'status',
            'interview_score'
        ]

    def get_teamLead(self, obj):
        return {
            'name': obj.leader.full_name,
            'role': 'Team Lead',
            'githubLink': obj.leader.github,
            'resumeLink': obj.leader.resume.url if obj.leader.resume else None,
            'githubScore' : obj.leader.github_score
        }

    def get_members(self, obj):
        return obj.members.exclude(id=obj.leader.id)

    def get_domainPreference(self, obj):
        try:
            return obj.projects.first().domain
        except AttributeError:
            return None

class InvitationSerializer(serializers.ModelSerializer):
    invitee = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = Invitation
        fields = ['id', 'hackathon', 'inviter', 'invitee', 'status', 'uid']
        read_only_fields = ['uid', 'status', 'inviter']

    def validate(self, data):
        hackathon = data['hackathon']
        invitees = data['invitee']
        for invitee in invitees:
            if Team.objects.filter(hackathon=hackathon, members=invitee).exists():
                raise serializers.ValidationError(f"The user with ID {invitee} is already part of a team in this hackathon.")
        return data

    def create(self, validated_data):
        inviter = self.context['request'].user
        hackathon = validated_data['hackathon']
        invitees = validated_data.pop('invitee')
        invitations = []
        for invitee_id in invitees:
            invitation = Invitation.objects.create(
                hackathon=hackathon,
                inviter=inviter,
                invitee_id=invitee_id
            )
            invitations.append(invitation)
        return invitations




class HackathonSerializer(serializers.ModelSerializer):
    # members = serializers.SerializerMethodField()
    hackathonName = serializers.CharField(source='name')
    about = serializers.CharField(source='description')
    prizePool = serializers.IntegerField(source='prize_pool')
    collegeName = serializers.CharField(source='college_name')
    minMembers = serializers.IntegerField(source='min_members')
    maxMembers = serializers.IntegerField(source='max_members')
    totalParticipants = serializers.IntegerField(source='total_participants')
    hackathonWebsite = serializers.URLField(source='website')
    applicationOpenDate = serializers.DateTimeField(source='application_open_date')
    applicationCloseDate = serializers.DateTimeField(source='application_close_date')
    hackathonBeginDate = serializers.DateTimeField(source='start_date')
    hackathonEndDate = serializers.DateTimeField(source='end_date')
    profilePhoto = serializers.ImageField(source='profile_photo')
    coverPhoto = serializers.ImageField(source='cover_photo')
    participationStatus = serializers.SerializerMethodField()
    createdByEmail = serializers.SerializerMethodField()

    class Meta:
        model = Hackathon
        fields = [
            "id",
            "hackathonName",
            "about",
            "prizePool",
            "city",
            "collegeName",
            "minMembers",
            "maxMembers",
            "totalParticipants",
            "hackathonWebsite",
            "applicationOpenDate",
            "applicationCloseDate",
            "hackathonBeginDate",
            "hackathonEndDate",
            "theme",
            "website",
            "social_links",
            "profilePhoto",
            "coverPhoto",
            "members",
            "participationStatus",
            "createdByEmail"
        ]

    def get_registration_status(self, obj):
        now = timezone.now()
        if obj.start_date <= now <= obj.end_date:
            return "open"
        return "closed"

    def get_participants_count(self, obj):
        return obj.participants.count()

    def get_createdByEmail(self, obj):
        return obj.created_by.email

    def get_members(self, obj):
        return obj.participants.all().values("name", "email", "phone")

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if self.context.get('request') and self.context['request'].method == 'GET':
            representation['registrationStatus'] = self.get_registration_status(instance)

        return representation

    def get_participationStatus(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            team = Team.objects.filter(
                hackathon=obj,
                members=request.user
            ).first()

            if team:
                return "pending" if team.decision == "none" else team.decision
        return None

class ProjectSerializer(serializers.ModelSerializer):
    teamName = serializers.CharField(source='team.name', read_only=True)
    repoLink = serializers.URLField(source='repo_link')
    liveLink = serializers.URLField(source='live_link')
    avgRating = serializers.DecimalField(
        source='avg_rating',
        max_digits=3,
        decimal_places=1,
        allow_null=True,
        required=False
    )

    class Meta:
        model = Project
        fields = [
            'id',
            'teamName',
            'domain',
            'repoLink',
            'liveLink',
            'avgRating'
        ]
        read_only_fields = ('teamName',)



class ProjectPitchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPitch
        fields = [
            'id',
            'project',
            'pitch_deck',
            'video_script',
            'documentation',
            'status',
            'generated_at',
            'video_url',
            'video_status'
        ]
        read_only_fields = [
            'id',
            'status',
            'generated_at',
            'video_url',
            'video_status'
        ]