from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings

class SecretOauth():
    def __init__(self):
        # 初始化一个TimedJSONWebSignatureSerializer对象，用于加密和解密
        self.serializer = Serializer(
            secret_key = settings.SECRET_KEY,
            expires_in = 24* 15 * 60 #秒
        )

    # 加密
    def dumps(self, content_dict):
        """
        加密数据
        :param 字典数据
        :return 加密后的数据
        """
        # 1. 通过 dumps方法 加密数据
        result = self.serializer.dumps(content_dict)
        # 2. result是bytes类型转换成 str
        return result.decode()

    # 解密
    def loads(self, content_secret):
        """
        解密数据
        :param 加密之后的字符串秘文
        :return 解密后的字典
        """
        try:
            result = self.serializer.loads(content_secret)
        except Exception as e:
            return None
        return result

