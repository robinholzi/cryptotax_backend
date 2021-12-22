
from django.contrib.auth.models import AbstractUser
from django.db import models

# null or default for optional fields (blank=True --> can be left out)
# null -> database
# blank -> rendered field


class BaseUserMixin(models.Model):
    updated = models.DateTimeField('updated', auto_now=True, blank=True, null=False)
    created = models.DateTimeField('created', auto_now_add=True, blank=True, null=False)

    # inherited: first_name = models.CharField('first_name', max_length=150)
    middle_name = models.CharField('middle_name', max_length=150, blank=True, null=True)
    # inherited: last_name = models.CharField('last_name', max_length=150)

    def __str__(self):
        return f'{self.first_name}' f'{self.middle_name}' f'{self.last_name} BaseUser'

    class Meta:
        abstract = True


class CryptoTaxUser(BaseUserMixin, AbstractUser):
    # inherited: BaseUserMixin.date_created
    # inherited: AbstractUser.date_joined
    # inherited: AbstractUser.last_login

    email = models.EmailField(unique=True, blank=False, null=False)
    # inherited: AbstractUser.username
    # inherited: AbstractUser.user
    # inherited: AbstractUser.password

    # inherited: AbstractUser.first_name
    # inherited: BaseUserMixin.middle_name
    # inherited: AbstractUser.last_name
    # inherited: BaseUserMixin.gender

    # middle_name = models.CharField('profile_img_link', max_length=1024, blank=True, null=True) TODO

    pass

    def __str__(self):
        return f'CryptoTaxUser: [{self.username}]'

    # def save(self, *args, **kwargs):
    #     super().save(args, kwargs)
