from django.shortcuts import render

# Create your views here.
from django.views.generic import CreateView

from rest_framework.response import Response
from rest_framework.views import APIView

# 请求方式GET    /users/usernames/(?P<username>\w{5, 20})/count/
from users.models import User
'''
前端在填写完用户名的时候,会将用户名传递给后端,通过get方式存放在url中
后端操作:
1, 获取到前端传递过来的用户名
2, 查询数据库中该用户名在数据库中同名的个数
3, 组织数据,将前段需要的数据组织起来
4, 返回响应
'''

# 验证用户名
from users.serializer import RegisterCreateSerializer


class RegisterUsernameCountAPIView(APIView):
    def get(self, request, username):
        # 通过用户名查询数据库该用户名的个数
        count = User.objects.filter(username=username).count()
        # 将数据组织返回给前端
        context = {
            'count': count,
            'username': username
        }
        return Response(context)


# 判断手机号是否存在
# 请求方式:请求方式： GET /users/mobiles/(?P<mobile>1[345789]\d{9})/count/

class RegisterPhoneCountAPIView(APIView):
    def get(self, request, mobile):
        '''
        1, 获取前端传递过来的手机号
        2, 查询数据库中该手机号的个数
        3, 组织数据返回给前端
        '''
        # 1, 获取前端传递过来的手机号
        # 2, 查询数据库中该手机号的个数
        count = User.objects.filter(mobile=mobile)
        # 3, 组织数据返回给前端
        context = {
            'count': count,
            'mobiles': mobile
        }
        return Response(context)


# 创建注册视图
# 前段将用户名, 密码,第二次输入的密码, 短信验证码, 手机号, 是否同意用户协议
# 请求路径:post/users/
'''
在用户点击注册按钮的时候,前段使用表单的方式将用户名,密码,再次输入的密码,
短信验证码,手机号,是否同意协议(布尔类型值)传递给后端
后端接收到前段传递过来的数据,创建序列化器,对数据进行格式转化,并且对数据进行校验
如果数据校验没有问题就会讲数据保存到数据库
1, 接收前端传递过来的数据
2, 将数据传入到序列化器中进行校验
3, 数据校验正确后将数据保存到数据库
4, 返回响应
'''
class RegisterCreateView(APIView):

    def post(self, request):
        # 1. 接收数据
        data = request.data
        # 2. 校验数据
        serializer = RegisterCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3. 数据入库
        serializer.save()
        # 4. 返回相应
        return Response(serializer.data)
