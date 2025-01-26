from django.contrib.auth.models import AbstractUser
from django.db import models
from dotenv import load_dotenv
import os
import requests
from django.utils import timezone
from datetime import datetime

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    password = models.CharField(max_length=128)
    skills = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    github = models.URLField(max_length=255, blank=True, null=True)
    linkedin = models.URLField(max_length=255, blank=True, null=True)
    github_score = models.IntegerField(default=0)

    ROLE_CHOICES = (
        ('organizer', 'Organizer'),
        ('participant', 'Participant'),
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='participant')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        if self.github and self.pk:
            original = CustomUser.objects.get(pk=self.pk)
            if original.github != self.github:
                self.github_score = github_score(self.github)
        elif self.github:
            self.github_score = github_score(self.github)
        super().save(*args, **kwargs)
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')


WEIGHTS = {
    'repos': 0.25,
    'stars': 0.30,
    'contributions': 0.10,
    'followers': 0.10,
    'forks': 0.10,
    'age': 0.05,
    'issues': 0.05,
    'prs': 0.05,
    'commit_freq': 0.05
}

def github_score(github_url):
    try:
        username = github_url.strip('/').split('/')[-1]
        if not username:
            return 0

        headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

        user_response = requests.get(f'https://api.github.com/users/{username}', headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()

        repos_response = requests.get(user_data['repos_url'], headers=headers)
        repos_data = repos_response.json()

        metrics = {
            'repos': min(user_data['public_repos'], 150),
            'stars': sum(repo['stargazers_count'] for repo in repos_data),
            'followers': min(user_data['followers'], 2000),
            'forks': sum(repo['forks_count'] for repo in repos_data),
            'age': (timezone.now().year -
                    datetime.strptime(user_data['created_at'], '%Y-%m-%dT%H:%M:%SZ').year),
            'issues': user_data['public_gists'] + user_data['public_repos'],
            'prs': user_data['public_repos'] * 3,
            'contributions': 0,
            'commit_freq': 0
        }

        max_values = {
            'repos': 150,
            'stars': 1000,
            'followers': 2000,
            'forks': 500,
            'age': 15,
            'issues': 300,
            'prs': 200,
            'contributions': 1500,
            'commit_freq': 1.5
        }

        score = 0
        for key, weight in WEIGHTS.items():
            if max_values[key] == 0:
                continue
            normalized = min((metrics[key] / max_values[key]) ** 0.5, 1.0)
            score += normalized * weight * 1000
        print(score)
        return round(score)

    except (requests.exceptions.RequestException, KeyError):
        return 0