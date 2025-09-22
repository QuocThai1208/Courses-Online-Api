from django.contrib import admin
from courses.models import Course, Category, Chapter, Lesson, User

# Register your models here.
admin.site.register(Course)
admin.site.register(Category)
admin.site.register(Chapter)
admin.site.register(Lesson)
admin.site.register(User)