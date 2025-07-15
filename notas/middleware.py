# notas/middleware.py
from .models import Colegio
# Probando el commit
class ColegioMiddleware:
    """
    Middleware que identifica el colegio activo basándose en el dominio.
    Esta versión es más robusta para manejar errores de base de datos durante
    el despliegue y para seleccionar un colegio principal por defecto.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # No ejecutar este middleware para rutas del admin, para evitar problemas
        if request.path.startswith('/admin'):
            return self.get_response(request)

        # Limpia el host para obtener el dominio base
        host = request.get_host().split(':')[0].lower()
        if host.startswith('www.'):
            host = host[4:]
        
        # Inicializamos request.colegio como None para evitar errores
        request.colegio = None
        
        try:
            # --- LÓGICA MEJORADA ---
            # 1. Intenta encontrar el colegio por el dominio exacto.
            #    Ej: 'integradoapr.edu.co' o 'colegio2.mcolegio.com.co'
            request.colegio = Colegio.objects.get(domain=host)

        except Colegio.DoesNotExist:
            # Si no hay un dominio exacto, buscamos un colegio "principal"
            try:
                # 2. Busca el colegio que tenga marcada la casilla "Es el colegio principal".
                request.colegio = Colegio.objects.get(es_principal=True)
            except Colegio.DoesNotExist:
                # 3. Si tampoco hay un principal, toma el primero que encuentre como último recurso.
                request.colegio = Colegio.objects.first()
            except Exception:
                # Si hay cualquier otro error de base de datos, no hace nada y deja request.colegio como None.
                pass
                
        except Exception:
            # 4. ¡ESTA ES LA PARTE CLAVE!
            # Si ocurre CUALQUIER error de base de datos (como que la tabla o la columna no existan
            # durante el despliegue), simplemente ignora el error y deja request.colegio como None.
            # Esto permite que el proceso de migración de Render se complete sin que la app se rompa.
            pass
        
        response = self.get_response(request)
        return response
