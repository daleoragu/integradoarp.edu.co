# notas/middleware.py

from .models import Colegio

class ColegioMiddleware:
    """
    Middleware que identifica el colegio activo basándose en el dominio.
    Esta versión tiene una lógica mejorada para diferenciar claramente
    entre el dominio principal, dominios personalizados y subdominios.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.main_domain = "mcolegio.com.co"

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        if host.startswith('www.'):
            host = host[4:]

        request.colegio = None

        # --- LÓGICA CORREGIDA Y ROBUSTA ---

        # 1. Intenta la búsqueda por el campo 'domain'.
        #    Esto debería encontrar 'mcolegio.com.co' y cualquier otro dominio personalizado.
        try:
            request.colegio = Colegio.objects.get(domain=host)
            # Si se encuentra, la petición continúa con el colegio correcto.
            # No es necesario hacer más verificaciones.
            return self.get_response(request)
        except Colegio.DoesNotExist:
            # Si no se encuentra un dominio personalizado, se procede a verificar si es un subdominio.
            pass

        # 2. Verifica si es un subdominio de la plataforma principal.
        #    La condición host.count('.') > self.main_domain.count('.') asegura que
        #    'mcolegio.com.co' no sea tratado como un subdominio de sí mismo.
        if host.endswith(f'.{self.main_domain}') and host.count('.') > self.main_domain.count('.'):
            # Extrae el slug (ej: 'colegio-nuevo' de 'colegio-nuevo.mcolegio.com.co')
            subdomain = host.replace(f'.{self.main_domain}', '')
            try:
                request.colegio = Colegio.objects.get(slug=subdomain)
            except Colegio.DoesNotExist:
                # El subdominio tiene el formato correcto pero no corresponde a ningún colegio.
                # request.colegio permanecerá como None.
                pass
        
        # Finalmente, se pasa la petición a la siguiente capa (la vista).
        return self.get_response(request)
