import random

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from rest_framework.views import APIView
from django_redis import get_redis_connection

# 图片验证码
# 请求方式: GET /verifications/imagecodes/(?P<image_code_id>.+)/
from libs.captcha.captcha import captcha
from libs.yuntongxun.sms import CCP
from verifications.serializer import RegisterSMSCodeSerializer


class RegisterImageCodeViews(APIView):
    '''
    1.分析需求 (到底要干什么)
    2.把需要做的事情写下来(把思路梳理清楚)
    3.请求方式 路由
    4.确定视图
    5.按照步骤实现功能

    前端传递一个 uuid过来 ,我们后端生成一个图片

    1.接收 image_code_id
    2.生成图片和验证码
    3.把验证码保存到redis中
    4.返回图片相应
    '''
    '''
    前端传递过来一个UUID,后端接收到之后在后端生成图片验证码,
    连接redis, 将UUID作为Key图片验证码中的验证信息作为value
    存储在redis中,然后将图片验证码返回给前端
    1, 接收前端生成的UUID
    2, 生成图片验证码
    3, 连接redis并且将图片验证码作为value,生成的uuid作为key
    存储在reids中
    4, 返回图片验证码给前段(注意:要修改content_type='image/jpeg')
    '''

    def get(self, request, image_code_id):
        # 1.接收 image_code_id
        # 2.生成图片和验证码
        text, image = captcha.generate_captcha()
        # 3.把验证码保存到redis中
        # 3.1 先链接redis
        redis_conn = get_redis_connection('code')
        # 3.2 将图片验证码保存到redis中
        redis_conn.setex('img_%s' % image_code_id, 60, text)
        # 4.返回图片相应
        # 一定要对图片的返回类型进行设置,要不然会返回一些乱码格式
        return HttpResponse(image, content_type='image/jpeg')


# 短信验证码
# 请求方式:GET /verifications/smscodes/(?P<mobile>1[345789]\d{9})/?text=xxxx & image_code_id=xxxx
'''
1.分析需求 (到底要干什么)
2.把需要做的事情写下来(把思路梳理清楚)
3.请求方式 路由
4.确定视图
5.按照步骤实现功能


当用户点击 获取短信按钮的时候 前端应该将 手机号,
图片验证码以及验证码id发送给后端
1.接收参数
2.校验参数
3.生成短信
4.将短信保存在redis中
5.使用云通讯发送短信
6.返回相应

GET             /verifications/smscodes/(?P<mobile>1[345789]\d{9})/?text=xxxx & image_code_id=xxxx
一种是 路由  weather/beijing/2018/
另外一个是 查询字符串 weather/?place=beijing&year=2018
混合起来也是可以的
        weather/2018/?place=beijing
'''


class RegisterSMSCodeView(GenericAPIView):
    serializer_class = RegisterSMSCodeSerializer

    def get(self, requset, mobile):
        # 1.接收参数
        parmas = requset.query_params
        # 2.校验参数
        serializer = RegisterSMSCodeSerializer(data=parmas)
        serializer.is_valid(raise_exception=True)
        # 3.生成短信
        sms_code = '%06d'%random.randint(0,999999)
        # 4.将短信保存在redis中
        redis_conn = get_redis_connection('code')
        redis_conn.setex('sms_'+mobile, 5*60, sms_code)
        # 5.使用云通讯发送短信
        # CCP().send_template_sms(mobile, [sms_code,5], '1')
        # # 6.返回相应
        # return HttpResponse({'msg':'ok'})
        from celery_tasks.sms.tasks import send_sms_code
        # delay 的参数和 任务的参数对应
        # 必须调用 delay 方法
        send_sms_code.delay(mobile, sms_code)

        # 6.返回相应
        return Response({'msg': 'ok'})
