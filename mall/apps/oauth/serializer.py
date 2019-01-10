from django_redis import get_redis_connection
from rest_framework import serializers

from oauth.models import OAuthQQUser
from oauth.utils import check_access_token
from users.models import User


class OAuthQQUserSerializer(serializers.Serializer):
    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    def validate(self, attrs):
        # 对加密的openid进行解密处理
        access_token = attrs.get('access_token')
        openid = check_access_token(access_token)
        # 对openid进行校验，如果open是空的就抛出异常
        if openid is None:
            raise serializers.ValidationError('openid错误')
        attrs['openid'] = openid
        # 对短信进行校验
        mobile = attrs.get('mobile')
        sms_code = attrs.get('sms_code')
        # 获取redis中短信验证码
        redis_conn = get_redis_connection('code')
        redis_code = redis_conn.get('sms_' + mobile)
        if redis_code is None:
            raise serializers.ValidationError('短信验证码已过期')
        # 校验完成后删除短信验证码
        redis_conn.delete('sms_' + mobile)
        # # 验证短信验证码是否一致
        if redis_code.decode() != sms_code:
            raise serializers.ValidationError('验证码不一致')
        # 对手机号进行校验
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 没有查询到该电话号码对应的用户，说明没有注册过创建用户

            pass
        else:
            # 说明注册过,注册过需要对密码进行校验
            if user.check_password('password'):
                raise serializers.ValidationError('密码输入错误')
            attrs['user'] = user

        return attrs

    # 数据流向：request.data---->序列化器---->
    # data --->attrs---->validated_data
    def create(self, validated_data):
        user = validated_data.get('user')
        if user is None:
            # 创建user
            user = User.objects.create(
                mobile=validated_data.get('mobile'),
                username=validated_data.get('mobile'),
                password=validated_data.get('password')
            )
            # 对密码进行加密
            user.set_password(validated_data['password'])
            user.save()
        qquser = OAuthQQUser.objects.create(
            user=user,
            openid=validated_data.get('openid')
        )
        return qquser
