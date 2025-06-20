from rest_framework import status, viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from PFE_VOC import settings
from analysts.models import Analyst, APIKey
from analysts.serializers import AnalystSerializer
import jwt, datetime

import os
from dotenv import load_dotenv
load_dotenv()




# Create your views here.




class RegisterAPIView(APIView):
    def post(self, request):
        serializer = AnalystSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
import datetime
import jwt

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = Analyst.objects.filter(email=email).first() #Looking for user with this email

        if user is None:  #If we don't find a user
            raise AuthenticationFailed('Email or password is incorrect')

        if not user.check_password(password):
            raise AuthenticationFailed('Email or password is incorrect')

        # Create payload
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow(),
        }

        # Get secret key from settings
        secret_key = settings.SECRET_KEY

        # Encode the token
        token = jwt.encode(payload, secret_key, algorithm='HS256')

        # If token is bytes (PyJWT < 2.0), convert to string
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        print(f"Token generated: {token[:10]}...")

        response = Response()
        response.data = {
            'jwt': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }

        # Set cookie for browsers
        response.set_cookie(key='jwt', value=token, httponly=True)

        return response





class AnalystView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get the logged-in user's profile data
        This endpoint uses the JWTAuthentication class to authenticate the user
        """
        # The user is already authenticated by the JWTAuthentication class
        # and is available in request.user
        user = request.user

        if not user.is_authenticated:
            raise AuthenticationFailed('Unauthenticated!')

        serializer = AnalystSerializer(user)
        return Response(serializer.data)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response()
        # Clear the JWT cookie
        response.delete_cookie(key='jwt')

        # Delete files uploaded by the user
        from analyst_file.models import AnalystFile
        user_files = AnalystFile.objects.filter(analyst=request.user)

        # Delete physical files and database records
        for file in user_files:
            # Delete the physical file if it exists
            if file.upload and hasattr(file.upload, 'path') and os.path.exists(file.upload.path):
                try:
                    os.remove(file.upload.path)
                except (OSError, PermissionError) as e:
                    print(f"Error deleting file {file.upload.path}: {e}")

        # Delete all file records for this user
        user_files.delete()

        # Delete all files in media/analyst_file directory
        analyst_file_dir = os.path.join('media', 'analyst_file')
        if os.path.exists(analyst_file_dir) and os.path.isdir(analyst_file_dir):
            for filename in os.listdir(analyst_file_dir):
                file_path = os.path.join(analyst_file_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

        # For Bearer token authentication, we'll set the token's expiration time to now
        # This effectively invalidates the token
        try:
            # Get the token from the request
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

                # Decode the token to get the payload
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

                # Set the expiration time to now
                payload['exp'] = datetime.datetime.utcnow()

                # Re-encode the token with the updated expiration time
                new_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

                # If token is bytes (PyJWT < 2.0), convert to string
                if isinstance(new_token, bytes):
                    new_token = new_token.decode('utf-8')

                # Set the new token in the response
                response.data = {
                    "message": "You have been logged out successfully.",
                    "token": new_token
                }
                return response
        except Exception as e:
            # If there's an error, just continue with the normal logout process
            pass

        response.data = {
            "message": "You have been logged out successfully."
        }
        return response












# class AnalystDestroyAPIView(DestroyAPIView):
#         queryset = Analyst.objects.all()
#         serializer_class = AnalystSerializer
#         # permission_classes = (IsAuthenticated,)
#         lookup_field = 'pk'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_api_key(request):
    """
    Generate a new API key for the authenticated user.
    """
    # Get the name for the API key from the request
    name = request.data.get('name', f"API Key {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Create a new API key for the user
    api_key = APIKey.objects.create(
        name=name,
        analyst=request.user
    )

    # Return the API key details
    return Response({
        'message': 'API key generated successfully',
        'api_key': {
            'id': api_key.id,
            'name': api_key.name,
            'key': api_key.key,  # Only shown once when created
            'created_at': api_key.created_at
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_api_keys(request):
    """
    List all API keys for the authenticated user.
    """
    api_keys = APIKey.objects.filter(analyst=request.user)

    # Return the API keys without showing the actual key values
    keys_data = [{
        'id': key.id,
        'name': key.name,
        'created_at': key.created_at,
        'last_used': key.last_used
    } for key in api_keys]

    return Response({
        'api_keys': keys_data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_api_key(request, key_id):
    """
    Delete an API key for the authenticated user.
    """
    try:
        api_key = APIKey.objects.get(id=key_id, analyst=request.user)
        api_key.delete()
        return Response({
            'message': 'API key deleted successfully'
        }, status=status.HTTP_200_OK)
    except APIKey.DoesNotExist:
        return Response({
            'error': 'API key not found'
        }, status=status.HTTP_404_NOT_FOUND)
