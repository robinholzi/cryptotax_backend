from __future__ import absolute_import, unicode_literals

from celery import shared_task

from tax_analysis.analysis_worker.processor_worker import processable_worker


# @shared_task(name="periodic_processable_worker")
# def periodic_processable_worker():
#     print("periodic_processable_worker")
#     processable_worker()
