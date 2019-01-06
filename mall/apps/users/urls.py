from django.conf.urls import url
from . import views


urlpatterns = [
   # url(r'^usernames/(?P<username>\w{5, 20})/count/$', views.RegisterUsernameCountAPIView.as_view(), name='usernamecount'),
   url(r'^usernames/(?P<username>\w{5,20})/count/$', views.RegisterUsernameCountAPIView.as_view(),name='usernamecount'),

]