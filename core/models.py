from django.db import models
from django.conf import settings
import uuid
from auths.models import CustomUser

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
CustomUser = get_user_model()

class Hackathon(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    prize_pool = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    college_name = models.CharField(max_length=255, blank=True, null=True)
    min_members = models.IntegerField(default=1)
    max_members = models.IntegerField(default=1)
    total_participants = models.IntegerField(default=1)
    website = models.URLField(blank=True, null=True)
    theme = models.CharField(max_length=255, blank=True, null=True)
    profile_photo = models.ImageField(upload_to="hackathon_profiles/", blank=True, null=True)
    cover_photo = models.ImageField(upload_to="hackathon_covers/", blank=True, null=True)
    application_open_date = models.DateTimeField(blank=True, null=True)
    application_close_date = models.DateTimeField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    members = models.JSONField(default=list)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="organized_hackathons"
    )
    participants = models.ManyToManyField(
        CustomUser, related_name="participating_hackathons", blank=True
    )
    social_links = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name



class Team(models.Model):
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='led_teams'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teams'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    decision = models.CharField(
        max_length=15,
        choices=[('pending', 'Pending'), ('shortlisted', 'Shortlisted'), ('rejected', 'Rejected')],
        default='pending'
    )
    interview_score = models.IntegerField(blank=True, null=True)
    interview_feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.hackathon.name})"

    def add_member(self, user):
        self.members.add(user)
        self.save()


class Invitation(models.Model):
    hackathon = models.ForeignKey('Hackathon', on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_invitations'
    )
    uid = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(
        max_length=15,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invitation from {self.inviter} to {self.invitee} for {self.hackathon}"

    def accept(self):
        self.status = 'accepted'
        self.save()
        team = Team.objects.get(hackathon=self.hackathon, leader=self.inviter)
        team.add_member(self.invitee)

    def decline(self):
        self.status = 'declined'
        self.save()

class Project(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    hackathon = models.ForeignKey(
        Hackathon,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    domain = models.CharField(max_length=255, null=True, blank=True)
    repo_link = models.URLField(max_length=500, blank=True, null=True)
    live_link = models.URLField(max_length=500, blank=True, null=True)
    avg_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team.name} - {self.domain}"


class ProjectPitch(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    pitch_deck = models.JSONField()
    video_script = models.TextField()
    documentation = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('processing', 'Processing'),
            ('ready', 'Ready'),
            ('failed', 'Failed')
        ],
        default='processing'
    )
    video_id = models.CharField(max_length=255, blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    video_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('ready', 'Ready'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    def __str__(self):
        return f"{self.project} Pitch ({self.status})"