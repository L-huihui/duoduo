from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django.shortcuts import render

# Create your views here.
# 返回ＱＱ登录网址的视图
# 请求方式：GET:/oquth/qq/status/?state=xxx
from rest_framework.response import Response
from rest_framework.views import APIView


class QQAuthURLView(APIView):
    '''提供ＱＱ登录页面网址'''
    def get(self, request):
        # next表示从那个页面进入到的登录页面，　将来登录成功后，就自动回到那个页面
        state = request.query_params.get('state')
        if not state:
            state = '/'
        # 获取ＱＱ登录页面网址
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET, redirect_uri=settings.QQ_REDIRECT_URI, state=state)
        login_url = oauth.get_qq_url()
        return Response({'login_url':login_url})
    pass