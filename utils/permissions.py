from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):
    """
    这个 Permission 负责检查 obj.user == request.user
    Permission 会一个个被执行
    - 如果是 detail=False 的 action， 只检测 has_permission
    - 如果是 detail=True 的 action， 同时检测 has_permission 和 has_object_permission
    出错则显示 message 内容
    """
    message = "You do not have the permission to access this object"

    # 不定义也可以,因为原本就是return True
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user
