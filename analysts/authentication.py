# analysts/authentication.py

import jwt
import logging
from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from analysts.models import Analyst, APIKey  # Import your custom models

logger = logging.getLogger(__name__)

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Try to get token from Authorization header
        auth_header = request.headers.get('Authorization')
        token = None

        if auth_header:
            try:
                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == 'bearer':
                    token = parts[1]
                else:
                    raise AuthenticationFailed('Invalid Authorization header format')
            except Exception as e:
                logger.error(f"Error parsing Authorization header: {e}")
                raise AuthenticationFailed('Invalid Authorization header format')

        # If token not in header, try cookie
        if not token:
            token = request.COOKIES.get('jwt')
            if not token:
                return None  # No token found anywhere

        try:
            # Print the first few characters of the token for debugging
            logger.debug(f"Attempting to validate token: {token[:10]}...")

            # Always use SECRET_KEY for consistency
            secret_key = settings.SECRET_KEY
            secret_key = settings.SECRET_KEY

            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            logger.debug(f"Token validated successfully for user ID: {payload.get('id')}")

        except jwt.ExpiredSignatureError:
            logger.error("Token validation failed: Token expired")
            raise AuthenticationFailed('Token expired')
        except jwt.DecodeError:
            logger.error("Token validation failed: Invalid token")
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise AuthenticationFailed(f'Token validation error: {str(e)}')

        try:
            analyst = Analyst.objects.get(id=payload['id'])
            return (analyst, None)
        except Analyst.DoesNotExist:
            logger.error(f"Analyst with ID {payload.get('id')} not found")
            raise AuthenticationFailed('Analyst not found')


class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')

        # If no API key in header, check query parameters
        if not api_key:
            api_key = request.query_params.get('api_key')

        if not api_key:
            return None  # No API key found

        try:
            # Find the API key in the database
            api_key_obj = APIKey.objects.get(key=api_key)

            # Update last used timestamp
            api_key_obj.last_used = timezone.now()
            api_key_obj.save(update_fields=['last_used'])

            logger.debug(f"API key authentication successful for analyst: {api_key_obj.analyst.email}")

            # Return the authenticated user
            return (api_key_obj.analyst, None)

        except APIKey.DoesNotExist:
            logger.error(f"Invalid API key: {api_key[:8]}...")
            raise AuthenticationFailed('Invalid API key')
