from django.conf import settings


def app_settings(request):
    return {
        "EML_MAX_FILES": settings.EML_MAX_FILES_PER_REQUEST,
        "EML_MAX_FILE_MB": settings.EML_MAX_FILE_BYTES // (1024 * 1024),
    }
