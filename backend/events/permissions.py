from rest_framework import permissions


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow organizers to edit their own events.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed for authenticated users
        # with organizer or admin role
        return (
            request.user.is_authenticated and 
            (request.user.role in ['organizer', 'admin'] or request.user.is_staff)
        )
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the organizer of the event
        # or admin users
        return (
            obj.organizer == request.user or 
            request.user.role == 'admin' or 
            request.user.is_staff
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object
        # Check if the object has an 'organizer' field (for events)
        if hasattr(obj, 'organizer'):
            return obj.organizer == request.user
        
        # Check if the object has a 'user' field (for user-related objects)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Default to checking if the object itself is the user
        return obj == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to make changes.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed for admin users
        return (
            request.user.is_authenticated and 
            (request.user.role == 'admin' or request.user.is_staff)
        )


class IsOrganizerUser(permissions.BasePermission):
    """
    Custom permission to only allow users with organizer role or higher.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role in ['organizer', 'admin']
        )


class CanManageEvent(permissions.BasePermission):
    """
    Custom permission for event management.
    Allows:
    - Event organizers to manage their own events
    - Admin users to manage any event
    - Read access for everyone
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write operations, user must be authenticated
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin users can manage any event
        if request.user.role == 'admin' or request.user.is_staff:
            return True
        
        # Organizers can only manage their own events
        if hasattr(obj, 'organizer'):
            return obj.organizer == request.user
        
        return False


class CanCreateEvent(permissions.BasePermission):
    """
    Custom permission for event creation.
    Only authenticated users with organizer role or higher can create events.
    """
    
    def has_permission(self, request, view):
        if request.method == 'POST':
            return (
                request.user.is_authenticated and 
                request.user.role in ['organizer', 'admin']
            )
        return True


class IsEventOwnerOrAdmin(permissions.BasePermission):
    """
    Permission for event-related actions that require ownership or admin access.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.role == 'admin' or request.user.is_staff:
            return True
        
        # Event organizers can manage their own events
        if hasattr(obj, 'organizer'):
            return obj.organizer == request.user
        
        # For booking-related objects, check the event owner
        if hasattr(obj, 'event') and hasattr(obj.event, 'organizer'):
            return obj.event.organizer == request.user
        
        return False