from _decimal import Decimal

from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import SKU
from orders.models import OrderInfo
from orders.serializer import OrderSettlementSerializer, OrderCommitSerializer, UserCenterOrderSerializer


class OrderSettlementView(APIView):
    '''
    订单结算
    '''
    # 添加认证
    permission_classes = [IsAuthenticated]

    # 获取结算订单
    def get(self, request):
        '''获取'''
        '''
        1, 获取用户信息
        2, 从redis中获取用户勾选的要结算的商品id的列表
        3, 遍历列表将数据字符串数据转换为整数类型
        4, 查询列表中的商品信息
        5, 返回响应

        '''
        # 1, 获取用户信息
        user = request.user
        # 2, 从redis中获取用户勾选的要结算的商品id的列表
        # 2.1 连接redis
        redis_conn = get_redis_connection('cart')
        # 2.2 根据user.id获取hash当前用户购物车中的商品列表
        redis_cart = redis_conn.hgetall('cart_%s'%user.id)
        # 2.3 根据user.id获取set中当前用户的购物车中勾选的商品
        redis_selected = redis_conn.smembers('cart_selected_%s'%user.id)
        # 3, 遍历列表将数据字符串数据转换为整数类型
        cart = {}
        for sku_id in redis_cart:
            cart[int(sku_id)] = int(redis_cart[sku_id])
        # 4, 查询列表中的商品信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]
        # 运费
        freight = Decimal('10.00')
        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})
        # 5, 返回响应
        return Response(serializer.data)


class OrderView(CreateAPIView):
    '''
    保存订单
    '''
    permission_classes = [IsAuthenticated]

    serializer_class = OrderCommitSerializer


class UserCenterOrdersView(ListAPIView):

    permission_classes = [IsAuthenticated]
    queryset = OrderInfo.objects.all()
    serializer_class = UserCenterOrderSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ('create_time', 'total_amount',)

