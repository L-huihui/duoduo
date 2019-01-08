import re

from rest_framework import serializers
from django_redis import get_redis_connection
from users.models import User


class RegisterCreateSerializer(serializers.ModelSerializer):
    # 自己定义字段
    sms_code = serializers.CharField(label='短信验证码', max_length=6, min_length=6, required=True, allow_blank=False)
    allow = serializers.CharField(label='是否同意协议', required=True, allow_blank=False)
    password2 = serializers.CharField(label='确认密码', required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ['mobile', 'username', 'password', 'sms_code', 'allow', 'password2']

    extra_kwargs = {
        'id': {'read_only': True},
        'username': {
            'min_length': 5,
            'max_length': 20,
            'error_messages': {
                'min_length': '仅允许5-20个字符的用户名',
                'max_length': '仅允许5-20个字符的用户名',
            }
        },
        'password': {
            'write_only': True,
            'min_length': 8,
            'max_length': 20,
            'error_messages': {
                'min_length': '仅允许8-20个字符的密码',
                'max_length': '仅允许8-20个字符的密码',
            }
        }
    }

    # 校验单个字段,校验手机号是否符合规范
    def validate_mobile(self, value):
        if not re.match(r'1[3-9]\d{9}', value):
            raise serializers.ValidationError('手机号不符合规范')
        return value

    # 校验单个字段,协议是否同意
    def validated_allow(self, value):
        if value != 'true':
            raise serializers.ValidationError('没有同意协议')
        return value

    # 多个字段的校验, 校验两次密码输入是否一致
    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError('两次输入的密码不一致')
        # 判断用户提交的短信验证码是否与redis中存储的一致
        # 获取用户提交的电话号码与短信验证码
        mobile = attrs.get('mobile')
        sms_code = attrs.get('sms_code')
        # 获取redis中短信验证码
        redis_conn = get_redis_connection('code')
        redis_code = redis_conn.get('sms_' + mobile)
        if redis_code is None:
            raise serializers.ValidationError('短信验证码已过期')
        # 校验完成后删除短信验证码
        # redis_conn.delete('sms_' + mobile)
        # # 验证短信验证码是否一致
        if redis_code.decode() != sms_code:
            raise serializers.ValidationError('验证码不一致')

        return attrs

    def create(self, validated_data):
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user