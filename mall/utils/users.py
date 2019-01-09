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


class UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)
        if user is not None and user.check_password(password):
            return user
        return None