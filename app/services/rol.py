from typing import List
from app.schemas.comunes import LovElemento


class RolService:
    @staticmethod
    async def get_roles(current_role: str) -> List[LovElemento]:
        """Get all available roles"""
        roles = []
        if current_role == "superAdmin":
            roles = [
                {"id": "superAdmin", "name": "Super admin"},
                {"id": "admin", "name": "Admin"},
                {"id": "supervisor", "name": "Supervisor"},
                {"id": "technician", "name": "Tecnico"}
            ]
        
        if current_role == "admin":
            roles = [
                {"id": "admin", "name": "Admin"},
                {"id": "supervisor", "name": "Supervisor"},
                {"id": "technician", "name": "Tecnico"}
            ]
        
        if current_role == "supervisor":
            roles = [
                {"id": "supervisor", "name": "Supervisor"},
                {"id": "technician", "name": "Tecnico"}
            ]
        
        if current_role == "technician":
            roles = [
                {"id": "technician", "name": "Tecnico"}
            ]
        
                
        return roles
