from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.db import models

# Models này chỉ dùng để test !!!!!!!!!
class User(AbstractUser):
    avatar = CloudinaryField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    # Đảm bảo email là bắt buộc
    email = models.EmailField(unique=True)

    # Đảm bảo first_name và last_name là bắt buộc
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)


class BaseModel(models.Model):
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(BaseModel):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Course(BaseModel):
    subject = models.CharField(max_length=255)
    description = models.TextField(null=True)
    image = CloudinaryField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    def __str__(self):
        return self.subject

    class Meta:
        ordering = ['-id']
