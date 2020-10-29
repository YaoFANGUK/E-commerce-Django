from django.db import models
from django.contrib.auth.models import AbstractUser
from mall.utils.models import BaseModel

class User(AbstractUser):

    # 额外增加mobile字段
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    # 新增email_active字段
    email_active = models.BooleanField(default=False,verbose_name="邮箱验证状态")
    # 新增默认收货地址
    default_address = models.ForeignKey(
        'Address', related_name='users', null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name='默认地址'
    )

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class Address(BaseModel):
    """
    用户地址（收货地址）
    """
    # on_delete=models.CASCADE --> 主表数据(User)存在关联的从表数据(Address),主表数据删除，从表数据级联删除
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    # on_delete=models.PROTECT --> 主表数据存在关联从表数据，则主表数据不允许删除
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses', verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses', verbose_name='区')

    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        # 设置默认 已更新时间降序 获取查询集数据
        ordering = ['-update_time']
