from QQLoginTool.QQtool import OAuthQQ

from django.shortcuts import render

# Create your views here.
# 返回ＱＱ登录网址的视图
# 请求方式：GET:/oquth/qq/status/?state=xxx
from rest_framework import status

from rest_framework.response import Response

from rest_framework.views import APIView
from QQLoginTool.QQtool import OAuthQQ
from rest_framework_jwt.settings import api_settings

from mall import settings
from oauth.models import OAuthQQUser
from oauth.serializer import OAuthQQUserSerializer
from oauth.utils import generic_open_id

'''
当前段点击ＱＱ按钮的时候，会发送一个请求，
我们后端要给它拼接一个url（URL是根据文档拼接的）
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
４，换取到的openid有两种情况，　一种是已经绑定过的一种是未绑定过的
    我们对openid进行判断，查询数据库中是否有此openid值对应的用户信息
    1, 如果有查询到该openid对应的用户信息，就说明该用户已经进行绑定了
       我们直接返回到登录界面，注意也要返回相应的数据（token, username,user_id）
    2, 如果没有查询到对应的用户信息，就返回到绑定页面，并且将openid也返回给前端
    3, 因为openid非常重要，可以由openid拿到用户信息，所以我们在返回openid给前端
    的时候要将openid进行加密处理，在后端拿到openid后进行解密处理，
'''
'''
如果token被篡改了是会检测到的
如果token过期了会报异常
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
            # 对openid进行加密处理
            token = generic_open_id(openid)
            return Response({'access_token': token})
        else:
            # 数据库中有该数据，直接返回数据
            # 生成token

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(qquser.user)
            token = jwt_encode_handler(payload)

            return Response({
                'token': token,
                'username': qquser.user.username,
                'user_id': qquser.user.id
            })

    '''
    当用户点击绑定的时候，前段将用户手机号，　密码，　短信验证码和加密的openid传递到后端
    １，　后端接收数据
    ２，　对数据进行校验
    ３，　保存数据
    ４，　返回响应
    请求方式：post   /oauth/qq/users/
    '''

    def post(self, request):
        # １，　后端接收数据
        data = request.data
        # ２，　对数据进行校验
        serializer = OAuthQQUserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # ３，　保存数据
        qquser = serializer.save()
        # ４，　返回响应
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(qquser.user)
        token = jwt_encode_handler(payload)
        return Response({
            'token': token,
            'username': qquser.user.username,
            'user_id': qquser.user.id
        })


'''
# 对返回给前段的openid进行加密处理
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from mall import settings
# 创建一个序列化器
# 其中两个参数分别是
# secret_key  秘钥
# expires_in　　过期时间
s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
# 组织数据
data = {
    'openid':'1234567890'
}
# 让序列化器对数据进行处理
s.dumps(data)
# 得到的结果是二进制的数据，跟token是一样的
# b'eyJleHAiOjE1NDcxMTYzOTIsImFsZyI6IkhTMjU2IiwiaWF0IjoxNTQ3MTEyNzkyfQ.eyJvcGVuaWQiOiIxMjM0NTY3ODkwIn0.OSOsJaFAgzwn2EBd_7q2XPt7CsvdCnYYUdSxk0oOKsA'
# 获取数据对数据进行解密
s.loads(data)
'''
