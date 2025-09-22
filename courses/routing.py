from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/forum/topic/(?P<topic_id>\d+)/$', consumers.ForumConsumer.as_asgi()),
]