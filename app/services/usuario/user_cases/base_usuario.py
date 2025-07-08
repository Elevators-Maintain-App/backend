from app.services.usuario.interfaces import UsuarioCaseInterface
from app.schemas.usuarios import UsuarioCreate
from app.db.models.compania import Compania
from app.db.models.enums.tipos_documento import TipoDocumento
from app.auth.firebase import UsuarioFirebaseCreate
import secrets
import string
from app.services.notificaciones import NotificacionService, TipoNotificacion
from app.services.notificaciones.templates import TemplateManager
from app.services.notificaciones.models import DestinatarioModel

class BaseUsuario(UsuarioCaseInterface):    
    def obtener_contraseña_temporal(self, length: int = 12) -> str:
        alphabet = (
            string.ascii_lowercase
            + string.ascii_uppercase
            + string.digits
            + "!@#$%&*"  # Símbolos básicos, evitando caracteres problemáticos
        )

        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def mapear_usuario_dto_a_usuario_firebase(self, usuario_nuevo: UsuarioCreate, compania: Compania, tipo_documento: TipoDocumento) -> UsuarioFirebaseCreate:
        password = self.obtener_contraseña_temporal(length=12)
        usuario_firebase = UsuarioFirebaseCreate(
                company_id=compania.id,
                password=password,
                company_name=compania.nombre,
                display_name=usuario_nuevo.display_name,
                document_id=str(usuario_nuevo.document_id),
                document_type=str(tipo_documento.id),
                document_type_name=tipo_documento.nombre,
                email=usuario_nuevo.email.lower(),
                photo_url= usuario_nuevo.photo_url if usuario_nuevo.photo_url else None,
                rol=usuario_nuevo.rol.value,
            )
                    
        return usuario_firebase
    
    def mapear_usuario_dto_a_usuario_create(self, usuario_nuevo: UsuarioCreate, firebase_uid: str) -> UsuarioCreate:
        usuario = UsuarioCreate(
                    uid=firebase_uid,
                    display_name=usuario_nuevo.display_name,
                    document_id=usuario_nuevo.document_id,
                    document_type_id=usuario_nuevo.document_type_id,
                    email=usuario_nuevo.email.lower(),
                    phone_number=usuario_nuevo.phone_number,
                    photo_url=usuario_nuevo.photo_url if usuario_nuevo.photo_url else None,
                    rol=usuario_nuevo.rol,
                    nivel=usuario_nuevo.nivel if usuario_nuevo.nivel else None,
                    zona_geografica_id=usuario_nuevo.zona_geografica_id if usuario_nuevo.zona_geografica_id else None,
                    is_active=usuario_nuevo.is_active,
                    company_id=usuario_nuevo.company_id,
                )

        return usuario
    
    async def enviar_email_de_bienvenida(self, email_destinatario: str, nombre_destinatario: str, password: str):
        notificacion_service = NotificacionService(TipoNotificacion.EMAIL)
        template_manager = TemplateManager()

        notificacion = template_manager.create_notification_from_template(
            template_name='bienvenida_usuario.html',
            destinatarios=[
                DestinatarioModel(
                    email=email_destinatario,
                    nombre=nombre_destinatario
                )
            ],
            asunto="Bienvenido a Verti-one",
            context={
                "password": password,
                "login_link": f"https://verti-one.com"
            }
        )

        return await notificacion_service.enviar_notificacion(notificacion)
    
    async def enviar_email_de_cambio_de_contraseña(self, email_destinatario: str, nombre_destinatario: str, password: str):
        notificacion_service = NotificacionService(TipoNotificacion.EMAIL)
        template_manager = TemplateManager()

        notificacion = template_manager.create_notification_from_template(
            template_name='cambio_de_contraseña.html',
            destinatarios=[
                DestinatarioModel(
                    email=email_destinatario,
                    nombre=nombre_destinatario
                )
            ],
            asunto="Cambio de contraseña",
            context={
                "login_link": f"https://verti-one.com"
            }
        )

        return await notificacion_service.enviar_notificacion(notificacion)