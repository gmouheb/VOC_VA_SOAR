from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AnalystFileSerializer
from .models import AnalystFile
import os
from django.conf import settings
from django.utils.crypto import get_random_string


def store_file(file):
    """
    Store an uploaded file with its original name in the uploaded_reports directory

    Args:
        file: The uploaded file object

    Returns:
        String: Path to the saved file relative to MEDIA_ROOT
    """
    try:
        # Ensure upload directory exists
        upload_dir = os.path.join(settings.MEDIA_ROOT, "uploaded_reports")
        os.makedirs(upload_dir, exist_ok=True)

        # Keep the original filename but handle duplicates
        original_filename = file.name
        # Clean the filename to ensure it's safe for filesystem
        safe_filename = ''.join(c for c in original_filename if c.isalnum() or c in '._- ')

        # Check if file already exists, add a suffix if needed
        base_name, ext = os.path.splitext(safe_filename)
        counter = 0
        final_filename = safe_filename
        full_path = os.path.join(upload_dir, final_filename)

        while os.path.exists(full_path):
            counter += 1
            final_filename = f"{base_name}_{counter}{ext}"
            full_path = os.path.join(upload_dir, final_filename)

        # Save the file
        print(f"Saving file to: {full_path}")
        with open(full_path, "wb+") as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        # Return relative path
        return os.path.join("uploaded_reports", final_filename)

    except Exception as e:
        print(f"Error saving file: {str(e)}")
        # Re-raise the exception to be handled by the caller
        raise




class AnalystFileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Return list of user's files
        user_files = AnalystFile.objects.filter(analyst=request.user)
        serializer = AnalystFileSerializer(user_files, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Debug information
        print("FILES in request:", request.FILES)
        print("Content-Type:", request.META.get('CONTENT_TYPE', 'Unknown'))
        print("Content-Length:", request.META.get('CONTENT_LENGTH', 'Unknown'))
        print("Request method:", request.method)

        if 'upload' not in request.FILES:
            print("Available keys in request.FILES:", request.FILES.keys())
            print("Available keys in request.data:", request.data.keys() if hasattr(request, 'data') else 'No data attribute')
            return Response({"error": "No file uploaded. Please ensure the file is sent with key 'upload'."}, 
                           status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['upload']
        print(f"File received: {file.name}, size: {file.size}, content_type: {file.content_type}")

        # Store file with original filename
        saved_path = store_file(file)
        print(f"File saved to: {saved_path}")

        # Get the absolute path for verification
        abs_path = os.path.join(settings.MEDIA_ROOT, saved_path)
        print(f"Absolute file path: {abs_path}")
        print(f"File exists at path: {os.path.exists(abs_path)}")

        # Create file record with authenticated user
        analyst_file = AnalystFile.objects.create(
            filename=file.name,
            file_type=file.content_type,
            upload=saved_path,
            analyst=request.user,  # Associate with the currently logged-in user
            scanner_source="manual"
        )

        serializer = AnalystFileSerializer(analyst_file)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
