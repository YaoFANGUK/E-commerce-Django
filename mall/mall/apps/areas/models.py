from django.db import models


class Area(models.Model):
    """
    行政区划
    """
    # 创建name字段，用户保存名称
    name = models.CharField(max_length=20, verbose_name="名称")
    # 自关联字段 parent
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs', null=True, blank=True, verbose_name='上级行政区划')

    class Meta:
        db_table = 'tb_areas'

    def __str__(self):
        return self.name
