from django.contrib.auth.backends import RemoteUserBackend


class CaseInsensitiveRemoteUser(RemoteUserBackend):
    def clean_username(self, username):
        return username.lower()