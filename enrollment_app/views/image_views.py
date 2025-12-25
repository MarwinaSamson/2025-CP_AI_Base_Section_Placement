from django.http import FileResponse, Http404
from django.conf import settings
import os


def serve_temp_image(request, filename):
    """
    Serve temporary uploaded images from temp_uploads directory
    """
    file_path = os.path.join(settings.BASE_DIR, 'temp_uploads', filename)
    
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    else:
        raise Http404("Image not found")