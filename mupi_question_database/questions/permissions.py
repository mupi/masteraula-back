from rest_framework import permissions

class Question_ListPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        # Qualquer usuario pode fazer a listagem dos dados
        if request.method in permissions.SAFE_METHODS:
            return True

        # Apenas super-usuarios e usuarios logados podem criar listas
        if request.user.is_superuser:
            return True
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj):
        # Apenas super-usuarios e donos da listas podem editar
        if request.user.is_superuser:
            return True
        if obj.owner == request.user:
            return True
        # Se a lista for privada, negar acesso a outras pessoas
        if obj.private:
            return False
        # Habilita somente métodos seguros
        return request.method in permissions.SAFE_METHODS

class QuestionPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        # Qualquer usuario pode fazer a listagem dos dados
        if request.method in permissions.SAFE_METHODS:
            return True

        # Apenas super-usuarios e usuarios logados podem criar questoes
        if request.user.is_superuser:
            return True
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj):
        # Qualquer usuario pode ver as questoes
        if request.method in permissions.SAFE_METHODS:
            return True

        # Somente super_usuarios e os respectivos autores das questoes podem editar
        if request.user.is_superuser:
            return True
        return obj.author == request.user

class UserPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser:
            return True
        return obj == request.user
