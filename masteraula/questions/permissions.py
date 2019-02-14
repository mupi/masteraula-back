from rest_framework import permissions

class QuestionPermission(permissions.BasePermission):
    """Só poderá editar a questão se o usuário for autenticado"""
   
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        
    # def has_object_permission(self, request, view, obj):
    #     if request.user.is_superuser:
    #         return True
    #     if obj.author == request.user:
    #         return True
    #     if request.method in permissions.SAFE_METHODS:
    #         return True

class LearningObjectPermission(permissions.BasePermission):
    """Só poderá editar o objeto se o usuário for autenticado"""
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        
class DocumentsPermission(permissions.BasePermission):
    """Regras: 
    - Qualquer usuário logado pode criar um documento;
    - Só podem editar um documento o autor desse documento e o super_usuario."""

    def has_permission(self, request, view, obj=None):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
           return True
        return obj.owner == request.user

class HeaderPermission(permissions.BasePermission):
    """Regras: 
    - Qualquer usuário logado pode criar um cabeçalho;
    - Só pode editar e visualizar um cabeçalho o autor e o super_usuario."""

    def has_permission(self, request, view, obj=None):
        if request.user.is_authenticated:
            return True
       
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
           return True
        return obj.owner == request.user

"""from rest_framework import permissions

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
        if obj.secret:
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
        if view.action == 'generate_list' and obj.owner != request.user:
            return False

        # Qualquer usuario pode ver as questoes
        if request.method in permissions.SAFE_METHODS:
            return True

        # Somente super_usuarios e os respectivos autores das questoes podem editar
        if request.user.is_superuser:
            return True
        return obj.author == request.user

class UserPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        # Qualquer usuario pode fazer a listagem dos dados
        if request.method in permissions.SAFE_METHODS:
            return True

        # super-usuarios tem privilegio total
        if request.user.is_superuser:
            return True
        # Somente pode criar novos usuarios pessoas nao logadas
        if view.action == 'create':
            return not request.user.is_authenticated()
        # garante acesso aos demais metodos nao SAFE
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser:
            return True
        return obj == request.user"""