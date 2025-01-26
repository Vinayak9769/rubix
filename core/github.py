import os
import requests
from dotenv import load_dotenv
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime

GITHUB_API_URL = "https://api.github.com    /users/{username}"
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
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

@api_view(['GET'])
def calculate_github_score(request, username):
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}
        response = requests.get(GITHUB_API_URL.format(username=username), headers=headers)
        response.raise_for_status()
        data = response.json()
        repos_response = requests.get(data['repos_url'], headers=headers)
        repos_data = repos_response.json()
        metrics = {
            'repos': min(data['public_repos'], 150),
            'stars': sum(repo['stargazers_count'] for repo in repos_data),
            'followers': min(data['followers'], 2000),
            'forks': sum(repo['forks_count'] for repo in repos_data),
            'age': (timezone.now().year - datetime.strptime(data['created_at'], '%Y-%m-%dT%H:%M:%SZ').year),
            'issues': data['public_gists'] + data['public_repos'],
            'prs': data['public_repos'] * 3,
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
        breakdown = {}

        for key, weight in WEIGHTS.items():
            normalized = min((metrics[key] / max_values[key])**0.5, 1.0)
            points = normalized * weight * 1000
            score += points
            breakdown[key] = round(points)

        user = request.user
        user.github_score = round(score)
        user.save()

        return Response({
            'username': username,
            'total_score': round(score),
            'score_breakdown': breakdown,
            'max_score': 1000
        })

    except requests.exceptions.HTTPError as e:
        return Response({'error': str(e)}, status=400)