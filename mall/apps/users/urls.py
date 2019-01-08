from django.conf.urls import url
from . import views


urlpatterns = [
   url(r'^usernames/(?P<username>\w{5,20})/count/$',views.RegisterUsernameCountAPIView.as_view(),name='usernamecount'),
   url(r'^phones/(?P<mobile>1[345789]\d{9})/count/$', views.RegisterPhoneCountAPIView.as_view(), name='mobilecount'),
   url(r'^$', views.RegisterCreateView.as_view(), name='register'),
]