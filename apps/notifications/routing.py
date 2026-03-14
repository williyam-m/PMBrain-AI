from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/project/(?P<project_id>[^/]+)/$', consumers.PMBrainConsumer.as_asgi()),
    re_path(r'ws/updates/$', consumers.PMBrainConsumer.as_asgi()),
]
