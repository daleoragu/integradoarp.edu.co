# notas/middleware.py

from .models import Colegio

class ColegioMiddleware:
    """
    Middleware que identifica el colegio activo basándose en el dominio.
    Incluye impresiones de depuración para rastrear el proceso en los logs.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.main_domain = "mcolegio.com.co"

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        # DEBUG: Imprime el host que se está procesando.
        print(f"DEBUG: Middleware - Host recibido: '{host}'")
        
        if host.startswith('www.'):
            host = host[4:]
            print(f"DEBUG: Middleware - Host sin 'www': '{host}'")

        request.colegio = None

        try:
            # Intenta encontrar el colegio por el campo 'domain'.
            request.colegio = Colegio.objects.get(domain=host)
            print(f"DEBUG: Middleware - Colegio encontrado por dominio: '{request.colegio.nombre}'")
        except Colegio.DoesNotExist:
            # Si no lo encuentra, verifica si es un subdominio.
            if host.endswith(f'.{self.main_domain}'):
                subdomain = host.split('.')[0]
                print(f"DEBUG: Middleware - Buscando por slug de subdominio: '{subdomain}'")
                if subdomain and subdomain != 'www':
                    try:
                        request.colegio = Colegio.objects.get(slug=subdomain)
                        print(f"DEBUG: Middleware - Colegio encontrado por slug: '{request.colegio.nombre}'")
                    except Colegio.DoesNotExist:
                        print("DEBUG: Middleware - No se encontró colegio por slug.")
                        pass
            else:
                print("DEBUG: Middleware - No se encontró colegio por dominio y no es un subdominio.")
        
        response = self.get_response(request)
        return response
