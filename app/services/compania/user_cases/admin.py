from app.db.models.usuarios import Usuario
from app.services.compania.interfaces import CompaniaCaseInterface
from typing import Optional

class AdminCompaniaCase(CompaniaCaseInterface):
    def obtener_filtros_para_listar_companias(self, usuario_actual: Usuario, search: Optional[str], tipo_documento_id: Optional[int]) -> dict:
        # Admin can only see their own company
        filters = {
            "exact_filters": {
                "id": usuario_actual.company_id,
            },
            "ilike_filters": {},
            "like_filters": {}
        }
        
        if search:
            filters["ilike_filters"]["nombre"] = f"%{search}%"
        if tipo_documento_id:
            filters["exact_filters"]["tipo_documento_id"] = tipo_documento_id

        return filters
    
    def obtener_filtro_para_totalizar_companias(self, usuario_actual: Usuario, tipo_documento_id: Optional[int]) -> dict:
        # Admin can only count their own company
        filters = {
            "exact_filters": {
                "id": usuario_actual.company_id,
            },
            "ilike_filters": {},
            "like_filters": {}
        }

        if tipo_documento_id:
            filters["exact_filters"]["tipo_documento_id"] = tipo_documento_id

        return filters
        
    def puede_ver_compania(self, usuario_actual: Usuario, compania_id: str) -> bool:
        """Admin can only view their own company"""
        return str(usuario_actual.company_id) == compania_id
        
    def puede_gestionar_companias(self, usuario_actual: Usuario) -> bool:
        """Admin can only manage their own company"""
        return True 