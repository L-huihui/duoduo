from django.conf import settings
from urllib.parse import urlencode, parse_qs
import json
import requests


class OAuthSina(object):
    """
    sina认证辅助工具类
    """

    def __init__(self, client_id=None, grant_type=None,client_secret=None, redirect_uri=None, state=None,scope=None,response_type=None,screen_name=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state = state   # 用于保存登录成功后的跳转页面路径
        self.scope=scope
        # self.response_type= response_type
        # self.screen_name =screen_name
        # self.grant_type=grant_type
    def get_sina_url(self):
        # Sina登录url参数组建
        data_dict = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'scope=':self.scope,


        }

        # 构建url
        sina_url = 'https://api.weibo.com/oauth2/authorize?' + urlencode(data_dict)

        return sina_url
    def sina_url(self):
        # Sina登录url参数组建
        data_dict = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'scope=':self.scope,


        }

        # 构建url
        sina_url = 'https://api.weibo.com/oauth2/get_token_info?' + urlencode(data_dict)

        return sina_url
    # 获取access_token值
    def get_access_token(self, code):
        # 构建参数数据
        data_dict = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': code
        }

        # 构建url
        # access_url = 'https://graph.qq.com/oauth2.0/token?' + urlencode(data_dict)
        access_url = 'https://api.weibo.com/oauth2/access_token?' + urlencode(data_dict)

        # 发送请求
        try:
            response = requests.post(access_url)

            # 提取数据
            # access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14
            data = response.text

            # 转化为字典
            data = parse_qs(data)
        except:
            raise Exception('Sina请求失败')

        # 提取access_token
        access_token = data.get('access_token', None)

        if not access_token:
            raise Exception('access_token获取失败')

        return access_token[0]

    # 获取open_id值

    def get_open_id(self, access_token):

        # 构建请求url
        url = 'https://api.weibo.com/oauth2/get_token_info=' + access_token

        # 发送请求
        try:
            response = requests.get(url)

            # 提取数据
            # callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} );
            # code=asdasd&msg=asjdhui  错误的时候返回的结果
            data = response.text
            data = data[10:-3]
        except:
            raise Exception('Sina请求失败')
        # 转化为字典
        try:
            data_dict = json.loads(data)
            # 获取openid
            openid = data_dict.get('openid')
        except:
            raise Exception('openid获取失败')

        return url
