from rest_framework import viewsets, generics, status, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
import hmac, hashlib
from courses.models import Category, Course, User, Role, UserCourse, Forum, Comment
from courses import serializers, paginators
from .perms import IsAdmin, IsStudent, IsTeacher
from .services.momo import create_momo_payment, update_status_user_course


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Category.objects.filter(active=True)
    serializer_class = serializers.CategorySerializer


class CourseViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Course.objects.filter(active=True)
    serializer_class = serializers.CourseSerializer
    pagination_class = paginators.CoursePagination
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        print("User:", request.user)
        serializer = serializers.CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(lecturer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=True, url_path='forum')
    def get_forum(self, request, pk=None):
        course = self.get_object()
        try:
            forum = course.forum
        except Forum.DoesNotExist:
            return Response({"detail": "Forum not found for this course"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializers.ForumSerializer(forum).data, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]

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

    # Đăng ký học viên
    @action(methods=['post'], detail=False, url_path='register-student')
    def register_student(self, request):
        data = request.data.copy()
        student_role = get_object_or_404(Role, pk=1)
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
        teacher_role = get_object_or_404(Role, pk=2)
        print(teacher_role)
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
        if IsStudent().has_permission(self.request, self):
            return UserCourse.objects.filter(user=user)
        if IsTeacher().has_permission(self.request, self):
            return UserCourse.objects.filter(lecturer=user)
        if IsAdmin().has_permission(self.request, self):
            return UserCourse.objects.all()

    @action(methods=['post'], detail=False, url_path='create', permission_classes=[IsStudent])
    def create_user_course(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user_course = serializer.save()
        pay_url = create_momo_payment(user_course.course.price, user_course.id)

        data = serializer.data
        data['payUrl'] = pay_url
        return Response(data, status=status.HTTP_201_CREATED)

class MomoIPNViewSet(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        user_course_id = data['extraData']

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

        # tạo chữ ký số
        signature = hmac.new(
            'K951B6PE1waDMi640xX08PD3vg6EkVlz'.encode("utf-8"),
            raw_signature.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        # xác thực chữ
        if signature != data.get("signature"):
            return Response({"message": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        # thanh toán thành công
        if data["resultCode"] == 0:
            update_status_user_course(user_course_id, True)
            return Response({"message": "Payment success"}, status=status.HTTP_200_OK)
        # thanh toán thất bại
        else:
            update_status_user_course(user_course_id, False)
            return Response({"message": "Payment failed"}, status=status.HTTP_200_OK)


class ForumViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    serializer_class = serializers.ForumSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        user = self.request.user
        if IsTeacher().has_permission(self.request, self):
            return Forum.objects.filter(user=user)
        elif IsAdmin().has_permission(self.request, self):
            return Forum.objects.all()


class CommentViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    serializer_class = serializers.CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(parent=None)

    @action(methods=['get'], detail=True, url_path='replies', permission_classes=[permissions.IsAuthenticated])
    def get_replies(self, request, pk=None):
        comment = self.get_object()
        try:
            relies = comment.replies
        except Comment.DoesNotExist:
            return Response('Comment not found relies', status=status.HTTP_200_OK)
        return Response(serializers.CommentSerializer(relies, many=True).data, status=status.HTTP_200_OK)

