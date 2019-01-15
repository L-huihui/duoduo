from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from fdfs_client.client import Fdfs_client

from mall import settings

@deconstructible
class MyStorage(Storage):
    def __init__(self, config_path=None, config_url=None):
        if not config_path:
            fdfs_config =settings.FDFS_CLIENT_CONF
            self.fdfs_config = fdfs_config
        if not config_url:
            fdfs_url = settings.FDFS_URL
            self.fdfs_url = fdfs_url

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content, max_length=None):
        # 1, 创建Fdfs的酷虎段，让客户端加载配置文件
        client = Fdfs_client('utils/fastdfs/client.conf')
        # 2, 获取上传的文件content.read就是读取content的内容
        file_data = content.read()
        # 3, 上传图片，并获取返回的内容
        result = client.upload_by_buffer(file_data)
        # 4,　根据返回的内容，获取remote file_id
        if result.get('Status') == 'Upload successed.':
            file_id = result.get('Remote file_id')
        else:
            raise Exception('上传失败')
        return file_id

    # exists做了重名处理，我们只需要上传就可以了
    def exists(self, name):
        return False
    # name是生成的文件地址
    def url(self, name):
        return 'http://192.168.233.233:8888' + name


# docker run -dti --network=host --name storage -e TRACKER_SERVER=192.168.233.233:22122 -v /var/fdfs/storage:/var/fdfs delron/fastdfs storage
