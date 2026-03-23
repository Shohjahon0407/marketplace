from rest_framework.permissions import BasePermission


class IsWorker(BasePermission):
    message = "Sizda worker huquqi yo‘q."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_worker
        )
