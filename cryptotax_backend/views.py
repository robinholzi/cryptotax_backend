from rest_framework.decorators import api_view

from cryptotax_backend.utils import success


@api_view(['GET'])
def test(request, *args, **kwargs):
    return success(200, 0, "test successful!")
