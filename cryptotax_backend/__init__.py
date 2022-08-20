from __future__ import (
    absolute_import,
    unicode_literals,
)

from cryptotax_backend.db import initialize_db

initialize_db()

# TODO
# from .celery import app as celery_app
#
# __all__ = ('celery_app',)
