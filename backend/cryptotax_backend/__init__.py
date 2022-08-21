from __future__ import (
    absolute_import,
    unicode_literals,
)

from cryptotax_backend.db import initialize_db

from .celery import app as celery_app

initialize_db()

__all__ = ("celery_app",)
