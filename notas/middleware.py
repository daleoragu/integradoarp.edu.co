# notas/middleware.py
from .models import Colegio

class ColegioMiddleware:
    """
    Middleware que identifica el colegio activo basándose en el dominio o subdominio.
    Esta versión corregida maneja tanto dominios personalizados (producción)
    como subdominios de localhost (desarrollo).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # No ejecutar este middleware para rutas del admin, para evitar problemas
        if request.path.startswith('/admin'):
            return self.get_response(request)

        host = request.get_host().split(':')[0].lower()
        
        request.colegio = None
        
        try:
            # --- LÓGICA CORREGIDA Y MEJORADA ---

            # 1. Intenta encontrar el colegio por el dominio personalizado (para producción).
            #    Ej: 'www.colegiobilinguesansebastian.com'
            try:
                request.colegio = Colegio.objects.get(domain=host)
            except Colegio.DoesNotExist:
                # 2. Si no lo encuentra y estamos en desarrollo (localhost),
                #    intenta encontrarlo por el subdominio (slug).
                if host.endswith('.localhost'):
                    # Extraemos el slug de 'colegio-bilingue-san-sebastian.localhost' -> 'colegio-bilingue-san-sebastian'
                    slug = host.split('.')[0]
                    try:
                        request.colegio = Colegio.objects.get(slug=slug)
                    except Colegio.DoesNotExist:
                        # Si el slug tampoco existe, se pasará a la lógica de fallback.
                        pass
            
            # 3. Lógica de Fallback: Si después de las búsquedas anteriores no se encontró un colegio.
            if not request.colegio:
                # Intenta encontrar un colegio marcado como principal.
                # (Necesitarías añadir un campo booleano 'es_principal' a tu modelo Colegio para que esto funcione).
                try:
                    request.colegio = Colegio.objects.get(es_principal=True)
                except (Colegio.DoesNotExist, AttributeError):
                    # Si no hay principal, no hace nada y deja que la vista decida.
                    pass

        except Exception:
            # Si ocurre cualquier otro error de base de datos (ej. durante migraciones),
            # se ignora para no romper el sitio. request.colegio seguirá siendo None.
            pass
        
        response = self.get_response(request)
        return response
