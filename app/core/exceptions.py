from fastapi import HTTPException, status
from typing import Any, Dict, Optional

class AppException(HTTPException):
    """Base exception for application specific errors"""
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class NotFoundException(AppException):
    """Exception raised when a resource is not found"""
    def __init__(
        self,
        detail: Any = "Resource not found",
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers,
        )

class UnauthorizedException(AppException):
    """Exception raised when unauthorized access is attempted"""
    def __init__(
        self,
        detail: Any = "Not authenticated",
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"},
        )

class ForbiddenException(AppException):
    """Exception raised when access is forbidden"""
    def __init__(
        self,
        detail: Any = "Forbidden",
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers,
        )

class BadRequestException(AppException):
    """Exception raised for invalid requests"""
    def __init__(
        self,
        detail: Any = "Bad request",
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers,
        )

class ConflictException(AppException):
    """Exception raised for conflict situations"""
    def __init__(
        self,
        detail: Any = "Resource conflict",
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers,
        ) 