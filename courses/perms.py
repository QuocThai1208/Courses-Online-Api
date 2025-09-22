from rest_framework import permissions


class IsTeacher(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.userRole.name == 'teacher'


class IsStudent(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.userRole.name == 'student'


class IsAdmin(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.userRole.name == 'admin'


class IsTeacherOrAdmin(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request,
                                      view) and (request.user.userRole.name == 'teacher' or request.user.userRole.name == 'admin')

