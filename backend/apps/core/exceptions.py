from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Standard API error response format.
    """

    response = exception_handler(exc, context)

    if response is None:
        return response

    detail = response.data

    if isinstance(detail, dict):
        message = detail.get("detail") or detail.get("error") or "Request failed."
        errors = detail
    else:
        message = "Request failed."
        errors = detail

    response.data = {
        "success": False,
        "message": message,
        "errors": errors,
        "status_code": response.status_code,
    }

    return response