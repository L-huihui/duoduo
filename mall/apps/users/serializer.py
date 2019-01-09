import re

from rest_framework import serializers
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from users.models import User

'''
1,创建序列化器,继承自ModelSerializer,model设置为User
2,将User中没有的字段添加上去,并且对字段进行约束设置
3,对字段进行校验
    3.1, 校验单个字段(validated+字段名)
        3.1.1 校验前段传递过来的手机号码是否符合规范
        3.1.2 校验用户在点击注册时的用户协议字段的值allow是否为Ture(同意)
              因为只有当用户同意协议的时候才能注册账号成功
    3.2, 多个字段的校验(validated)
        3.2.1 校验两次输入的密码是否一致
        3.2.2 校验用户输入的短信验证码是否正确
              1, 获取前端用户输入的短信验证码
              2, 连接redis,取出保存在redis中的短信验证码
              3, 判读如果没有从redis中取出对应的短信验证码,
                返回短信验证码过期提示
              4, 对用户输入的验证码和redis中保存的验证码进行对比验证
    3.3, 父类的create方法不能满足因为当前的数据太多,父类中没有个某些字段,
        因此我们重写create方法
        3.3.1, 删除模型中没有的字段数据
        3.3.2, 删除完模型中没有的字段后数据可以满足父类的create方法
        3.3.3, 调用父类的create方法
        3.3.4, 当前的密码是明文保存,为了安全起见,我们将密码进行加密
        3.3.5, 保存数据
        3.3.6, 返回响应
4, 返回传入到序列化器中的数据

'''


class RegisterCreateSerializer(serializers.ModelSerializer):
    # 自己定义字段 write_only 只是在反序列化的时候使用,在序列化的时候不使用该字段
    sms_code = serializers.CharField(label='短信验证码', max_length=6, min_length=6, required=True, write_only=True,
                                     allow_blank=False)
    allow = serializers.CharField(label='是否同意协议', required=True, allow_blank=False, write_only=True)
    password2 = serializers.CharField(label='确认密码', required=True, allow_blank=False, write_only=True)
    token = serializers.CharField(label='token',read_only=True)
    class Meta:
        model = User
        fields = ['mobile', 'username', 'token','password', 'sms_code', 'allow', 'password2']
    # 在返回的数据中不能有密码,应该对密码字段几你选那设置为只读模式
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
        '''
        父类的create方法不能满足因为当前的数据太多,父类中没有个某些字段,
        因此我们重写create方法
        1, 删除模型中没有的字段数据
        2, 删除完模型中没有的字段后数据可以满足父类的create方法
        3, 调用父类的create方法
        4, 当前的密码是明文保存,为了安全起见,我们将密码进行加密
        5, 保存数据
        6, 返回响应
        '''

    def create(self, validated_data):
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        user = super().create(validated_data)
        # 当前的密码是明文保存,为了安全起见,我们将密码进行加密
        user.set_password(validated_data['password'])
        user.save()
        # 补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token
        return user
