from django.conf.urls import url
from .views import OAuthQQURLView, OAuthQQUserAPIView,OauthSina,OauthSinaUserAPIView
urlpatterns = [
    url(r'^qq/statues/$', OAuthQQURLView.as_view()),
    url(r'^qq/users/$', OAuthQQUserAPIView.as_view()),
    url(r'^sina/user/$', OauthSinaUserAPIView.as_view()),
    url(r'^sina/statues/$', OauthSina.as_view()),
]