from django.contrib import admin
from courses.models import Course, Category, Role, RolePermission, Permission, Payment, UserCourse, Chapter, Document, Lesson, LessonProgress, Forum, Comment

# Register your models here.
admin.site.register(Course)
admin.site.register(Role)
admin.site.register(Permission)

admin.site.register(RolePermission)

admin.site.register(Payment)



admin.site.register(UserCourse)

admin.site.register(Chapter)

admin.site.register(Document)

admin.site.register(LessonProgress)

admin.site.register(Forum)

admin.site.register(Comment)