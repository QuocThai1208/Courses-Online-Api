from django.contrib import admin
from .models import (
    Role, User, Permission, Category, Course, UserCourse,
    Chapter, Lesson, Document, Payment, LessonProgress,
    Forum, Comment
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "active", "created_at")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", 'avatar', "email", "first_name", "last_name", "phone", "userRole", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "userRole")
    search_fields = ("username", "email", "first_name", "last_name")


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "method", "path", "module", "role", "active")
    list_filter = ("method", "role")
    search_fields = ("name", "path", "module")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "active", "created_at")
    search_fields = ("name",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "subject", "category", "lecturer", "price", "level", "duration", "active")
    list_filter = ("level", "category", "lecturer")
    search_fields = ("name", "subject", "description")


@admin.register(UserCourse)
class UserCourseAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "status", "active", "created_at")
    list_filter = ("active", "course")
    search_fields = ("user__username", "course__name")


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "course", "is_published", "active")
    list_filter = ("is_published", "course")
    search_fields = ("name", "description")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "chapter", "type", "duration", "is_published")
    list_filter = ("is_published", "chapter__course")
    search_fields = ("name", "description")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "lesson", "type")
    list_filter = ("type",)
    search_fields = ("name",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "amount", "method", "status", "created_at")
    list_filter = ("status", "method")
    search_fields = ("user__username", "course__name")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "lesson", "status", "watch_time", "started_at", "completed_at")
    list_filter = ("status",)
    search_fields = ("user__username", "lesson__name")


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "course", "user", "is_locked", "active")
    list_filter = ("is_locked", "course")
    search_fields = ("name", "description")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "forum", "parent", "content", "created_at")
    list_filter = ("forum",)
    search_fields = ("user__username", "content")
