from django.urls import path, include

from . import views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')
router.register('courses', views.CourseViewSet, basename='course')
router.register('chapters', views.ChapterViewSet, basename='chapter')
router.register('lessons', views.LessonViewSet, basename='lesson')
router.register('users', views.UserViewSet, basename='user')
router.register("teachers", views.TeacherViewSet, basename='teacher')
router.register('enrollments', views.UserCourseViewSet, basename='enrollments')
router.register('forums', views.ForumViewSet, basename='forums')
router.register('topics', views.TopicViewSet, basename='topics')
router.register('comments', views.CommentViewSet, basename='comments')
router.register('lesson-progress', views.LessonProgressViewSet, basename='lesson-progress')
router.register('enrolled-courses', views.EnrolledCoursesViewSet, basename='enrolled-courses')

urlpatterns = [
    path('', include(router.urls)),
    path('payment/momo/ipn/', views.MomoIPNViewSet.as_view(), name='momo-ipn'),
    path('forget-password/', views.ForgotPasswordView.as_view(), name='forget-password'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),

]