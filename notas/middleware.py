# notas/middleware.py

from .models import Colegio

class ColegioMiddleware:
    """
    Middleware que identifica el colegio activo basándose en el dominio.
    Maneja tres casos:
    1. Dominios personalizados (ej: integradoapr.edu.co).
    2. El dominio principal de la plataforma (ej: mcolegio.com.co).
    3. Subdominios de la plataforma (ej: colegio-nuevo.mcolegio.com.co).
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # CORREGIDO: Se eliminó la 's' extra.
        self.main_domain = "mcolegio.com.co"

    def __call__(self, request):
        # Obtiene el host y lo limpia (elimina el puerto y 'www.')
        host = request.get_host().split(':')[0].lower()
        if host.startswith('www.'):
            host = host[4:]

        request.colegio = None

        # --- LÓGICA REESTRUCTURADA PARA MAYOR ROBUSTEZ ---

        # 1. Primero, intentar la coincidencia directa por el campo 'domain'.
        #    Esto funciona tanto para dominios personalizados como para el dominio principal.
        try:
            request.colegio = Colegio.objects.get(domain=host)
        except Colegio.DoesNotExist:
            # 2. Si no hay coincidencia directa, verificar si es un subdominio válido.
            #    Nos aseguramos de que termine en '.mcolegio.com.co'
            if host.endswith(f'.{self.main_domain}'):
                
                # Extraemos el 'slug' del subdominio de forma segura.
                # Ej: 'colegio-nuevo' de 'colegio-nuevo.mcolegio.com.co'
                subdomain = host.split('.')[0]
                
                try:
                    request.colegio = Colegio.objects.get(slug=subdomain)
                except Colegio.DoesNotExist:
                    # El subdominio es válido en formato, pero no está registrado en la BD.
                    # request.colegio permanecerá como None, y la vista mostrará la página de inicio.
                    pass
        
        # Continuar con la petición
        response = self.get_response(request)
        return response
