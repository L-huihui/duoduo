from django.shortcuts import render

# Create your views here.
from django.views.generic import CreateView
from django_redis import get_redis_connection
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

from goods.models import SKU
from goods.serializer import SKUSerializer
from users.models import User, Address
from carts.utils import merge_cookie_to_redis
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
            'user_id':user.id,
            'default_address_id':user.default_address_id,
            'limit': 20,
            'addresses':serializer.data
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
    def get(self,request):
        """获取"""
        #获取用户信息
        user_id = request.user.id
        #连接redis
        redis_conn =  get_redis_connection('history')
        #获取数据
        history_sku_ids = redis_conn.lrange('history_%s'%user_id,0,5)
        skus = []
        for sku_id in history_sku_ids:
            sku = SKU.objects.get(pk=sku_id)
            skus.append(sku)
        #序列化
        serializer = SKUSerializer(skus,many=True)
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
            #merge_cart_cookie_to_redis(request, user, response)
            response = merge_cookie_to_redis(request, user, response)

        return response

