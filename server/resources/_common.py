from resources.schemas._common import ErrorResponse

JWT_SECURITY = [{"jwtCookie": []}]

STANDARD_ERROR_RESPONSES = {
    400: {"description": "Bad request", "schema": ErrorResponse},
    404: {"description": "Not found", "schema": ErrorResponse},
}

AUTH_ERROR_RESPONSES = {
    400: {"description": "Bad request", "schema": ErrorResponse},
    401: {"description": "Unauthorized", "schema": ErrorResponse},
    403: {"description": "Forbidden", "schema": ErrorResponse},
    404: {"description": "Not found", "schema": ErrorResponse},
}

NOT_FOUND_RESPONSE = {
    404: {"description": "Not found", "schema": ErrorResponse},
}
