# notas/middleware.py

from .models import Colegio

class ColegioMiddleware:
    """
    Middleware que identifica el colegio activo basándose en el dominio.
    Esta versión tiene una lógica simplificada y más robusta para asegurar
    el correcto funcionamiento del dominio principal y los subdominios.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.main_domain = "notas.mcolegio.com.co"

    def __call__(self, request):
        # Obtiene el host y lo limpia (elimina el puerto y 'www.')
        host = request.get_host().split(':')[0].lower()
        if host.startswith('www.'):
            host = host[4:]

        request.colegio = None

        # --- LÓGICA CORREGIDA Y SIMPLIFICADA ---

        # 1. Buscar una coincidencia EXACTA en el campo de dominio personalizado.
        #    Esto debería encontrar 'mcolegio.com.co' o 'integradoapr.edu.co'.
        try:
            request.colegio = Colegio.objects.get(domain=host)
        except Colegio.DoesNotExist:
            # 2. Si no se encuentra, y SOLO si no se encuentra, verificar si es un subdominio.
            #    La condición `host != self.main_domain` evita que el dominio principal
            #    sea procesado como un subdominio de sí mismo.
            if host.endswith(self.main_domain) and host != self.main_domain:
                
                # Extrae el slug (ej: 'colegio-nuevo' de 'colegio-nuevo.mcolegio.com.co')
                subdomain = host.replace(f'.{self.main_domain}', '')
                
                try:
                    request.colegio = Colegio.objects.get(slug=subdomain)
                except Colegio.DoesNotExist:
                    # El subdominio tiene el formato correcto pero no está registrado.
                    # request.colegio permanecerá como None.
                    pass
        
        # Todas las rutas de código terminan aquí, pasando la petición a la siguiente capa.
        response = self.get_response(request)
        return response
