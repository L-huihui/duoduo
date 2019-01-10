from django.conf.urls import url
from .views import OAuthQQURLView, OAuthQQUserAPIView
urlpatterns = [
    url(r'^qq/statues/$', OAuthQQURLView.as_view()),
    url(r'^qq/users/$', OAuthQQUserAPIView.as_view())
]