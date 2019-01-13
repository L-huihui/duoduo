from django.db import models

# Create your models here.
from django.db import models


class Area(models.Model):
    """
    行政区划
    """
    name = models.CharField(max_length=20, verbose_name='名称')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs',
                               null=True, blank=True,
                               verbose_name='上级行政区划')


    '''
    １，在省份数据库中只有id和name字段，没有parent字段
    ２，在市数据库中的parent字段的值为所属省份的id
    ３，区县数据库中的parent字段的值为所属市的id

    '''
    class Meta:
        db_table = 'tb_areas'
        verbose_name = '行政区划'
        verbose_name_plural = '行政区划'

    def __str__(self):
        return self.name
