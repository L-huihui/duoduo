from django.conf.urls import url
from . import views
from rest_framework_jwt.views import obtain_jwt_token

urlpatterns = [
   url(r'^usernames/(?P<username>\w{5,20})/count/$', views.RegisterUsernameCountAPIView.as_view(), name='usernamecount'),
   url(r'^phones/(?P<mobile>1[345789]\d{9})/count/$', views.RegisterPhoneCountAPIView.as_view(), name='mobilecount'),
   url(r'^$', views.RegisterCreateView.as_view(), name='register'),
   url(r'^auths/', views.UserAuthorizationView.as_view(), name='auths'),
   url(r'^infos/$', views.UserDetailView.as_view(), name='infos'),
   url(r'^emails/$', views.EmailView.as_view(), name='send_mail'),
   url(r'^emails/verification/$', views.VerificationEmailView.as_view()),

   # url(r'^(?P<username>1[3-9]\d{9})/sms/token/$', views.FindUserPassword.as_view()),
   #  url(r'^sms_codes/$',views.RegisterSMSCodeView.as_view()),
   #  url(r'^(?P<username>1[3-9]\d{9})/password/token/$', views.SendPassword.as_view()),
   #  url(r'^(?P<user_id>\d+)/password/$', views.CheakPassword.as_view()),

   url(r'^(?P<username>1[345789]\d{9})/sms/token/$', views.FindPassWordAPIView.as_view()),
   url(r'^sms_codes/$', views.GetTokenAPIView.as_view()),
   url(r'^(?P<username>1[345789]\d{9})/password/token/$', views.SendSmsAPIView.as_view()),
   url(r'^(?P<user_id>\d+)/password/$', views.SetPassWordAPIView.as_view()),

   # /users/browerhistories/
   url(r'^browerhistories/$', views.UserBrowsingHistoryView.as_view(), name='history'),
   #/users/browerhistories/
   # url(r'^browerhistories/$', views.UserBrowsingHistoryView.as_view(),name='history'),
]
from .views1 import AddressViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'addresses',AddressViewSet,base_name='address')
urlpatterns += router.urls