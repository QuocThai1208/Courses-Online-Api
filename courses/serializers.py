from courses.models import Category, Course, User, UserCourse, Forum, Comment, Chapter, Lesson, Document, \
    LessonProgress, CourseProgress, LessonProgressStatus, Topic
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
import cloudinary
import cloudinary.uploader


class BaseSerializer(serializers.ModelSerializer):
    def upload_to_cloudinary(self, image_file, folder="uploads"):
        try:
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder=folder,
                resource_type="image",
                transformation=[
                    {'width': 500, 'height': 500, 'crop': 'limit'},
                    {'quality': 'auto'}
                ]
            )
            return upload_result.get('secure_url')
        except Exception as e:
            raise serializers.ValidationError(f"Lỗi khi upload ảnh: {str(e)}")

    def handle_image_upload(self, validated_data, field_name, folder="uploads"):
        if field_name in validated_data and validated_data[field_name]:
            image_file = validated_data[field_name]
            secure_url = self.upload_to_cloudinary(image_file, folder)
            validated_data[field_name] = secure_url
        return validated_data


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name']


class ItemSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['image'] = instance.image.url

        return data


class CourseSerializer(ItemSerializer):
    lecturer_name = serializers.SerializerMethodField(read_only=True)
    category_name = serializers.SerializerMethodField(read_only=True)
    total_student = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'subject', 'image', 'category', 'category_name', 'total_student', 'lecturer', 'lecturer_name',
                  'name', 'description', 'price', 'level', 'duration',
                  'created_at']

    def get_lecturer_name(self, obj):
        return obj.lecturer.last_name + " " + obj.lecturer.first_name

    def get_total_student(self, obj):
        return obj.user_course.count()

    def get_category_name(self, obj):
        return obj.category.name

    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs()
        request = self.context.get('request')

        if request and request.method in ['PUT', 'PATCH']:
            extra_kwargs['subject'] = {'required': False}
            extra_kwargs['image'] = {'required': False}

        return extra_kwargs


class ChapterSerializer(BaseSerializer):
    class Meta:
        model = Chapter
        fields = ['id', 'course', 'name', 'description', 'is_published', 'active', 'created_at']


class LessonSerializer(BaseSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'chapter', 'name', 'description', 'type', 'video_url', 'duration', 'is_published', 'active',
                  'created_at']


class UserRegistrationSerializer(BaseSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'confirm_password', 'email',
                  'first_name', 'last_name', 'avatar', 'address', 'introduce', 'phone', 'userRole')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Mật khẩu xác nhận không khớp."})
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email này đã được sử dụng.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Tên đăng nhập này đã được sử dụng.")
        return value

    def create(self, validated_data):
        validated_data = self.handle_image_upload(validated_data, 'avatar', 'avatars')
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(BaseSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'avatar', 'address', 'introduce', 'password', 'phone')

    def update(self, instance, validated_data):
        validated_data = self.handle_image_upload(validated_data, 'avatar', 'avatars')
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserSerializer(BaseSerializer):
    avatar = serializers.SerializerMethodField()
    userRole = serializers.SerializerMethodField(read_only=True)
    date_joined = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'avatar', 'address', 'introduce', 'phone', 'date_joined', 'userRole', 'is_active')
        read_only_fields = ('id', 'date_joined')

    def get_userRole(self, obj):
        return obj.userRole.name

    def get_date_joined(self, obj):
        return obj.date_joined.strftime("%d-%m-%Y")

    def get_avatar(self, obj):
        if obj.avatar:
            if isinstance(obj.avatar, str):
                return obj.avatar
            else:
                return obj.avatar.url if obj.avatar else None
        return None


class UserCourseSerializer(BaseSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    course_obj = CourseSerializer(source='course', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_at = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserCourse
        fields = ['id', 'user', 'course', 'course_obj', 'status', 'status_display', 'created_at']

    def get_user(self, obj):
        return obj.user.username

    def get_created_at(self, obj):
        return obj.created_at.strftime("%d-%m-%Y")

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserNameMixin:
    def get_username(self, obj):
        return obj.user.username


class ForumSerializer(serializers.ModelSerializer, UserNameMixin):
    user = serializers.SerializerMethodField(read_only=True)
    course_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Forum
        fields = ['id', 'user', 'course', 'course_name', 'name', 'description', 'is_locked']

    def get_user(self, obj):
        return self.get_username(obj)

    def get_course_name(self, obj):
        return obj.course.name

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TopicSerializer(serializers.ModelSerializer, UserNameMixin):
    user = serializers.SerializerMethodField(read_only=True)
    comment_count = serializers.SerializerMethodField(read_only=True)
    last_comment = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Topic
        fields = ['id', 'forum', 'user', 'title', 'content', 'is_pinned', 'is_locked',
                  'view_count', 'last_activity', 'comment_count', 'last_comment', 'created_at']
        read_only_fields = ['id', 'user', 'view_count', 'last_activity', 'created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Swagger documentation
        self.fields['title'].help_text = "Tiêu đề của chủ đề thảo luận"
        self.fields['content'].help_text = "Nội dung chi tiết của chủ đề"
        self.fields['is_pinned'].help_text = "Chủ đề được ghim lên đầu"
        self.fields['is_locked'].help_text = "Chủ đề bị khóa không cho bình luận"
        self.fields['forum'].help_text = "ID của forum chứa chủ đề này"

    def get_user(self, obj):
        return self.get_username(obj)

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_last_comment(self, obj):
        last_comment = obj.comments.last()
        if last_comment:
            return {
                'user': last_comment.user.username,
                'content': last_comment.content[:100] + '...' if len(
                    last_comment.content) > 100 else last_comment.content,
                'created_at': last_comment.created_at
            }
        return None

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer, UserNameMixin):
    user = serializers.SerializerMethodField(read_only=True)
    user_avatar = serializers.SerializerMethodField(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'user_avatar', 'forum', 'topic', 'parent', 'content', 'replies', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Swagger documentation
        self.fields['content'].help_text = "Nội dung bình luận"
        self.fields['topic'].help_text = "ID của topic chứa bình luận này"
        self.fields['parent'].help_text = "ID của bình luận cha (nếu là reply)"
        self.fields['forum'].help_text = "ID của forum (deprecated, sử dụng topic thay thế)"

    def get_user(self, obj):
        return self.get_username(obj)

    def get_user_avatar(self, obj):
        if obj.user.avatar:
            if isinstance(obj.user.avatar, str):
                return obj.user.avatar
            else:
                return obj.user.avatar.url if obj.user.avatar else None
        return None

    def get_replies(self, obj):
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True, context=self.context).data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class LecturerSerializer(serializers.ModelSerializer):
    userRole = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'address', 'introduce', 'phone',
                  'date_joined', 'userRole', 'is_active']

    def get_userRole(self, obj):
        return obj.userRole.name if obj.userRole else None

    def get_avatar(self, obj):
        if obj.avatar:
            if isinstance(obj.avatar, str):
                return obj.avatar
            else:
                return obj.avatar.url if obj.avatar else None
        return None


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'lesson', 'name', 'file_url', 'type', 'active', 'created_at', 'updated_at']


class LessonDetailSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'chapter', 'name', 'description', 'type', 'video_url', 'duration', 'is_published', 'active',
                  'created_at', 'updated_at', 'documents']


class ChapterDetailSerializer(serializers.ModelSerializer):
    lessons = LessonDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'course', 'name', 'description', 'is_published', 'active', 'created_at', 'updated_at',
                  'lessons']


class CourseDetailSerializer(serializers.ModelSerializer):
    lecturer = LecturerSerializer(read_only=True)
    students_count = serializers.SerializerMethodField(read_only=True)
    chapters = ChapterDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'price', 'level', 'duration', 'thumbnail_url', 'learning_outcomes',
                  'requirements', 'video_url', 'lecturer', 'students_count', 'chapters']

    def get_students_count(self, obj):
        return obj.user_course.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Convert duration from minutes to seconds
        data['duration'] = instance.duration * 60
        # Convert price to string
        data['price'] = str(instance.price) if instance.price else '0'
        return data


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_name = serializers.CharField(source='lesson.name', read_only=True)
    lesson_duration = serializers.IntegerField(source='lesson.duration', read_only=True)
    status_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson', 'lesson_name', 'lesson_duration', 'status', 'status_display',
                  'started_at', 'completed_at', 'watch_time', 'last_watched_at', 'completion_percentage']
        read_only_fields = ['id', 'started_at', 'completed_at', 'last_watched_at']

    def get_status_display(self, obj):
        """Get human readable status"""
        status_map = {
            'NOT_STARTED': 'Chưa bắt đầu',
            'IN_PROGRESS': 'Đang học',
            'COMPLETED': 'Đã hoàn thành'
        }
        return status_map.get(obj.status, obj.status)


class CourseProgressSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_image = serializers.CharField(source='course.image.url', read_only=True)

    class Meta:
        model = CourseProgress
        fields = ['id', 'course', 'course_name', 'course_image', 'total_lessons', 'completed_lessons',
                  'total_watch_time', 'completion_percentage', 'last_accessed_at', 'enrolled_at']
        read_only_fields = ['id', 'total_lessons', 'completed_lessons', 'total_watch_time', 'completion_percentage']


class LessonProgressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ['status', 'watch_time', 'completion_percentage']

    def update(self, instance, validated_data):
        from django.utils import timezone

        # Update last watched time
        instance.last_watched_at = timezone.now()

        # Set started_at if not set and status is IN_PROGRESS
        if validated_data.get('status') == LessonProgressStatus.IN_PROGRESS and not instance.started_at:
            instance.started_at = timezone.now()

        # Set completed_at if status is COMPLETED
        if validated_data.get('status') == LessonProgressStatus.COMPLETED and not instance.completed_at:
            instance.completed_at = timezone.now()

        # Update the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Update course progress
        course_progress, created = CourseProgress.objects.get_or_create(
            user=instance.user,
            course=instance.lesson.chapter.course
        )
        course_progress.update_progress()

        return instance


class EnrolledCourseSerializer(serializers.ModelSerializer):
    course = CourseDetailSerializer(read_only=True)
    progress = CourseProgressSerializer(read_only=True)

    class Meta:
        model = UserCourse
        fields = ['id', 'course', 'status', 'progress', 'created_at']

    def get_progress(self, obj):
        """
        Lấy CourseProgress từ prefetched data
        """
        # Sử dụng prefetched data
        if hasattr(obj.course, 'user_course_progress'):
            progress_list = obj.course.user_course_progress
            if progress_list:
                # Lấy progress đầu tiên (chỉ có 1 vì filter theo user)
                progress = progress_list[0]
                return CourseProgressSerializer(progress).data

        # Fallback: Tạo progress mới nếu chưa có
        try:
            progress = CourseProgress.objects.get(
                user=obj.user,
                course=obj.course
            )
            return CourseProgressSerializer(progress).data
        except CourseProgress.DoesNotExist:
            # Tạo CourseProgress mới
            progress = CourseProgress.objects.create(
                user=obj.user,
                course=obj.course
            )
            progress.update_progress()
            return CourseProgressSerializer(progress).data