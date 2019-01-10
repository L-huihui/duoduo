from QQLoginTool.QQtool import OAuthQQ

from django.shortcuts import render

# Create your views here.
# 返回ＱＱ登录网址的视图
# 请求方式：GET:/oquth/qq/status/?state=xxx
from rest_framework import status

from rest_framework.response import Response
from rest_framework.views import APIView
from QQLoginTool.QQtool import OAuthQQ

from mall import settings

'''
class QQAuthURLView(APIView):


    def get(self, request):
        # next表示从那个页面进入到的登录页面，　将来登录成功后，就自动回到那个页面
        state = request.query_params.get('state')
        if not state:
            state = '/'
        # 获取ＱＱ登录页面网址
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=state)
        login_url = oauth.get_qq_url()
        return Response({'login_url': login_url})

'''
'''
当前段点击ＱＱ按钮的时候，会发送一个请求，
我们后端要给它拼接一个ｕｒｌ（URL是根据文档拼接的）
请求方式:/oauth/qq/status/

'''


class OAuthQQURLView(APIView):
    def get(self, request):
        state = '/'
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=state)
        login_url = oauth.get_qq_url()
        return Response({'login_url': login_url})


'''
1, 用户同意授权登录的时候（用户扫码确认登录的时候），会返回一个code
2, 我们用code换取ｔｏｋｅｎ
3, 有了token 然后再换取openid
'''
'''
前端接收到用户同意之后的code ,前段讲code发送给后端
１，接收这个code数据
2, 用code换ｔｏｋｅｎ
３，用token换openid
请求方式：　／oauth/qq/users/
'''


class OAuthQQUserAPIView(APIView):
    def get(self, request):
        # １，接收这个code数据
        params = request.query_params
        code = params.get('code')
        # 2, 用code换ｔｏｋｅｎ
        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        )
        token = oauth.get_access_token(code)
        # ３，用token换openid
        openid = oauth.get_open_id(token)
        pass
