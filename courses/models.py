from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.db import models


class CourseStatus(models.TextChoices):
    PENDING = 'PENDING', 'Đang chờ thanh toán'
    IN_PROGRESS = 'IN_PROGRESS', 'Đang học'
    FAILED ='FAILED', 'Không đạt yêu cầu'
    COMPLETE = 'COMPLETE', 'Hoàn thành'
    INACTIVE = 'INACTIVE', 'Bị khóa tài khoản'
    PAYMENT_FAILED = 'PAYMENT_FAILED', "Thanh toán thất bại"


class BaseModel(models.Model):
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True


class Role(BaseModel):
    name = models.CharField(max_length=100, default='')
    description = models.TextField(default='')

    def __str__(self):
        return self.name


class User(AbstractUser):
    avatar = CloudinaryField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    userRole = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)


class Permission(BaseModel):
    name = models.CharField(max_length=100, default='')
    description = models.TextField(default='')
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=20)
    module = models.CharField(max_length=100)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")


class RolePermission(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)


class Category(BaseModel):
    name = models.CharField(max_length=100, default='')
    image_url = models.URLField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Course(BaseModel):
    class Level(models.TextChoices):
        SO_CAP = "so_cap", "Sơ cấp"
        TRUNG_CAP = "trung_cap", "Trung cấp"
        CAO_CAP = "cao_cap", "Cao cấp"

    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lectures", null=True, blank=True)
    subject = models.CharField(max_length=255)
    image = CloudinaryField()
    name = models.CharField(max_length=255, default='')
    description = models.TextField(default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.SO_CAP
    )
    duration = models.IntegerField(help_text="Duration in minutes", default=0)

    def __str__(self):
        return self.name


class UserCourse(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_course")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="user_course")
    status = models.CharField(max_length=20, default=CourseStatus.PENDING, choices=CourseStatus.choices)


class Payment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50)
    status = models.CharField(max_length=50)

class UserCourse(BaseModel):
    class Status(models.TextChoices):
        ENROLLED = "enrolled", "Đã đăng ký"
        IN_PROGRESS = "in_progress", "Đang học"
        COMPLETED = "completed", "Hoàn thành"
        CANCELLED = "cancelled", "Đã hủy"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="courses")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="students")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ENROLLED
    )

    Payment= models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="user_course",  null=True, blank= True)
   
    class Meta:
        unique_together = ("user", "course") 

    def __str__(self):
        return f"{self.user.username} - {self.course.name} ({self.status})"




class Chapter(BaseModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chapters", null=True, blank=True)
    name = models.CharField(max_length=255, default='')
    description = models.TextField(default='')
    is_published = models.BooleanField(default=False)


class Lesson(BaseModel):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="lessons")
    name = models.CharField(max_length=255, default='')
    description = models.TextField(default='')
    type = models.CharField(max_length=50, default='')
    video_url = models.URLField(null=True, blank=True)
    duration = models.IntegerField()
    is_published = models.BooleanField(default=False)


class Document(BaseModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=255, default='')
    file_url = models.URLField()
    type = models.CharField(max_length=50, default='')





class LessonProgress(BaseModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    user_course = models.ForeignKey(UserCourse, on_delete=models.CASCADE, related_name="lesson_progresses", null= True, blank=True)
    status = models.CharField(max_length=50)
    watch_time = models.IntegerField(default=0)


class Forum(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    usercourse = models.ForeignKey(UserCourse, on_delete=models.CASCADE, related_name="usercourse",  null=True, blank=True)
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name="forum", null=True, blank=True)
    name = models.CharField(max_length=255, default='')
    description = models.TextField(default='')
    is_locked = models.BooleanField(default=False)


class Comment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    content = models.TextField()
