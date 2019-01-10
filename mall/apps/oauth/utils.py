# 对返回给前端的数据openid进行加密处理
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from mall import settings


def generic_open_id(openid):
    # 创建一个序列化器
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
    # 对数据进行处理
    token = s.dumps({
        'openid': openid
    })
    return token.decode()

    # 对后端拿到的openid数据进行解密处理
