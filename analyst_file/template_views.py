from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie

from analyst_file.models import AnalystFile

@login_required
@ensure_csrf_cookie
def file_upload_view(request):
    error = None
    success = None

    if request.method == 'POST':
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']

            # Check file size (limit to 10MB)
            if uploaded_file.size > 10 * 1024 * 1024:
                error = "File size exceeds the 10MB limit."
            else:
                # Create a new AnalystFile
                new_file = AnalystFile.objects.create(
                    filename=uploaded_file.name,
                    file_type=uploaded_file.content_type,
                    upload=uploaded_file,
                    analyst=request.user
                )

                success = f"File '{uploaded_file.name}' uploaded successfully."

                # If it's an XML file, offer to process it
                if new_file.is_xml:
                    return redirect(f'/vulnerabilities/import?file_id={new_file.id}')
        else:
            error = "No file was uploaded."

    # Get all files uploaded by the current user
    files = AnalystFile.objects.filter(analyst=request.user).order_by('-created_at')

    context = {
        'files': files,
        'error': error,
        'success': success,
    }

    return render(request, 'analyst_file/file_upload.html', context)
