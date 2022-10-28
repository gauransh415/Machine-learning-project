import os
import mimetypes
from wsgiref.util import FileWrapper

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import StreamingHttpResponse
from django.http import JsonResponse

from detection.main import (
    bicep_curl_error_detection,
    plank_error_detection,
    squat_error_detection,
)
from detection.utils import get_static_file_url


@api_view(["GET"])
def stream_video(request):
    """
    Query: video_name
    Stream video get from query
    """
    video_name = request.GET.get("video_name")
    if not video_name:
        return JsonResponse(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "message": "File name not given",
            },
        )

    static_url = get_static_file_url(f"media/{video_name}")
    if not static_url:
        return JsonResponse(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "message": "File not found",
            },
        )

    # Streamed video as chunked
    video_size = os.path.getsize(static_url)
    content_type, _ = mimetypes.guess_type(static_url)
    content_type = content_type or "application/octet-stream"

    chunk_size = video_size // 10

    response = StreamingHttpResponse(
        FileWrapper(open(static_url, "rb"), chunk_size), content_type=content_type
    )
    response["Content-Length"] = video_size
    response["Accept-Ranges"] = "bytes"
    return response


@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_video(request):
    # FIXME Video saved still unstable
    try:
        if request.method == "POST":
            video = request.FILES["file"]

            # Convert any video to .mp4
            video_name, _ = video.name.split(".")
            name_to_save = f"{video_name}.mp4"

            # Process and Saved Video
            squat_error_detection(
                video.temporary_file_path(),
                name_to_save=name_to_save,
                rescale_percent=50,
            )

            return JsonResponse(
                status=status.HTTP_200_OK,
                data={"processed": True, "file_name": name_to_save},
            )

    except Exception as e:
        print(f"Error Video Processing: {e}")
        return JsonResponse(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={
                "error": f"Error: {e}",
            },
        )
