from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            # Try username first, fall back to email
            try:
                user = UserModel.objects.get(username__iexact=username)
            except UserModel.DoesNotExist:
                user = UserModel.objects.get(email__iexact=username)
        except (UserModel.DoesNotExist, UserModel.MultipleObjectsReturned):
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
