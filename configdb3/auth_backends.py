import requests
from django.conf import settings
from django.contrib.auth.models import User


class OAuth2Backend(object):
    """
    Authenticate against the Oauth backend, using
    grant_type: password
    """

    def authenticate(self, username=None, password=None):
        if username == 'eng':
            return None  # anonymous eng account disabled
        response = requests.post(
            settings.OAUTH_TOKEN_URL,
            data={
                'grant_type': 'password',
                'username': username,
                'password': password,
                'client_id': settings.OAUTH_CLIENT_ID,
                'client_secret': settings.OAUTH_CLIENT_SECRET
            }
        )
        if response.status_code == 200:
            user, created = User.objects.get_or_create(
                username=username,
                is_superuser=True,
                is_staff=True
            )
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
