from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Allow access only to the owner referenced by `user`."""

    def has_object_permission(self, request, view, obj):
        return getattr(obj, "user", None) == request.user


class IsConversationParticipant(permissions.BasePermission):
    """Allow access only to a conversation buyer or seller."""

    def has_object_permission(self, request, view, obj):
        return request.user in {
            getattr(obj, "buyer", None),
            getattr(obj, "seller", None),
        }


class IsNotificationRecipient(permissions.BasePermission):
    """Allow access only to the user receiving a notification."""

    def has_object_permission(self, request, view, obj):
        return getattr(obj, "recipient", None) == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow unsafe writes only to staff users."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
