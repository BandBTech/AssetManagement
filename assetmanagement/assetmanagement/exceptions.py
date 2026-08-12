from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        messages = []
        if isinstance(response.data, dict):
            for field, err in response.data.items():
                prefix = f"{field}: " if field not in ("detail", "non_field_errors", "error") else ""
                if isinstance(err, list):
                    for item in err:
                        if isinstance(item, dict) and "message" in item:
                            messages.append(f"{prefix}{item['message']}")
                        else:
                            messages.append(f"{prefix}{item}")
                elif isinstance(err, dict) and "message" in err:
                    messages.append(f"{prefix}{err['message']}")
                else:
                    messages.append(f"{prefix}{err}")
        elif isinstance(response.data, list):
            messages = [str(item) for item in response.data]
        else:
            messages = [str(response.data)]

        response.data = {
            "message": "; ".join(messages),
            "success": False,
        }

    return response
