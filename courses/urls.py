

from django.urls import path, include
from . import views
from rest_framework import routers




r = routers.DefaultRouter()





urlpatterns = [
    path('', include(r.urls)),

]
