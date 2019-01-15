from django.shortcuts import render

# Create your views here.
from django.views.generic import View
from goods.models import GoodsCategory, GoodsChannel
from contents.models import ContentCategory
from collections import OrderedDict


# Create your views here.
class CategoryView(View):
    """
    获取首页分类数据

    GET /goods/categories/
    """

    def get(self, request):
        pass
