from core.models import Hackathon
from rest_framework.permissions import BasePermission
class IsOrganizer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'organizer'

class IsParticipant(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'participant'


class IsHackathonOrganizer(BasePermission):
    def has_permission(self, request, view):
        hackathon_id = view.kwargs.get('hackathon_id')
        if hackathon_id:
            hackathon = Hackathon.objects.get(id=hackathon_id)
            return hackathon.created_by == request.user
        return False