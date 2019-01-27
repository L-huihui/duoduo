import random
import re
from django.shortcuts import render

# Create your views here.
from django.views.generic import CreateView
from django_redis import get_redis_connection
from itsdangerous import BadData
from itsdangerous import Serializer
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, CreateAPIView, ListAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.views import APIView

# 请求方式GET    /users/usernames/(?P<username>\w{5, 20})/count/
from rest_framework.viewsets import GenericViewSet

from rest_framework_jwt.views import ObtainJSONWebToken

from contents.migrations.meiduo_34.mall.libs.yuntongxun.sms import CCP
from goods.models import SKU
from goods.serializer import SKUSerializer
from users.models import User, Address
from carts.utils import merge_cookie_to_redis
from utils.users import get_user_by_account

'''
前端在填写完用户名的时候,会将用户名传递给后端,通过get方式存放在url中
后端操作:
1, 获取到前端传递过来的用户名
2, 查询数据库中该用户名在数据库中同名的个数
3, 组织数据,将前段需要的数据组织起来
4, 返回响应
'''

# 验证用户名
from users.serializer import RegisterCreateSerializer, UserDetailSerializer, EmailSerializer, AddressSerializer, \
    AddressTitleSerializer, AddUserBrowsingHistorySerializer


class RegisterUsernameCountAPIView(APIView):
    def get(self, request, username):
        # 通过用户名查询数据库该用户名的个数
        count = User.objects.filter(username=username).count()
        # 将数据组织返回给前端
        context = {
            'count': count,
            'username': username
        }
        return Response(context)


# 判断手机号是否存在
# 请求方式:请求方式： GET /users/mobiles/(?P<mobile>1[345789]\d{9})/count/

class RegisterPhoneCountAPIView(APIView):
    def get(self, request, mobile):
        '''
        1, 获取前端传递过来的手机号
        2, 查询数据库中该手机号的个数
        3, 组织数据返回给前端
        '''
        # 1, 获取前端传递过来的手机号
        # 2, 查询数据库中该手机号的个数
        count = User.objects.filter(mobile=mobile)
        # 3, 组织数据返回给前端
        context = {
            'count': count,
            'mobiles': mobile
        }
        return Response(context)


# 创建注册视图
# 前段将用户名, 密码,第二次输入的密码, 短信验证码, 手机号, 是否同意用户协议
# 请求路径:post/users/
'''
在用户点击注册按钮的时候,前段使用表单的方式将用户名,密码,再次输入的密码,
短信验证码,手机号,是否同意协议(布尔类型值)传递给后端
后端接收到前段传递过来的数据,创建序列化器,对数据进行格式转化,并且对数据进行校验
如果数据校验没有问题就会讲数据保存到数据库
1, 接收前端传递过来的数据
2, 将数据传入到序列化器中进行校验
3, 数据校验正确后将数据保存到数据库
4, 返回响应
'''


class RegisterCreateView(APIView):
    def post(self, request):
        # 1. 接收数据
        data = request.data
        # 2. 校验数据
        serializer = RegisterCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3. 数据入库
        serializer.save()
        # 4. 返回相应
        return Response(serializer.data)


class UserDetailView(RetrieveAPIView):
    '''获取登录用户的信息'''
    # 添加认证信息
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer

    # 重写get_object方法：
    def get_object(self):
        return self.request.user


# 邮箱
class EmailView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmailSerializer

    def get_object(self):
        return self.request.user


class VerificationEmailView(APIView):
    """
    验证激活邮箱
    GET /users/emails/verification/?token=xxxx

    思路:
    获取token,并判断
    获取 token中的id
    查询用户,并判断是否存在
    修改状态
    返回响应
    """

    def get(self, request):
        # 获取token, 并判断
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)
        # 获取token中的id,email
        # 查询用户, 并判断是否存在
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message': '链接无效'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # 修改状态
            user.email_active = True
            user.save()
            # 返回响应
            return Response({'message': 'ok'})


# 新建收货地址视图
# class UserAddressViewSet(CreateAPIView):
# # class UserAddressViewSet(ListAPIView):
#     # 设置序列化器
#     serializer_class = AddressSerializer
#     # 我们不用queryset因为我们不需要在新建用户地址的之后不用获取每条数据
#
#
#     # queryset = Address.objects.all()

class AddressViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    list GET: /users/addresses/
    create POST: /users/addresses/
    destroy DELETE: /users/addresses/
    action PUT: /users/addresses/pk/status/
    action PUT: /users/addresses/pk/title/
    """

    # 制定序列化器
    serializer_class = AddressSerializer
    # 添加用户权限
    permission_classes = [IsAuthenticated]

    # 由于用户的地址有存在删除的状态,所以我们需要对数据进行筛选
    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        count = request.user.addresses.count()
        if count >= 20:
            return Response({'message': '保存地址数量已经达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        '''获取用户地址列表'''
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        # 设置响应
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': 20,
            'addresses': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        '''
        删除地址
        :param request:
        :param args:
        :param kwargs:
        :return:
        '''
        address = self.get_object()
        # 进行逻辑删除
        address.is_deleted = True
        address.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def title(self, requset, pk=None, address_id=None):
        '''修改标题'''
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=requset.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)


# 添加浏览记录
class UserBrowsingHistoryView(mixins.CreateModelMixin, GenericAPIView):
    """
    用户浏览历史记录
    POST /users/browerhistories/
    GET  /users/browerhistories/
    数据只需要保存到redis中
    """
    serializer_class = AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        保存
        """
        return self.create(request)

    # 生成浏览记录
    def get(self, request):
        """获取"""
        # 获取用户信息
        user_id = request.user.id
        # 连接redis
        redis_conn = get_redis_connection('history')
        # 获取数据
        history_sku_ids = redis_conn.lrange('history_%s' % user_id, 0, 5)
        skus = []
        for sku_id in history_sku_ids:
            sku = SKU.objects.get(pk=sku_id)
            skus.append(sku)
        # 序列化
        serializer = SKUSerializer(skus, many=True)
        return Response(serializer.data)


class UserAuthorizationView(ObtainJSONWebToken):
    def post(self, request, *args, **kwargs):
        # 调用jwt扩展的方法，对用户登录的数据进行验证
        response = super().post(request)

        # 如果用户登录成功，进行购物车数据合并
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 表示用户登录成功
            user = serializer.validated_data.get("user")
            # 合并购物车
            # merge_cart_cookie_to_redis(request, user, response)
            response = merge_cookie_to_redis(request, user, response)

        return response


# 修改密码
class ResetPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        # 1, 先获取前端传递过来的用户
        data = request.data
        # 2， 根据用户id进行数据库查询，查询当前用户信息
        user = User.objects.get(id=pk)
        # 3， 获取用户输入的当前密码， 要修改的密码
        old_password = data.get('old_password')
        password = data.get('password')
        password2 = data.get('password2')
        # 4， 校验当前用户的密码与输入的原密码是否相同
        if not user.check_password(old_password):
            raise Exception('原密码输入错误！')
        else:
            if password != password2:
                raise Exception('两次输入的密码不一致')
            else:
                user.set_password(password2)
                user.save()

        return Response({'message': 'OK'})


from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings


# 生成token
def check_access_token(mobile):
    # serializer = Serializer(秘钥, 有效期秒)
    serializer = Serializer(settings.SECRET_KEY, 3600)
    # serializer.dumps(数据), 返回bytes类型
    token = serializer.dumps({'mobile': mobile})
    token = token.decode()
    return token


# 校验token
def inspect_access_token(token):
    # 检验token
    # 验证失败，会抛出itsdangerous.BadData异常
    serializer = Serializer(settings.SECRET_KEY, 3600)
    try:
        data = serializer.loads(token)
    except BadData:
        return None
    return data


#
# # 忘记密码的第一步图片验证码验证
class FindPassWordAPIView(APIView):
    # GET /users/17611666527/sms/token/?text=pokm&image_code_id=bec7e636-a811-4b48-9749-a7a54c7eda6d

    def get(self, request, username):
        try:
            user = get_user_by_account(username)
        except User.DoesNotExits:
            return Response({'message': '用户不存在'})
        text = request.query_params.get('text')
        image_id = request.query_params.get('image_code_id')
        # 连接redis对数据进行校验
        redis_conn = get_redis_connection('code')
        redis_text = redis_conn.get('img_' + str(image_id))
        if redis_text is None:
            return Response({'message': '图片验证码过期'})
        if redis_text.decode().lower() != text.lower():
            return Response({'message': '图片验证码错误'})
        access_token = check_access_token(mobile=username)
        mobile = user.mobile
        list = mobile[3:7]
        user_mobile = mobile.replace(list, '****')
        data = {
            'mobile': user_mobile,
            'access_token': access_token
        }
        return Response(data)


class GetTokenAPIView(APIView):
    '''发送短信，校验token'''

    def get(self, request):
        token = request.query_params.get('access_token')
        access_token = inspect_access_token(token)
        mobile = access_token['mobile']
        sms_code = '%06d' % random.randint(0, 999999)
        redis_conn = get_redis_connection('code')
        redis_conn.setex('sms_' + mobile, 5 * 60, sms_code)
        from celery_tasks.sms.tasks import send_sms_code
        send_sms_code.delay(mobile, sms_code)

        return Response({'message':'ok'})

class SendSmsAPIView(APIView):
    '''校验输入的短信验证码'''

    def get(self, request, username):

        '''
        校验手机号
        校验短信验证码
        校验access_token
        1, 获取前端传递过来的电话并进行验证
        2， 获取前端传递过来的短信验证码并链接redis进行校验
        3， 获取前端传递过来的access_token 进行校验
        4, 返回响应， user_id, access_token
        '''
        # 3， 获取前端传递过来的access_token 进行校验

            # 1, 获取前端传递过来的电话并进行验证
        try:
            user = get_user_by_account(username)
        except Exception as e:
            return Response('用户不存在')
        mobile = user.mobile
        # 2， 获取前端传递过来的短信验证码并链接redis进行校验
        sms_code = request.query_params.get('sms_code')
        redis_conn = get_redis_connection('code')
        smscode = redis_conn.get('sms_%s' % mobile).decode()
        if sms_code != smscode:
            return Response({'message': '短信验证码输入错误'})
        new_token = check_access_token(mobile=mobile)
        # 4, 返回响应， user_id, access_token
        data = {
            'user_id': user.id,
            'access_token': new_token
        }
        return Response(data)


class SetPassWordAPIView(APIView):
    def post(self, request, user_id):

        token = request.data.get('access_token')
        password = request.data.get('password')
        password2 = request.data.get('password2')
        if inspect_access_token(token):

            # 获取user_id判断用户是否存在
            try:
                user = User.objects.get(id=user_id)
            except Exception as e:
                return Response('用户不存在')
            # 获取T /users/7/passwo前端传递过来的两个密码校验是否一致
            if password != password2:
                return Response({'message': '两次密码输入不一致'})
            user.set_password(password)
            user.save()
            return Response(status=status.HTTP_201_CREATED)



# class FindUserPassword(APIView):
#     def get(self, reqeust, username):
#         try:
#             user = get_user_by_account(username)
#         except:
#             return Response('用户不存在')
#         user_mobile = user.mobile
#         text = reqeust.query_params.get('text')
#         image_id = reqeust.query_params.get('image_code_id')
#
#         redis_conn = get_redis_connection('code')
#         redis_text = redis_conn.get('img_' + str(image_id))
#
#         if redis_text.decode().lower() != text.lower():
#             raise Exception('输入错误')
#
#         token = check_access_token(mobile=user_mobile)
#
#         data = {
#             'mobile': user_mobile,  # 加密
#             'access_token': token,
#         }
#         return Response(data)
#
#
# class RegisterSMSCodeView(APIView):
#     def get(self, request):
#         access_token = request.query_params.get('access_token')
#
#         token = inspect_access_token(access_token)
#
#         mobile = token['mobile']
#
#         redis_conn = get_redis_connection('code')
#         sms_code = '%06d' % random.randint(0, 999999)
#         # redis增加记录
#         redis_conn.setex('sms_%s' % mobile, 5 * 60, sms_code)
#         redis_conn.setex('sms_flag_%s' % mobile, 60, 1)
#         # 发送短信
#         ccp = CCP()
#         ccp.send_template_sms(mobile, [sms_code, 5], 1)
#
#         return Response({'message': 'ok'})
#
#
# class SendPassword(APIView):
#     def get(self, request, username):
#
#         try:
#             user = get_user_by_account(username)
#         except:
#             return Response('用户不存在')
#
#         user_id = user.id
#
#         user_mobile = user.mobile
#
#         sms_code = request.query_params.get('sms_code')
#
#         redis_conn = get_redis_connection('code')
#
#         redis_code = redis_conn.get('sms_' + str(user_mobile)).decode()
#
#         if sms_code != redis_code:
#             raise Exception('验证码输入错误操你妈的')
#
#         access_token = check_access_token(mobile=user_mobile)
#
#         data = {
#             'user_id': user_id,
#             'access_token': access_token
#         }
#
#         return Response(data)
#
#
# class CheakPassword(APIView):
#     def post(self, request, user_id):
#
#         password = request.data.get('password')
#         password2 = request.data.get('password2')
#         access_token = request.data.get('access_token')
#
#         if not access_token:
#             return Response('请求超时')
#         if password != password2:
#             return Response('前后密码不一致操你妈的')
#
#         user = User.objects.get(id=user_id)
#         user.set_password(password)
#         user.save()
#         return Response(status=status.HTTP_201_CREATED)
