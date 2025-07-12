# notas/middleware.py

from .models import Colegio

class ColegioMiddleware:
    """
    Middleware que identifica el colegio activo basándose en el dominio.
    Prioriza dominios personalizados y luego busca subdominios.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.main_domain = "mcolegios.com.co" # Tu dominio principal

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        
        # Limpiamos 'www.' para consistencia
        if host.startswith('www.'):
            host = host[4:]

        request.colegio = None

        # --- LÓGICA MEJORADA ---

        # 1. Buscar por dominio personalizado (ej: integradoapr.edu.co)
        try:
            request.colegio = Colegio.objects.get(domain=host)
        except Colegio.DoesNotExist:
            # 2. Si no se encuentra, verificar si es un subdominio de tu plataforma
            if host.endswith(self.main_domain):
                # Extraer el subdominio (ej: 'liceo-los-andes' de 'liceo-los-andes.mcolegios.com.co')
                subdomain = host.replace(f'.{self.main_domain}', '')
                
                # Evitar que 'www' o el dominio principal se consideren subdominios válidos
                if subdomain and subdomain != 'www':
                    try:
                        # Buscar el colegio por su 'slug'
                        request.colegio = Colegio.objects.get(slug=subdomain)
                    except Colegio.DoesNotExist:
                        pass # El subdominio no corresponde a ningún colegio

        response = self.get_response(request)
        return response
