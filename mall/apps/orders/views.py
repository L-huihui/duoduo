from _decimal import Decimal

from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import mixins
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from orders.serializer import OrderSettlementSerializer, OrderCommitSerializer, UserCenterOrderSerializer, UserCenterGoodsSerializer, \
    CommentOrderSerializer, CommentDetailSerializer


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



class CommentListView(ListAPIView):
    '''
        评论详情数据
            GET /orders/(?P<order_id>\d+)/uncommentgoods/
    '''
    pagination_class = None
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        return OrderGoods.objects.filter(order_id=order_id, is_commented= False)
    serializer_class = UserCenterGoodsSerializer


class CommentView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):

        # 1.接受数据
        data = request.data
        # 2.校验数据
        serializer = CommentOrderSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        order = serializer.validated_data.get('order')

        sku = serializer.validated_data.get('sku')
        comment = serializer.validated_data.get('comment')
        score = serializer.validated_data.get('score')
        is_anonymous = serializer.validated_data.get('is_anonymous')

        # 3. 数据入库
        try:
            comment_goods = OrderGoods.objects.get(order=order, sku=sku)
        except OrderGoods.DoesNotExist:
            return Response({'message': '产品信息错误'}, status=status.HTTP_400_BAD_REQUEST)

        comment_goods.comment = comment
        comment_goods.score = score
        comment_goods.is_anonymous = is_anonymous
        comment_goods.is_commented = True

        comment_goods.save()

        # 判断订单状态，修改
        try:
            flag = 0
            comments_goods = OrderGoods.objects.filter(order_id=order_id)
            for comment_good in comments_goods:
                if comment_good.is_commented == False:
                    flag = 1
            if flag == 0:
                try:
                    comment_infos = OrderInfo.objects.get(order_id=order_id)
                except OrderInfo.DoesNotExist:
                    return Response({'message': '产品信息错误'}, status=status.HTTP_400_BAD_REQUEST)
                comment_infos.status = 5
                comment_infos.save()
        except OrderGoods.DoesNotExist:
            return Response({'message': '产品信息错误'}, status=status.HTTP_400_BAD_REQUEST)

        # 4. 返回响应
        return Response({
            'comment': comment,
            'score': score,
            'is_anonymous': is_anonymous,
        })


class CommentDetailView(ListAPIView):
    '''
        评论详情数据
            GET /orders/(?P<sku_id>\d+)/comments/
    '''
    pagination_class = None

    def get_queryset(self):
        sku_id = self.kwargs.get('sku_id')
        return OrderGoods.objects.filter(sku_id=sku_id, is_commented= True)
    serializer_class = CommentDetailSerializer