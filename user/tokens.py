from datetime import (
    datetime,
    time,
)
from typing import Any

from django.conf import settings
from django.utils.crypto import (
    constant_time_compare,
    salted_hmac,
)
from django.utils.http import (
    base36_to_int,
    int_to_base36,
)

from user.models import CryptoTaxUser


class EmailVerificationTokenGenerator:
    """
    Strategy object used to generate and check tokens for the password
    reset mechanism.
    """

    key_salt = "cryptotax_backend.user.tokens.EmailVerificationTokenGenerator"
    algorithm: Any = None
    secret = settings.SECRET_KEY

    def __init__(self) -> None:
        # RemovedInDjango40Warning: when the deprecation ends, replace with:
        # self.algorithm = self.algorithm or 'sha256'
        self.algorithm = self.algorithm or settings.DEFAULT_HASHING_ALGORITHM

    def make_token(self, user: CryptoTaxUser) -> str:
        """Return a token that can be used once to verify a user's email address."""
        return self._make_token_with_timestamp(user, self._num_seconds(self._now()))

    def check_token(self, user: CryptoTaxUser, token: str) -> bool:
        """Check that a email verification reset token is correct for a given user."""
        if not (user and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
            # RemovedInDjango40Warning.
            legacy_token = len(ts_b36) < 4
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
            # RemovedInDjango40Warning: when the deprecation ends, replace
            # with:
            #   return False
            if not constant_time_compare(
                self._make_token_with_timestamp(user, ts, legacy=True),
                token,
            ):
                return False

        # RemovedInDjango40Warning: convert days to seconds and round to
        # midnight (server time) for pre-Django 3.1 tokens.
        now = self._now()
        if legacy_token:
            ts *= 24 * 60 * 60
            ts += int((now - datetime.combine(now.date(), time.min)).total_seconds())
        # Check the timestamp is within limit.
        if (self._num_seconds(now) - ts) > settings.PASSWORD_RESET_TIMEOUT:
            return False

        return True

    def _make_token_with_timestamp(
        self, user: CryptoTaxUser, timestamp: int, legacy: bool = False
    ) -> str:
        # timestamp is number of seconds since 2001-1-1. Converted to base 36,
        # this gives us a 6 digit string until about 2069.
        ts_b36 = int_to_base36(timestamp)
        hash_string = salted_hmac(
            self.key_salt,
            self._make_hash_value(user, timestamp),
            secret=self.secret,
            # RemovedInDjango40Warning: when the deprecation ends, remove the
            # legacy argument and replace with:
            #   algorithm=self.algorithm,
            algorithm="sha1" if legacy else self.algorithm,
        ).hexdigest()[
            ::2
        ]  # Limit to 20 characters to shorten the URL.
        return "%s-%s" % (ts_b36, hash_string)

    def _make_hash_value(self, user: CryptoTaxUser, timestamp: int) -> str:
        """
        Hash the user's primary key and some user state that's sure to change
        after a password reset to produce a token that invalidated when it's
        used:
        1. The password field will change upon a password reset (even if the
           same password is chosen, due to password salting).
        2. The last_login field will usually be updated very shortly after
           a password reset.
        Failing those things, settings.PASSWORD_RESET_TIMEOUT eventually
        invalidates the token.

        Running this data through salted_hmac() prevents password cracking
        attempts using the reset token, provided the secret isn't compromised.
        """
        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        login_timestamp = (
            ""
            if user.last_login is None
            else user.last_login.replace(microsecond=0, tzinfo=None)
        )
        return (
            str(user.pk)
            + user.password
            + str(login_timestamp)
            + str(timestamp)
            + str(user.is_active)
        )

    def _num_seconds(self, dt: datetime) -> int:
        return int((dt - datetime(2001, 1, 1)).total_seconds())

    def _now(self) -> datetime:
        # Used for mocking in tests
        return datetime.now()


email_verification_token_generator = EmailVerificationTokenGenerator()
