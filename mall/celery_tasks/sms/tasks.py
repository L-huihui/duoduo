'''
1, 新建任务
2, 创建celery实例
3, 在celery中设置任务,broken
4, worker

'''
# 1, 这个普通的函数,必须要被celery实例对象的task装饰
# 2, 这个任务需要cele自己去检测
from celery_tasks.main import app
from libs.yuntongxun.sms import CCP


@app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    CCP().send_template_sms(mobile, [sms_code, 5], 1)


