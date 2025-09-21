from django.db.models import Count
from rest_framework import viewsets, generics, status, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
import hmac, hashlib
from courses.models import Category, Course, User, Role, UserCourse, Forum, Comment, Chapter, Lesson, CourseStatus, \
    Payment, PaymentStatus, LessonProgress, CourseProgress, LessonProgressStatus, Topic
from courses import serializers, paginators
from .perms import IsAdmin, IsStudent, IsTeacher, IsTeacherOrAdmin
from .services.momo import create_momo_payment, update_status_user_course
from rest_framework.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Category.objects.filter(active=True)
    serializer_class = serializers.CategorySerializer


class TeacherViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = User.objects.filter(userRole__name="Teacher")
    serializer_class = serializers.TeacherSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.filter(active=True)
    serializer_class = serializers.CourseSerializer
    pagination_class = paginators.CoursePagination

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsTeacherOrAdmin()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(lecturer=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.request

        lecturer_id = request.query_params.get('lecturer')
        category_id = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        level = request.query_params.get('level')

        if lecturer_id:
            queryset = queryset.filter(lecturer_id=lecturer_id)

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        if level:
            queryset = queryset.filter(level=level)

        return queryset

    @action(methods=['get'], detail=True, url_path='forum')
    def get_forum(self, request, pk=None):
        course = self.get_object()
        try:
            forum = course.forum
        except Forum.DoesNotExist:
            return Response({"detail": "Forum not found for this course"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializers.ForumSerializer(forum).data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='top')
    def get_courses_top(self, request, pk=None):
        top_courses = Course.objects.annotate(student_count=Count('user_course')).order_by('-student_count')[:3]
        return Response(serializers.CourseSerializer(top_courses, many=True).data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True, url_path='detail')
    def get_course_detail(self, request, pk=None):
        try:
            course = self.get_object()
            # Optimize queries with select_related and prefetch_related
            course = Course.objects.select_related('lecturer', 'lecturer__userRole').prefetch_related(
                'chapters__lessons__documents'
            ).get(pk=pk)
            
            serializer = serializers.CourseDetailSerializer(course)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return Response({"detail": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChapterViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ChapterSerializer
    pagination_class = paginators.ChapterPagination
    queryset = Chapter.objects.all()

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsTeacherOrAdmin()]
        return [permissions.IsAuthenticated()]


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.LessonSerializer
    pagination_class = paginators.LessonPagination
    queryset = Lesson.objects.all()

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsTeacherOrAdmin()]
        return [permissions.IsAuthenticated()]


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser]

    def get_serializer_class(self):
        if self.action in ['register_student', 'register_teacher']:
            return serializers.UserRegistrationSerializer
        return serializers.UserSerializer

    def get_permissions(self):
        if self.action in ['register_student', 'register_teacher']:
            return [permissions.AllowAny()]
        elif self.action in ['get_current_user']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Vui lòng sử dụng /users/register-student/ hoặc /users/register-teacher/ để đăng ký."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    # Đăng ký học viên
    @action(methods=['post'], detail=False, url_path='register-student')
    def register_student(self, request):
        data = request.data.copy()
        student_role = get_object_or_404(Role, name="Student")
        data['userRole'] = student_role.pk
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Đăng ký học viên thành công!',
                'user': serializers.UserSerializer(user).data,
                'note': 'Vui lòng sử dụng endpoint /o/token/ để lấy access token sau khi đăng ký'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Đăng ký giảng viên
    @action(methods=['post'], detail=False, url_path='register-teacher')
    def register_teacher(self, request):
        data = request.data.copy()
        teacher_role = get_object_or_404(Role, name="Teacher")
        data['userRole'] = teacher_role.pk
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Đăng ký giảng viên thành công!',
                'user': serializers.UserSerializer(user).data,
                'note': 'Vui lòng sử dụng endpoint /o/token/ để lấy access token sau khi đăng ký'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get', 'patch'], url_path='current-user', detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def get_current_user(self, request):
        user = request.user
        if request.method == 'PATCH':
            serializer = serializers.UserUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializers.UserSerializer(user).data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializers.UserSerializer(user).data)


class UserCourseViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    serializer_class = serializers.UserCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if IsAdmin().has_permission(self.request, self):
            return UserCourse.objects.all()
        return UserCourse.objects.filter(user=user)


    @action(methods=['post'], detail=False, url_path='create', permission_classes=[IsStudent])
    def create_user_course(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user_course = serializer.save()
        pay_url = create_momo_payment(user, user_course.course.price, user_course.id, user_course.course.id)

        return Response({'payUrl': pay_url}, status=status.HTTP_201_CREATED)


class MomoIPNViewSet(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        user_course_id = data['extraData']
        payment_id = data['orderId']

        raw_signature = (
            f"accessKey=F8BBA842ECF85"
            f"&amount={data['amount']}"
            f"&extraData={data['extraData']}"
            f"&message={data['message']}"
            f"&orderId={data['orderId']}"
            f"&orderInfo={data['orderInfo']}"
            f"&orderType={data['orderType']}"
            f"&partnerCode={data['partnerCode']}"
            f"&payType={data['payType']}"
            f"&requestId={data['requestId']}"
            f"&responseTime={data['responseTime']}"
            f"&resultCode={data['resultCode']}"
            f"&transId={data['transId']}"
        )

        signature = hmac.new(bytes('K951B6PE1waDMi640xX08PD3vg6EkVlz', 'utf-8'),
                     bytes(raw_signature, 'utf-8'),
                     hashlib.sha256).hexdigest()

        # xác thực chữ
        if signature != data.get("signature"):
            return Response({"message": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
        payment = Payment.objects.get(id=payment_id)

        # thanh toán thành công
        if data["resultCode"] == 0:
            update_status_user_course(user_course_id, CourseStatus.IN_PROGRESS)
            payment.status = PaymentStatus.SUCCESS
            payment.save()
            return Response({"message": "Payment success"}, status=status.HTTP_200_OK)
        # thanh toán thất bại
        else:
            update_status_user_course(user_course_id, CourseStatus.PAYMENT_FAILED)
            payment.status = PaymentStatus.FAILED
            payment.save()
            return Response({"message": "Payment failed"}, status=status.HTTP_200_OK)



class CanAccessForum(permissions.BasePermission):

    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admin có quyền truy cập tất cả
        if IsAdmin().has_permission(request, view):
            return True
            
        # Teacher có quyền truy cập forum họ tạo
        if IsTeacher().has_permission(request, view) and obj.user == user:
            return True
            
        # Student có quyền truy cập forum của khóa học đã đăng ký
        if obj.course:
            return UserCourse.objects.filter(
                user=user,
                course=obj.course,
                status__in=[CourseStatus.IN_PROGRESS, CourseStatus.COMPLETE]
            ).exists()
            
        return False

class ForumViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    serializer_class = serializers.ForumSerializer
    permission_classes = [CanAccessForum]

    def get_queryset(self):
        user = self.request.user
        if IsTeacher().has_permission(self.request, self):
            return Forum.objects.filter(user=user)
        elif IsAdmin().has_permission(self.request, self):
            return Forum.objects.all()
        else:
            # Lấy danh sách các khóa học mà user đã đăng ký
            enrolled_courses = UserCourse.objects.filter(
                user=user,
                status__in=[CourseStatus.IN_PROGRESS, CourseStatus.COMPLETE]  # Chỉ khóa học đang học hoặc đã hoàn thành
            ).values_list('course', flat=True)
            
            # Trả về forums của các khóa học đã đăng ký
            return Forum.objects.filter(course__in=enrolled_courses)

    @swagger_auto_schema(
        operation_summary="Tạo forum mới",
        operation_description="Chỉ giảng viên mới có thể tạo forum cho khóa học",
        request_body=serializers.ForumSerializer,
        responses={
            201: openapi.Response(
                description="Tạo forum thành công",
                schema=serializers.ForumSerializer
            ),
            403: openapi.Response(
                description="Không có quyền tạo forum"
            )
        }
    )
    def perform_create(self, serializer):
        # Chỉ teacher mới có thể tạo forum
        if not IsTeacher().has_permission(self.request, self):
            raise PermissionDenied("Chỉ giảng viên mới có thể tạo forum")
        
        serializer.save(user=self.request.user)

class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        forum_id = self.request.query_params.get('forum_id')
        if forum_id:
            return Topic.objects.filter(forum_id=forum_id).select_related('user', 'forum')
        return Topic.objects.all().select_related('user', 'forum')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="Tăng số lượt xem topic",
        operation_description="Tăng số lượt xem của một topic cụ thể",
        responses={
            200: openapi.Response(
                description="Thành công",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'view_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Số lượt xem mới')
                    }
                )
            )
        }
    )
    @action(methods=['post'], detail=True, url_path='increment-view')
    def increment_view(self, request, pk=None):
        topic = self.get_object()
        topic.view_count += 1
        topic.save()
        return Response({'view_count': topic.view_count}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Lấy danh sách bình luận của topic",
        operation_description="Lấy tất cả bình luận của một topic cụ thể",
        responses={
            200: openapi.Response(
                description="Danh sách bình luận",
                schema=serializers.CommentSerializer(many=True)
            )
        }
    )
    @action(methods=['get'], detail=True, url_path='comments')
    def get_topic_comments(self, request, pk=None):
        topic = self.get_object()
        comments = topic.comments.filter(parent=None).select_related('user').prefetch_related('replies__user')
        serializer = serializers.CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        topic_id = self.request.query_params.get('topic_id')
        if topic_id:
            return Comment.objects.filter(topic_id=topic_id, parent=None).select_related('user').prefetch_related('replies__user')
        return Comment.objects.filter(parent=None).select_related('user').prefetch_related('replies__user')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="Lấy danh sách reply của bình luận",
        operation_description="Lấy tất cả reply của một bình luận cụ thể",
        responses={
            200: openapi.Response(
                description="Danh sách reply",
                schema=serializers.CommentSerializer(many=True)
            )
        }
    )
    @action(methods=['get'], detail=True, url_path='replies', permission_classes=[permissions.IsAuthenticated])
    def get_replies(self, request, pk=None):
        comment = self.get_object()
        replies = comment.replies.all().select_related('user')
        serializer = serializers.CommentSerializer(replies, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class LessonProgressViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LessonProgress.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="Cập nhật tiến độ học bài",
        operation_description="Cập nhật tiến độ học của một bài học cụ thể",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'lesson_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID của bài học'),
                'watch_time': openapi.Schema(type=openapi.TYPE_INTEGER, description='Thời gian xem (giây)', default=0),
                'completion_percentage': openapi.Schema(type=openapi.TYPE_NUMBER, description='Phần trăm hoàn thành (0-100)', default=0)
            },
            required=['lesson_id']
        ),
        responses={
            200: openapi.Response(
                description="Cập nhật thành công",
                schema=serializers.LessonProgressSerializer
            ),
            400: openapi.Response(description="Dữ liệu không hợp lệ"),
            403: openapi.Response(description="Không có quyền truy cập"),
            404: openapi.Response(description="Không tìm thấy bài học")
        }
    )
    @action(methods=['post'], detail=False, url_path='update-progress')
    def update_lesson_progress(self, request):
        """Update lesson progress for a specific lesson"""
        lesson_id = request.data.get('lesson_id')
        watch_time = request.data.get('watch_time', 0)
        completion_percentage = request.data.get('completion_percentage', 0)
        
        if not lesson_id:
            return Response({"error": "lesson_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is enrolled in the course
        user_course = UserCourse.objects.filter(
            user=request.user,
            course=lesson.chapter.course,
            status=CourseStatus.IN_PROGRESS
        ).first()
        
        if not user_course:
            return Response({"error": "You are not enrolled in this course"}, status=status.HTTP_403_FORBIDDEN)
        
        # Get or create lesson progress
        lesson_progress, created = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        # Determine status based on completion percentage
        if completion_percentage >= 90:
            status = LessonProgressStatus.COMPLETED
        elif completion_percentage > 0:
            status = LessonProgressStatus.IN_PROGRESS
        else:
            status = LessonProgressStatus.NOT_STARTED
        
        # Update progress
        serializer = serializers.LessonProgressUpdateSerializer(lesson_progress, data={
            'status': status,
            'watch_time': watch_time,
            'completion_percentage': completion_percentage
        })
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializers.LessonProgressSerializer(lesson_progress).data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Lấy tiến độ khóa học",
        operation_description="Lấy tiến độ học tập của user trong một khóa học cụ thể",
        manual_parameters=[
            openapi.Parameter(
                'course_id',
                openapi.IN_PATH,
                description="ID của khóa học",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Thành công",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'course_progress': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Thông tin tiến độ khóa học'
                        ),
                        'lesson_progresses': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description='Danh sách tiến độ các bài học'
                        )
                    }
                )
            ),
            403: openapi.Response(description="Không có quyền truy cập"),
            404: openapi.Response(description="Không tìm thấy khóa học")
        }
    )
    @action(methods=['get'], detail=False, url_path='course/(?P<course_id>[^/.]+)')
    def get_course_progress(self, request, course_id=None):
        """Get progress for all lessons in a course"""
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is enrolled
        user_course = UserCourse.objects.filter(
            user=request.user,
            course=course,
            status=CourseStatus.IN_PROGRESS
        ).first()
        
        if not user_course:
            return Response({"error": "You are not enrolled in this course"}, status=status.HTTP_403_FORBIDDEN)
        
        # Get course progress
        course_progress, created = CourseProgress.objects.get_or_create(
            user=request.user,
            course=course
        )
        course_progress.update_progress()
        
        # Get lesson progress for all lessons in the course
        lesson_progresses = LessonProgress.objects.filter(
            user=request.user,
            lesson__chapter__course=course
        ).select_related('lesson', 'lesson__chapter')
        
        return Response({
            'course_progress': serializers.CourseProgressSerializer(course_progress).data,
            'lesson_progresses': serializers.LessonProgressSerializer(lesson_progresses, many=True).data
        }, status=status.HTTP_200_OK)


class EnrolledCoursesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.EnrolledCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserCourse.objects.filter(
            user=self.request.user,
            status=CourseStatus.IN_PROGRESS
        ).select_related('course').prefetch_related('course__progress')