from django.conf.urls import url
from . import views
from rest_framework_jwt.views import obtain_jwt_token

urlpatterns = [
    #/users/usernames/(?P<username>\w{5,20})/count/
    url(r'^usernames/(?P<username>\w{5,20})/count/$',views.RegisterUsernameAPIView.as_view(),name='usernamecount'),

    url(r'^$',views.RegiserUserAPIView.as_view()),

    #实现登陆
    url(r'^auths/',obtain_jwt_token),
    # jwt 把用户名和密码给系统,让系统进行认证,认证成功之后jwt 生成token

    #
    url(r'^infos/$',views.UserCenterInfoAPIView.as_view()),

    # users/emails/
    url(r'^emails/$',views.UserEmailInfoAPIView.as_view()),

    url(r'^emails/verification/$',views.UserEmailVerificationAPIView.as_view()),


    url(r'^addresses/$',views.UserAddressAPIView.as_view()),

    #/users/browerhistories/
    url(r'^browerhistories/$',views.UserHistoryAPIView.as_view()),
]

"""
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.
eyJ1c2VybmFtZSI6Iml0Y2FzdCIsImV4cCI6MTU0NzAwMDQxNCwiZW1haWwiOiIiLCJ1c2VyX2lkIjo4fQ.
HVw9FkI7gXxobEtMWJ9t4QXsBbV54l4rA5ehddwqnZ4
"""