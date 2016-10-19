from rest_framework import permissions

class IsOwnerOrReadOnlyQuestion_List(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if obj.private and obj.owner != request.user:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user
