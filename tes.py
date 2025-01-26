import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rubix.settings')
django.setup()

from core.models import Hackathon, Team, Project
from auths.models import CustomUser

# Create users
users = [
    CustomUser(username=f'user{i}', email=f'user{i}@example.com', password='password') for i in range(1, 11)
]
for user in users:
    user.save()

hackathon = Hackathon.objects.create(name='Sample Hackathon', created_by=users[0])

team = Team.objects.get(id=16)

for user in users:
    hackathon.participants.add(user)
    team.members.add(user)

projects = [
    Project(
        team=team,
        hackathon=hackathon,
        domain='Web Development' if i % 2 == 0 else 'AI/ML',
        repo_link=f'https://github.com/team-16/project{i+1}',
        live_link=f'https://team-16-project{i+1}.com'
    ) for i in range(5)
]

for project in projects:
    project.save()

print("Users, projects, and hackathon registrations for team id=16 have been populated.")