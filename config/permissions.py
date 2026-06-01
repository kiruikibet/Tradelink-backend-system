from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    """Allow access only to the object's owner."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsConversationParticipant(BasePermission):
    """Allow access only to participants of a conversation."""

    def has_object_permission(self, request, view, obj):
        return request.user in (obj.sender, obj.receiver)


class IsNotificationRecipient(BasePermission):
    """Allow access only to the notification's recipient."""

    def has_object_permission(self, request, view, obj):
        return obj.recipient == request.user


class IsAdminOrReadOnly(BasePermission):
    """Allow read-only access to everyone; write access to admins only."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
