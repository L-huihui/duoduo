from django.db import transaction
from django_redis import get_redis_connection
from rest_framework import serializers
from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from users.models import User


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)


class OrderCommitSerializer(serializers.ModelSerializer):
    '''
    需要返回的数据有：订单id   地址   支付方式
    '''

    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        '''保存订单信息需要调用create方法，
        因为序列化器自带的create方法不嫩满足，所以我们重写create方法'''
        '''
        1.生成订单信息
              1.1 获取user信息
              1.2 获取地址信息
              1.3 获取支付方式
              1.4 判断支付状态
              1.5 订单id(订单id我们采用自己生成的方式)
              1.6 运费,价格和数量 先为 0
              order = OrderInfo.objects.create()

        2.生成订单商品(列表)信息
            2.1 连接redis
            2.2  hash
                 set
            2.3  选中商品的信息  {sku_id:count}
            2.4  [sku_id,sku_id,...]
            2.5  [SKU,SKU,SKU]
            2.6 对列表进行遍历
        '''
        # 1.生成订单信息
        #       1.1 获取user信息
        user = self.context['request'].user
        #       1.2 获取地址信息
        address = validated_data.get('address')
        #       1.3 获取支付方式
        pay_method = validated_data.get('pay_method')
        #       1.4 判断支付状态
        if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH']:
            # 货到付款
            status = OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        else:
            # 支付宝
            status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']
        #       1.5 订单id(订单id我们采用自己生成的方式)
        # 时间（年月日时分秒）+ 6位的用户id信息
        from django.utils import timezone
        order_id = timezone.now().strftime('%Y%m%d%H%M%S')+'%06d'%user.id
        #       1.6 运费,价格和数量 先为 0
        from decimal import Decimal
        freight = Decimal('10.00')
        total_count = 0
        total_amount = Decimal('0')
        #       order = OrderInfo.objects.create()
        # with 语法实现对部分代码实现事务功能
        with transaction.atomic():
            # 设置事务回滚点
            save_point = transaction.savepoint()
            # 组织数据入库
            order = OrderInfo.objects.create(
                order_id = order_id,
                user = user,
                address = address,
                total_count = total_count,
                total_amount = total_amount,
                freight = freight,
                pay_method=pay_method,
                status = status
            )
            # 2.生成订单商品(列表)信息
            #     2.1 连接redis
            redis_conn = get_redis_connection('cart')
            #     2.2  hash
            redis_id_count = redis_conn.hgetall('cart_%s'%user.id)
            #          set
            redis_selected_ids = redis_conn.smembers('cart_selected_%s'%user.id)
            #     2.3  选中商品的信息  {sku_id:count}
            selected_cart = {}
            for sku_id in redis_selected_ids:
                selected_cart[int(sku_id)] = int(redis_id_count[sku_id])
            #     2.4  [sku_id,sku_id,...]
            ids = selected_cart.keys()
            #     2.5  [SKU,SKU,SKU]
            skus = SKU.objects.filter(pk__in=ids)
            #     2.6 对列表进行遍历
            for sku in skus:
                # 购买的数量
                count = selected_cart[sku.id]
                if sku.stock < count:
                    # 出现异常就应该回滚到指定的保存点
                    transaction.savepoint_rollback(save_point)
                    raise serializers.ValidationError('库存不足')
                # 1, 先查询库存
                old_stock = sku.stock
                old_sales = sku.sales
                # 2, 把更新的数据准备好
                new_stock = sku.stock - count
                new_sales = sku.sales + count
                # 3, 更新之前再查询一次是否和之前的数量一致
                rect = SKU.objects.filter(pk=sku.id,
                                          stock=old_stock).update(stock=new_stock,
                                                                  sales = new_sales)
                if rect == 0:
                    print('下单失败')
                    transaction.savepoint_rollback(save_point)
                    raise serializers.ValidationError('下单失败')
                # 累加，计算总数量和总价格
                order.total_count += count
                order.total_amount += (count * sku.price)
                # 组织数据进行入库
                OrderGoods.objects.create(
                    order = order,
                    sku = sku,
                    count = count,
                    price = sku.price
                )
            order.save()
            transaction.savepoint_commit(save_point)
            # 完成清单之后清除购物车数据（清除redis中的数据）
        pl = redis_conn.pipeline()
        pl.hdel('cart_%s' % user.id, *redis_selected_ids)
        pl.srem('cart_selected_%s' % user.id, *redis_selected_ids)
        pl.execute()
        return order


class UserCenterSkuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url')


class  UserCenterGoodsSerializer (serializers.ModelSerializer):
    sku = UserCenterSkuSerializer()

    class Meta:
        model = OrderGoods
        fields=('sku','price','count','comment','score','is_anonymous','is_commented')
        read_only_fields = ('sku','price')


class UserCenterOrderSerializer(serializers.ModelSerializer):
    skus = UserCenterGoodsSerializer(many=True,read_only=True)

    class Meta:

        model = OrderInfo
        fields = ('user','order_id','total_count','total_amount','freight','pay_method','status','skus','create_time')


class CommentOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderGoods
        fields = ('sku', 'comment', 'score', "is_anonymous", "order")
        extra_kwargs = {
            "comment": {
                'required': True,
            }
        }


class CommentDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderGoods
        fields=('sku','price','count','comment','score','is_anonymous','is_commented')
