from django.shortcuts import render

# Create your views here.
# 验证用户名
from rest_framework.response import Response
from rest_framework.views import APIView


# 请求方式GET    /users/usernames/(?P<username>\w{5, 20})/count/
from users.models import User


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

