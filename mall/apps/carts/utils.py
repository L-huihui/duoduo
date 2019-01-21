'''
当用户在未登录的情况下将商品添加到来购物车，然后在付款的时候必须要登录用户才可以
当用户登录时要将购物车数据进行合并，也就是说要将cookie中的数据合并到redis中去
1, 获取cookie中的数据
2, 获取redis中的数据
3, 初始化redis的hash数据
4,合并
5, 将最终的数据保存到redis中
6, 合并之后，删除cookie中的数据
'''
import base64
import pickle

from django_redis import get_redis_connection

'''
redis中的数据结构：hash: {用户id:{商品id：商品数量}}
                  set: {用户id：{商品id， 商品id}}
cookie中的数据结构：{商品id：{商品个数：xxx， 是否勾选：xxx}}
'''

'''
1, 获取cookie中的数据
    cookie中的数据结构：{商品id：{商品个数：xxx ,是否勾选:xxx}}
    1.1 判断cookie中是否有数据，
    1.2 如果cookie中有数据则进行第二步的操作（需要对数据进行pickle和base64操作）
    1.3 如果cookie中没有数据，直接返回响应
2, 获取redis中的数据
    redis中的数据结构：Hash ： {用户id：{商品id：商品个数}}
                     Set  ： {用户id：{商品id， 商品id...}}
    2.1 连接redis
    2.2 根据user.id获取redis中的所有数据
3, 初始化redis中的数据
    3.1 组织保存在redis中Hash的数据
        3.1.1 遍历redis中的数据，将对应的数据保存在空字典中
    3.2 组织保存在Set 中的数据：初始化一个空列表
4, 合并
    4.1 遍历cookie中的数据，当cookie和redis中商品重复时选取cookie中的商品数量
    4.2 当cookie中勾选状态为True 时添加到set列表中
5, 将最终数据保存到redis中，
    5.1 Hash数据将组织的数据保存到hash中
    5.2 对set的列表进行解包保存到set中，但是要对该列表进行判断，当大于0的时候才能解包添加
6, 返回响应
'''


def merge_cookie_to_redis(request, user, response):
    # 1, 获取cookie中的数据
    cookie_str = request.COOKIES.get('cart')
    # 判断cookie中是否有数据，如果有数据就将数据合并
    # 如果没数据，就不用合并，直接使用redis中的数据
    if cookie_str is not None:
        # 对cookie中的数据进行解密转格式
        cookie_cart = pickle.loads(base64.b64decode(cookie_str))
        # 2, 获取redis中的数据
        redis_conn = get_redis_connection('cart')
        redis_id_count = redis_conn.hgetall('cart_%s' % user.id)
        # 3, 初始化redis的hash数据
        # 创建一个字典用于保存合并好的数据
        merge_cart = {}
        # 遍历redis中取到的数据
        for sku_id, count in redis_id_count.items():
            merge_cart[int(sku_id)] = int(count)
            # {sku_id:count}{sku_id:count}
        # 初始化选中状态
        selected_ids = []
        # 4,合并
        # 遍历cookie中的数据
        for sku_id, count_selected_dict in cookie_cart.items():
            # 判断选中状态
            # 选用cookie中的商品数量
            merge_cart[sku_id] = count_selected_dict['count']
            # 将cookie中的勾选中的商品添加到初始化状态的列表中
            if count_selected_dict['selected']:
                selected_ids.append(sku_id)
        # 5, 将最终的数据保存到redis中
        redis_conn.hmset('cart_%s' % user.id, merge_cart)
        # 当勾选的商品id不为0的时候，对列表解包添加
        if len(selected_ids) > 0:
            redis_conn.sadd('cart_selected_%s' % user.id, *selected_ids)
        # 6, 合并之后，删除cookie中的数据
        return response

    return response
