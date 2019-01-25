from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature
from mall import settings


# 对返回给前端的数据openid进行加密处理
def generic_open_id(access_token):
    # 创建一个序列化器
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
    # 对数据进行处理
    token = s.dumps({
        'access_token': access_token
    })
    return token.decode()


# 对后端拿到的openid数据进行解密处理
def check_access_token(access_token):
    # 创建序列化器
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
    # 对数据进行loads操作
    try:
        data = s.loads(access_token)
    except BadSignature:
        return None
    # 返回openid
    return data['access_token']
