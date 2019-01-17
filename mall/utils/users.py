import re

from django.contrib.auth.backends import ModelBackend

from users.models import User


def jwt_response_payload_handler(token, user=None, request=None):
    # token ＪＷＴ生成的
    # user = None jwt 验证成功之后的user
    # request = None  请求
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username,
    }


def get_user_by_account(username):
    try:
        if re.match(r'1[345789]\d{9}', username):
            user = User.objects.get(mobile=username)
        else:
            user = User.objects.get(username=username)
    except User.DoseNotExist:
        user = None
    return user


'''
１, 获取用户输入的账户框里的信息
２，用正则对获取的信息进行匹配，如果匹配到的是电话号码，
    就在数据库中进行查询到该用户信息
３，如果不是电话号码那就是用户名，查询数据库中该用户的信息
４，再进行判断，如果数据库中查询到用户数据不为空并且对密码进行校验是正确的
    那么就返回用户信息，登录成功
'''


class UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)
        if user is not None and user.check_password(password):
            return user
        return None
