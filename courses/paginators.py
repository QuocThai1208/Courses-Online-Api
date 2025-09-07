from rest_framework.pagination import PageNumberPagination


class CoursePagination(PageNumberPagination):
    page_size = 8

class ChapterPagination(PageNumberPagination):
    page_size = 6

class LessonPagination(PageNumberPagination):
    page_size = 8