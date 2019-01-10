from QQLoginTool.QQtool import OAuthQQ

from django.shortcuts import render

# Create your views here.
# 返回ＱＱ登录网址的视图
# 请求方式：GET:/oquth/qq/status/?state=xxx
from rest_framework import status

from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from QQLoginTool.QQtool import OAuthQQ

from mall import settings
from oauth.models import OAuthQQUser

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
在用户通过扫码同意授权之后认证服务器会返回一个code给前端
前端会将code以GET的形式发送给后端，后端接收到code
１，　后端接收code
２，　后端讲code发送给认证服务器换取token
３，　将tokrn发送给认证服务器换取openid
    openid是此网站上唯一对应用户身份的标识，网站可将此ID进行
    存储便于用户下次登录时辨识其身份，或将其与用户在网站上
    的原有账号进行绑定。
４，获取到的openid有两种情况，　一种是已经绑定过的一种是未绑定过的

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
        # ４，查询数据库中openid的数据，
        # 如果有就说明用户已经绑定了  就让用户直接登录
        # 如果没有数据就说明用户没有绑定　　就绑定用户信息
        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 数据库中没有查找到该数据, 绑定用户信息
            return Response({'access_token':openid})

            pass
        else:
            # 数据库中有该数据，直接返回数据
            # 生成token
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(qquser.user)
            token = jwt_encode_handler(payload)

            return Response({
                'token':token,
                'username':qquser.user.username,
                'user_id':qquser.user.id
            })
            pass

