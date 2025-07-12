from typing import List
from app.schemas.comunes import LovElemento
from app.db.models.usuarios import Rol

class RolService:
    @staticmethod
    async def get_roles(current_role: Rol | None = None) -> List[LovElemento]:
        """Get all available roles"""
        roles = []
        print(current_role)
        if current_role == Rol.SUPER_ADMIN:
            roles = [
                {"id": "superAdmin", "name": "Super admin"},
                {"id": "admin", "name": "Admin"},
                {"id": "supervisor", "name": "Supervisor"},
                {"id": "technician", "name": "Tecnico"},
                {"id": "client", "name": "Cliente"}
            ]
        
        if current_role == Rol.ADMIN:
            roles = [
                {"id": "admin", "name": "Admin"},
                {"id": "supervisor", "name": "Supervisor"},
                {"id": "technician", "name": "Tecnico"},
                {"id": "client", "name": "Cliente"}

            ]
        
        if current_role == Rol.SUPERVISOR:
            roles = [
                {"id": "supervisor", "name": "Supervisor"},
                {"id": "technician", "name": "Tecnico"}
            ]
        
        if current_role == Rol.TECHNICIAN:
            roles = [
                {"id": "technician", "name": "Tecnico"}
            ]
        
                
        return roles
