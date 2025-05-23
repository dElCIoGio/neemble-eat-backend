import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR


class ResponseFormatterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            status_code = response.status_code

            # Decode JSON response
            if isinstance(response, JSONResponse):
                original_content = json.loads(response.body.decode("utf-8"))

                # Check if response already has the expected fields
                is_already_structured = any(
                    key in original_content for key in ["data", "message", "error", "meta"]
                )

                formatted_response = {
                    "status": status_code,
                    "success": 200 <= status_code < 300,
                    "message": original_content.get("message", "Request successful"),
                    "data": original_content.get("data") if is_already_structured else original_content,
                    "error": original_content.get("error") if "error" in original_content else (
                        None if 200 <= status_code < 300 else {
                            "code": status_code,
                            "message": "An error occurred"
                        }
                    ),
                    "meta": original_content.get("meta", None),
                }

                return JSONResponse(content=formatted_response, status_code=status_code)

            # If response is not JSON (e.g., files), return as is
            return response

        except Exception as e:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": HTTP_500_INTERNAL_SERVER_ERROR,
                    "success": False,
                    "message": "An internal server error occurred",
                    "data": None,
                    "error": {
                        "code": HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": str(e)
                    },
                    "meta": None
                }
            )
