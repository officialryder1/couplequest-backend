import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed

def decode_access_token(token):
    try:
        payload = jwt.decode(token, 'secret', algorithms="HS256")

        user_id = payload.get('user_id')
        if not user_id:
            raise AuthenticationFailed("Invalid token: No user ID found")

         # Retrieve the user from the database
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")

    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Token has expired')
    except jwt.InvalidTokenError:
        raise AuthenticationFailed('Invalid token')