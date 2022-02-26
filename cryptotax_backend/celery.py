from __future__ import absolute_import, unicode_literals

from celery.utils.log import get_task_logger

import os

from celery import Celery, shared_task

from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptotax_backend.settings')
app = Celery('cryptotax_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')

# app.conf.beat_schedule = {
#     'every-15-seconds3': {
#         'task': "tax_analysis.tasks.periodic_processable_worker",
#         # 'schedule': 1,  # crontab(minute='*/15')
#         'schedule': 15,
#     },
# #     # 'every-1-seconds-test': {
# #     #     'task': 'cryptotax_backend.celery.test',
# #     #     'schedule': myschedule(timedelta(seconds=5), start_date=datetime.date.today()),
# #     # }
# }

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(15.0, test, name='periodic_processable_worker')

    # Calls test('hello') every 5 seconds.
    # sender.add_periodic_task(2.0, some_task(), name='add every 10')

    # Calls test('world') every 5 seconds
    # sender.add_periodic_task(5.0, some_task.s('world'), expires=10)

    # Executes every Monday morning at 7:30 a.m.
    # sender.add_periodic_task(
    #     crontab(hour=7, minute=30, day_of_week=1),
    #     test.s('Happy Mondays!'),
    # )

#
logger = get_task_logger("logger.txt")


@shared_task
def test():
    logger.info(f'test')
    print("def test shared_task")


# @periodic_processable_worker(run_every=(crontab(second='*/1')), name="some_task", ignore_result=True)

@shared_task
def some_task():
    print(f'Request')
    logger.info(f'Request')
    return
    with open("testtesttest.txt", "a") as myfile:
        myfile.write("appended text")
    raise ZeroDivisionError
    # do something

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
