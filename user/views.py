
"""
ERRORS:
- 200:
    0: login successful
- 400:
    field_errors
    non_field_errors
- 401:
    0: email not verified, yet.
"""
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view

from cryptotax_backend.utils import error_response, success
from user.view_helpers.auth_serializer import AuthTokenSerializer


@api_view(['POST'])
# TODO; catcha to avoid brute force blocks
# @ratelimit(key='ip', rate='10/s')
def login_view(request, *args, **kwargs):
    serializer = AuthTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(400, "TODO", "form error", data=serializer.errors)

    user = serializer.validated_data['user']
    if user.is_active:
        token, created = Token.objects.get_or_create(user=user)
        return success(200, 0, "login successful", data={
            'email': user.email,
            'username': user.username,
            'token': token.key,
        })
    else:
        return error_response(401, 0, title="email not verified, yet.", data={
            'email': user.email,
            'username': user.username,
        })

