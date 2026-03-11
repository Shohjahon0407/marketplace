import json
import uuid
import traceback
from datetime import datetime


class ErrorLoggingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        try:
            response = self.get_response(request)
            return response

        except Exception as e:

            error_data = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "method": request.method,
                "path": request.path,
                "user_id": str(request.user.id) if request.user.is_authenticated else None,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

            with open("logs/unhandled_errors.json", "a") as f:
                json.dump(error_data, f)
                f.write(",\n")

            raise e