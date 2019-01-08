from rest_framework import serializers
from django_redis import get_redis_connection


class RegisterSMSCodeSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=4, min_length=4, required=True)
    image_code_id = serializers.UUIDField(required=True)

    # 验证
    def validate(self, attrs):
        # 1, 获取用户提交的验证码
        text = attrs.get('text')
        # 2, 获取redis中的验证码
        # 2.1 链接redis
        redis_conn = get_redis_connection('code')
        image_id = attrs.get('image_code_id')
        redis_text = redis_conn.get('img_' + str(image_id))
        # 加入redis中取不到数据,表示redis已经过期
        if redis_text is None:
            raise serializers.ValidationError('图片验证码已过期')
        # 3, 进行比对
        # 3.1 redis中的数据是bytes类型
        # 3.2 大小写不一致
        if redis_text.decode().lower() != text.lower():
            raise serializers.ValidationError('验证码输入错误')
        return attrs
