import time
import os
from goods.models import GoodsChannel
from .models import ContentCategory
from collections import OrderedDict
from django.template import loader
from django.conf import settings
'''
页面静态化－－－－提升用户体验
其实就是我们先把数据查询出来，　将查询出来的数据填充到模板中
形成了html，将html写入到指定的文件
当用户访问的时候，直接访问静态文件
'''


def generate_static_index_html():
    """
    生成静态的主页html
    """

    print('%s:generate_static_index' % time.ctime())
    # 商品频道及分类菜单
    # 使用有序字典保存类别的顺序
    # categories = {
    #     1: { # 组1
    #         'channels': [{'id':, 'name':, 'url':},{}, {}...],
    #         'sub_cats': [{'id':, 'name':, 'sub_cats':[{},{}]}, {}, {}, ..]
    #     },
    #     2: { # 组2
    #
    #     }
    # }
    # 初始化存储容器
    categories = OrderedDict()
    # 获取一级分类
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')

    # 对一级分类进行遍历
    for channel in channels:
        # 获取group_id
        group_id = channel.group_id
        # 判断group_id 是否在存储容器,如果不在就初始化
        if group_id not in categories:
            categories[group_id] = {
                'channels': [],
                'sub_cats': []
            }

        one = channel.category
        # 为channels填充数据
        categories[group_id]['channels'].append({
            'id': one.id,
            'name': one.name,
            'url': channel.url
        })
        # 为sub_cats填充数据
        for two in one.goodscategory_set.all():
            # 初始化 容器
            two.sub_cats = []
            # 遍历获取
            for three in two.goodscategory_set.all():
                two.sub_cats.append(three)

            # 组织数据
            categories[group_id]['sub_cats'].append(two)

    # 广告和首页数据
    contents = {}
    content_categories = ContentCategory.objects.all()
    # content_categories = [{'name':xx , 'key': 'index_new'}, {}, {}]
    # {
    #    'index_new': [] ,
    #    'index_lbt': []
    # }
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

    context = {
        'categories': categories,
        'contents': contents
    }

    # 数据分为广告数据和分类数据
    # 将数据填充到模板
    # loader.get_template会到系统的模板文件夹中加载指定的文件
    template = loader.get_template('index.html')
    # 渲染数据,渲染之后会生成html数据
    html_data = template.render(context)
    # 指定写入路径
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html')
    # 写入数据
    with open(file_path, 'w') as f:
        f.write(html_data)
