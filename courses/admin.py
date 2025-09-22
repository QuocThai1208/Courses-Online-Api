from django.contrib import admin
from .models import (
    Role, User, Permission, Category, Course, UserCourse,
    Chapter, Lesson, Document, Payment, LessonProgress, CourseProgress,
    Forum, Comment, LessonProgressStatus, Topic
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
    list_display = ("id", "user", "lesson", "status", "completion_percentage", "watch_time", "started_at", "completed_at", "last_watched_at")
    list_filter = ("status", "lesson__chapter__course")
    search_fields = ("user__username", "lesson__name")
    readonly_fields = ("started_at", "completed_at", "last_watched_at")
    ordering = ("-last_watched_at", "-created_at")


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "completion_percentage", "completed_lessons", "total_lessons", "total_watch_time", "last_accessed_at", "enrolled_at")
    list_filter = ("course", "enrolled_at")
    search_fields = ("user__username", "course__name")
    readonly_fields = ("total_lessons", "completed_lessons", "total_watch_time", "completion_percentage", "enrolled_at")
    ordering = ("-last_accessed_at", "-enrolled_at")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'course')


# Note: LessonProgressStatus is a TextChoices enum, not a model
# So we don't need to register it as an admin class
# The choices are available in the LessonProgress admin form


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "course", "user", "is_locked", "active")
    list_filter = ("is_locked", "course")
    search_fields = ("name", "description")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "forum", "is_pinned", "is_locked", "view_count", "last_activity", "created_at")
    list_filter = ("forum", "is_pinned", "is_locked", "created_at")
    search_fields = ("title", "user__username", "content")
    readonly_fields = ("view_count", "last_activity", "created_at", "updated_at")
    ordering = ("-is_pinned", "-last_activity")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'forum')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "forum", "topic", "parent", "content", "created_at")
    list_filter = ("forum", "topic", "created_at")
    search_fields = ("user__username", "content")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'forum', 'topic')
