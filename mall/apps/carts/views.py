import base64
import pickle

from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializer import CartDeleteSerializer
from carts.serializer import CartSerializer, CartSKUSerializer
from goods.models import SKU

'''
购物车业务逻辑分析：
在用户登录与未登录的情况下都可以保存用户的购物车数据
登录情况下保存的购物车数据分别有：
    用户ID， 商品ID， 添加商品的数量，购物车是否勾选
1， 在用户登录的情况下添加的购物车数据是保存在数据库中，
    我们选择将数据保存在redis中，这样数据的提取速度有很大的提升
    1.1 为了充分利用redis存储空间，我们将数据分开保存
        用户ID和商品ID， 商品的数量保存在reids的哈希类型
           组织数据结构--------用户ID：{商品ID：商品数量}
    1.2 将购物车中商品是否勾选记录保存在Set类型，
        里面保存的是已经勾选的商品的ID
           组织数据结构--------用户ID：{商品ID， 商品ID}
2， 在用户未登录的情况下添加的购物车数据是保存在cookie中
    cookie中我们保存的数据是：商品ID， 商品个数， 勾选状态
    组织数据结构：商品ID：{商品数量：xxx， 是否勾选：True}勾选状态默认为True
'''
'''
在用户添加购物车的时候，因为我们采用JWT认证方式，所以会先进行JWT认证，
会验证token，在token不存在或者被篡改或过期的情况下是不能加入到购物车的
我们的业务逻辑是先让用户添加到购物车
我们重写perform_authentication（）方法，这样就可以不先进行token认证，
直接进入添加购物车的方法中来，在我们需要验证的时候再去验证
在我们重写了方法之后会不去进行token验证，直接进入到添加购物车的方法中，
购物车方法中获取用户信息的代码会报错，因为取不到用户信息，
所以我们对提取用户信息的代码进行捕获异常,如果捕获到异常就说明没有用户信息
我们就将用户设置为None

'''

'''
在用户为登录的情况下会将购物车数据(字典)保存在cookie中，
在保存之前为了数据的安全性我们要对数据进行处理
1, 使用pickle模块可以将字典转换成bytes类型
    pickle.dumps() 将python数据序列化为bytes类型
    pickle.loads() 将bytes类型数据反序列化为python的数据类型
2, base64 模块可以将二进制数据进行加密处理
    base64.b64encode() 将bytes类型数据进行base64编码，返回编码后的bytes类型
    base64.b64deocde() 将base64编码的bytes类型进行解码，返回解码后的bytes类型

'''
'''
cookie数据处理步骤：
加入购物车时的处理：
1, 使用one = pickle.dumps(dict)将字典类型数据转换为二进制数据
2, 使用two = base64.b64encode(one)将二进制数据进行加密处理
   将数据转换为字符串 value = two.decode()
提取到cookie中数据时的处理：
3, 使用three = base64.b64decode(three)将数据进行解密
4, 使用fore = pickle.loads(three)将二进制数据转换为字典
'''


class CartsApiView(APIView):
    def perform_authentication(self, request):
        pass

    '''
    添加购物车逻辑：

        当用户点击加入购物车按钮的时候，前端会将数据
        （商品id， 商品个数，勾选状态默认为True，用户id）
        1, 后端接受数据
        2, 校验数据
        3, 获取校验之后的数据
        4, 获取用户信息
        5, 根据用户信息进行判断用户是否登录
        6, 登录用户保存在redis中
            6.1 连接raids
            6.2 将数据保存在redis中的hash和set中
            6.3 返回响应
        7, 未登录用户保存在cookie中
            7.1 先获取cookie中的数据
            7.2 判断是否存在cookie数据
            7.3 如果添加购物车的商品id存在，则进行商品数量的累加
            7.4 如果添加购物车的商品id不存在，则直接添加商品信息
            7.5 返回
    '''

    def post(self, request):
        # 1, 后端接受数据
        data = request.data
        # 2, 校验数据
        serializer = CartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3, 获取校验之后的数据
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')
        # 4, 获取用户信息
        try:
            user = request.user
        except Exception as e:
            user = None
        # 5, 根据用户信息进行判断用户是否登录
        # 如果用户信息存在并且认证通过
        if user is not None and user.is_authenticated:
            # 6, 登录用户保存在redis中
            # 6.1 连接raids
            redis_conn = get_redis_connection('cart')
            # 6.2 将数据保存在redis中的hash和set中
            # 保存在hash中的数据 cart_userid:sku_id:count
            redis_conn.hset('cart_%s' % user.id, sku_id, count)
            # 保存在set中的数据  cart_selrcted_userid:sku_id
            redis_conn.sadd('cart_selected_%s' % user.id, sku_id)
            # 6.3 返回响应
            return Response(serializer.data)
        else:
            # 7, 未登录用户保存在cookie中
            #     7.1 先获取cookie中的数据
            cookie_str = request.COOKIES.get('cart')
            #     7.2 判断是否存在cookie数据
            if cookie_str is not None:
                # 说明有数据
                # 对base64的数据进行解码
                decode = base64.b64decode(cookie_str)
                # 对数据进行转换成字典
                cookie_cart = pickle.loads(decode)
            else:
                cookie_cart = {}
                # 说明没有数据,先进行初始化
                # 7.3 如果添加购物车的商品id存在，则进行商品数量的累加
            if sku_id in cookie_cart:
                # 存在，原个数
                origin_count = cookie_cart[sku_id]['count']
                # 商品个数的增加
                count += origin_count
                # 7.4 如果添加购物车的商品id不存在，则直接添加商品信息

            cookie_cart[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 7.5对数据进行加密处理
            # 将数据转换成二进制
            dumps = pickle.dumps(cookie_cart)
            # 将数据加密
            encode = base64.b64encode(dumps)
            # 将数据转换为字符串
            value = encode.decode()
            # 7.6 返回响应
            response = Response(serializer.data)
            response.set_cookie('cart', value)
            return response

    '''
    获取用户购物车数据业务逻辑：
    get请求需要将用户信息传递过来
    1, 接收用户信息
    2, 根据用户信息进行判断
    3, 登录用户从redis中获取数据
        3.1 连接raids
        3.2 hash    cart_userid:{sku_id:count}
            set     cart_selected_userid : sku_id
        3.3 根据商品id获取商品的详细信息
        3.4 返回响应
    4, 未登录用户从cookie中获取数据
        4.1 先从cookie中获取数据
        4.2 判断是否存在购物车数据
        4.3 根据商品id获取商品的详细信息
        4.4 返回响应
    '''

    def get(self, request):
        # 获取用户购物车数据业务逻辑：
        # get请求需要将用户信息传递过来
        # 1, 接收用户信息
        try:
            user = request.user
        except Exception as e:
            user = None
        # 2, 根据用户信息进行判断
        if user is not None and user.is_authenticated:
            '''
            用户信息存在，数据从redis中获取
            '''
            # 3, 登录用户从redis中获取数据
            #     3.1 连接raids
            redis_conn = get_redis_connection('cart')
            #     3.2 hash    cart_userid:{sku_id:count}
            redis_hash = redis_conn.hgetall('cart_%s' % user.id)
            #         set     cart_selected_userid : sku_id
            redis_selected = redis_conn.smembers('cart_selected_%s' % user.id)
            # 组织数据
            # 1, 定义一个空字典
            cart = {}
            # 2, 组织数据格式为：cart = {sku_id:{count:xxx, selected:xxx}}
            for sku_id, count in redis_hash.items():
                cart[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected
                }
        else:
            # 4, 未登录用户从cookie中获取数据
            #     4.1 先从cookie中获取数据
            cart_str = request.COOKIES.get('cart')
            #     4.2 判断是否存在购物车数据
            if cart_str is not None:
                # 此时取出来的数据是字符串，首选我们需要将字符串转换为二进制，
                # 然后对二进制进行base64解码，然后通过pickle.loads方法将数据转换为字典格式
                loads = base64.b64decode(cart_str)
                cart = pickle.loads(loads)
            else:
                cart = {}

        # 5 根据商品id获取商品的详细信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]['count']
            sku.selected = cart[sku.id]['selected']
        # 序列化数据返回响应
        serializer = CartSKUSerializer(skus, many=True)
        # 6 返回响应
        return Response(serializer.data)

    def put(self, request):
        '''
        1, 获取前端传递过来的数据
        2, 创建序列化器，校验数据
        3, 获取校验之后的数据
        4, 获取用户信息，判断用户是否登录
        5, 登录用户，从redis中获取数据
            获取到数据之后对数据进行修改
        6, 未登录用户从cookie中获取数据
            获取到数据之后对数据进行修改
        '''
        # 1, 获取前端传递过来的数据
        data = request.data
        # 2, 创建序列化器，校验数据
        serializer = CartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3, 获取校验之后的数据
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')
        # 4, 获取用户信息，判断用户是否登录
        try:
            user = request.user
        except Exception as e:
            user = None
        if user is not None and user.is_authenticated:
            # 5, 登录用户，从redis中获取数据
            # 5.1 连接redis
            redis_conn = get_redis_connection('cart')
            # 对数据进行修改
            # hash修改
            redis_conn.hset('cart_%s' % user.id, sku_id, count)
            # set修改
            # 如果可选状态为真，则添加到set中
            if selected:
                redis_conn.sadd('cart_selected_%s' % user.id, sku_id)
            # 为假,从set中删除
            else:
                redis_conn.srem('cart_selected_%s' % user.id, sku_id)
            return Response(serializer.data)

        else:
            # 6, 未登录用户从cookie中获取数据
            cart_str = request.COOKIES.get('cart')
            # 判断cookie中是否有数据
            if cart_str is not None:
                # 有数据，对数据进行解码，格式转换
                decode = base64.b64decode(cart_str)
                cart = pickle.loads(decode)
            else:
                # 没有数据，对数据进行初始化
                cart = {}
            # 判断当商品id在cookie中的商品id中就进行修改
            if sku_id in cart:
                cart[sku_id] = {
                    'count': count,
                    'selected': selected
                }
            # 组织数据使用序列化器进行保存
            dumps = pickle.dumps(cart)
            encode = base64.b64encode(dumps)
            response = Response(serializer.data)
            response.set_cookie('cart', encode)
            return response

    def delete(self, request):
        '''
        1, 获取前端提交的商品id
        2, 对数据进行校验
        3， 获取校验之后的数据
        4, 获取用户信息
        5, 登录用户从raids中删除数据
        6, 未登录用户从cookie中删除数据
        '''
        # 1, 获取前端提交的商品id
        data = request.data
        # 2, 对数据进行校验
        serializer = CartDeleteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3， 获取校验之后的数据
        sku_id = serializer.validated_data.get('sku_id')
        # 4, 获取用户信息
        user = request.user
        if user is not None:
            # 5, 登录用户从raids中删除数据
            # 5.1 连接redis
            redis_conn = get_redis_connection('cart')
            # 删除hash数据
            redis_conn.hdel('cart_%s'%user.id, sku_id)
            # 删除set数据
            redis_conn.srem('cart_selected_%s'%user.id, sku_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # 6, 未登录用户从cookie中删除数据
            # 获取cookie数据
            cart_str = request.COOKIES.get('cart')
            # 判断cookie数据是否为空
            if cart_str is not None:
                # 解密， 解码
                decode = base64.b64decode(cart_str)
                cart = pickle.loads(decode)
            else:
                cart = {}
            response = Response(serializer.data)
            if sku_id in cart:
                del cart[sku_id]
                # 组织数据
                dumps = pickle.dumps(cart)
                cookie_str = base64.b64encode(dumps)
                response.set_cookie('cart', cookie_str)
            return response