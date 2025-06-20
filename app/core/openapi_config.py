from fastapi.openapi.utils import get_openapi
from app.core.config import settings
from fastapi import FastAPI


class OpenAPIConfig:
    def __init__(self, app: FastAPI):
        self.app = app
        self.app.openapi_schema = self._custom_openapi()

    def get_openapi(self):
        return self.app.openapi_schema

    def _custom_openapi(self):
        if self.app.openapi_schema:
            return self.app.openapi_schema
        openapi_schema = get_openapi(
            title=settings.app_name,
            version="0.1.0",
            description="VertiOne con autenticación por JWT",
            routes=self.app.routes,
        )
        
        # Initialize components if it doesn't exist
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
            
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your JWT token"
            }
        }
        
        # Apply security to all protected routes
        for path_item in openapi_schema["paths"]:
            for method in openapi_schema["paths"][path_item]:
                if method.lower() in ["get", "post", "put", "delete", "patch"]:
                    operation = openapi_schema["paths"][path_item][method]
                    
                    # Skip health check endpoint
                    if path_item == "/" and method.lower() == "get":
                        continue
                        
                    # Apply security to all other endpoints
                    operation["security"] = [{"BearerAuth": []}]
        
        self.app.openapi_schema = openapi_schema
        return openapi_schema