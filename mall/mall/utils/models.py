from django.db import models

# 只是一个被用于继承的集类，不会被用于迁移建表
class BaseModel(models.Model):
    """为模型类补充字段"""

    # 创建时间:
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    # 更新时间:
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        # 说明是抽象模型类(抽象模型类不会创建表)
        abstract = True
