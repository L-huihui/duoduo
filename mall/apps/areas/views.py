from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from .models import Area
from .serializer import AreaSerializer, SubAreaSerializer

# Create your views here.


# class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
class AreasViewSet( ReadOnlyModelViewSet):
    """
    行政区划信息
    list : GET/areas/
    retrieve :GET/areas/(?P<pk>\d+)/
    """
    pagination_class = None  # 区划信息不分页

    # 设置缓存　　　缓存时间为一小时，　配置信息为默认配置
    # @cache_response(timeout=3600, cache='default')
    def get_queryset(self):
        """
        提供数据集
        """
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        """
        提供序列化器
        """
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubAreaSerializer