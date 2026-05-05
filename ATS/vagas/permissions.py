from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsEmpresaOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.tipo == 'empresa'

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.tipo == 'empresa' and obj.empresa_id == request.user.id
