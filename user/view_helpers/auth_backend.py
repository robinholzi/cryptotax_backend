from django.contrib.auth import get_user_model

from user.models import CryptoTaxUser


class EmailOrUsernameModelBackend(object):
    """
    This is a ModelBacked that allows authentication with either a username or an email address.
    """
    def authenticate(email_username=None, password=None):
        if '@' in email_username:
            kwargs = {'email': email_username}
        else:
            kwargs = {'username': email_username}
        try:
            user = get_user_model().objects.get(**kwargs)
            if user.check_password(password):
                return user
        except CryptoTaxUser.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            CryptoTaxUser().set_password(password)
            return None
