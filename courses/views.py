from rest_framework import viewsets, generics, status, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from courses.models import Category, Course, User
from courses import serializers, paginators, perms

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

class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]

    def get_serializer_class(self):
        if self.action == 'register':
            return serializers.UserRegistrationSerializer
        return serializers.UserSerializer

    def get_permissions(self):
        if self.action in ['register']:
            return [permissions.AllowAny()]
        elif self.action in ['get_current_user']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @action(methods=['post'], detail=False, url_path='register')
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            return Response({
                'message': 'Đăng ký tài khoản thành công!',
                'user': serializers.UserSerializer(user).data,
                'note': 'Vui lòng sử dụng endpoint /o/token/ để lấy access token sau khi đăng ký'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get', 'patch'], url_path='current-user', detail=False, permission_classes = [permissions.IsAuthenticated])
    def get_current_user(self, request):
        u = request.user
        if request.method.__eq__('PATCH'):
            for k, v in request.data.items():
                if k in ['first_name', 'last_name']:
                    setattr(u, k, v)
                elif k.__eq__('password'):
                    u.set_password(v)

            u.save()

        return Response(serializers.UserSerializer(u).data)