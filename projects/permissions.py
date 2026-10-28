from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

from .models import Membership


def get_project_or_404(user, project_id, roles=None):
    """Return the project if `user` is a member, with one of `roles` if given.

    Non-members get a 404, so they can't tell the project exists.
    Members without the right role get a 403.
    """
    membership = get_object_or_404(
        Membership.objects.select_related("project"), project_id=project_id, user=user
    )
    if roles and membership.role not in roles:
        raise HttpError(403, f"This needs the {' or '.join(roles)} role")
    return membership.project
