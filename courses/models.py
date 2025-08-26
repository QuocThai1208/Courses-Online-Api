from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class User(AbstractUser):
    phone = models.CharField(max_length=20, null=True, blank=True)
    avatar = models.URLField(null=True, blank=True)
    userRole = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,  null=True, blank=True)


class Permission(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=20)
    module = models.CharField(max_length=100)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")

class Category(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.URLField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True,  null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,  null=True, blank=True)

class Course(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lectures")
    name = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail_url = models.URLField(null=True, blank=True)
    video_url = models.URLField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    level = models.CharField(max_length=50)
    duration = models.IntegerField(help_text="Duration in minutes")
    created_at = models.DateTimeField(auto_now_add=True,  null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,  null=True, blank=True)


class Chapter(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chapters")
    name = models.CharField(max_length=255)
    description = models.TextField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,  null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,  null=True, blank=True)


class Lesson(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="lessons")
    name = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=50, default='')
    video_url = models.URLField(null=True, blank=True)
    duration = models.IntegerField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,  null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,  null=True, blank=True)


class Document(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=255)
    file_url = models.URLField()
    type = models.CharField(max_length=50, default='')
    created_at = models.DateTimeField(auto_now_add=True,  null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,  null=True, blank=True)

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True,  null=True, blank=True)


class LessonProgress(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    watch_time = models.IntegerField(default=0)


class Forum(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name="forum",  null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(default='')
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,  null=True, blank=True)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True ,  null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,  null=True, blank=True)
