from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

class IsVendor(BasePermission):
    
    def has_permission(self, request, view):
        if not (request.user.is_authenticated):
            return False
        if request.user.role == 1:
            return True
        else:
            return False
        
class IsRetail(BasePermission):
    
    def has_permission(self, request, view):
        if not (request.user.is_authenticated):
            return False
        if request.user.role == 1 and request.user.user.vendor_type == 2 :
            return True
        else:
            return False
        

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        if not bool(request.user):
            return False
        if request.user.role == 1:
            return False
        else:
            return True
        

class IsVendorOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return bool(
                request.method in SAFE_METHODS or
                request.user and
                bool(request.user.role == 1)
            )
        elif request.method in SAFE_METHODS:
            return True

class IsSuperAdmin(BasePermission):
    
    def has_permission(self, request, view):
        if not (request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        else:
            return False
            

