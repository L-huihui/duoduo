from django.db import models


# Create your models here.
# 创建模型类基类

# 定义ＱＱ身份与用户模型类User的关联关系
from utils.models import BaseModel


class OAuthQQUser(BaseModel):
    '''
    ＱＱ登录用户数据
    '''
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=64, unique=True,verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name