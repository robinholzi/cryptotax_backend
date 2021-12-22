from cryptotax_backend import celery


class myschedule(celery.beat_schedule):

    def __init__(self, *args, **kwargs):
        super(myschedule, self).__init__(*args, **kwargs)
        self.start_date = kwargs.get('start_date', None)

    def is_due(self, last_run_at):
        if self.start_date is not None and self.now() < self.start_date:
            return (False, 20)  # try again in 20 seconds
        return super(myschedule, self).is_due(last_run_at)

    def __reduce__(self):
        return self.__class__, (self.run_every, self.relative, self.nowfun, self.start_date)