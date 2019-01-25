from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^imagecodes/(?P<image_code_id>.+)/$',views.RegisterImageCodeViews.as_view(),name='imagecode'),
    url(r'^sms_codes/(?P<mobile>1[345789]\d{9})/$', views.RegisterSMSCodeView.as_view(), name='smscode'),

]