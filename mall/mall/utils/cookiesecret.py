"""
利用pickle和base64把cookie购物车数据编码和解吗
"""
import pickle, base64


class CookieSecret:
    # 编码
    @classmethod
    def dumps(cls, data):
        """
        功能： 把cookie购物车字典数据编码
        :param data: {1:{"count": 5, "selected": True}}
        :return: cookie字符串数据
        """
        # (1).pickle把字典编码成字节数据
        data_bytes = pickle.dumps(data)
        # (2).base64把字节数据编码成字符串的字节数据
        base64_bytes = base64.b64encode(data_bytes)
        # (3).返回base64编码之后的字符串，用于保存在cookie中
        return base64_bytes.decode()

    # 解码
    @classmethod
    def loads(cls, data):
        """
        功能： 把cookie中的字符串数据解码成字典对象
        :param data: 购物车字符串数据
        :return: 购物车字典
        """
        # (1).base64解码成字节
        base64_bytes = base64.b64decode(data)
        # (2). pickle解码成字典
        pickle_data = pickle.loads(base64_bytes)
        return pickle_data


if __name__ == '__main__':
    # 编写测试案例
    cart = {
        1: {
            "count": 5,
            "selected": True
        },
        2: {
            "count": 10,
            "selected": False
        }
    }
    # (1)、编码
    cart_str = CookieSecret.dumps(cart)
    print("cookie购物车数据字符串: ", cart_str)
    # (2)、解码
    cart_dict = CookieSecret.loads(cart_str)
    print("cookie购物车字典数据: ", cart_dict)