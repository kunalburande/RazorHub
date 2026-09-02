from rest_framework import permissions

class AgentPermission(permissions.BasePermission):
    """
    Checks if the request is from an authorized AI agent.
    For MVP, we allow any authenticated user to act as an agent if they have an API token.
    In a real system, this would check JWT scope claims (e.g., 'commerce.products.read').
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # In a real system we would check scopes here
        # e.g., 'commerce.products.read' in request.auth.payload.get('scopes', [])
        return True
