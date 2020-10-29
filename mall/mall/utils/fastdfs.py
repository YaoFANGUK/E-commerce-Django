from django.core.files.storage import Storage
from django.conf import settings

class FastDFSStorage(Storage):
    """
    自定义文件存储系统， 修改存储的方案
    """
    def __init__(self, fdfs_base_url=None):
        """
        :param fdfs_base_url: Storage的IP
        """
        self.fdfs_base_url = fdfs_base_url or settings.FDFS_BASE_URL

    def _save(self, name, content):
        # TODO: 保存文件
        pass

    def _open(self, name, mode='rb'):
        # TODO: 打开文件
        pass

    def url(self, name):
        """
        返回name所知文件的绝对url
        """
        return self.fdfs_base_url + name
