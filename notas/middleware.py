# notas/middleware.py

from .models import Colegio

class ColegioMiddleware:
    """
    Este middleware se encarga de identificar el colegio activo
    basándose en el dominio (hostname) de la petición entrante.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Este método se ejecuta una sola vez, al iniciar el servidor.

    def __call__(self, request):
        # Este método se ejecuta para CADA petición.

        # Obtenemos el hostname sin el puerto. Ej: 'www.integradoapr.edu.co' o 'localhost'
        host = request.get_host().split(':')[0]

        # Limpiamos el 'www.' si existe, para tener un dominio limpio.
        if host.startswith('www.'):
            host = host[4:]

        # Inicializamos request.colegio como None.
        request.colegio = None

        try:
            # Buscamos en la base de datos un colegio que coincida con el dominio.
            # Esta es la consulta clave de todo el sistema.
            request.colegio = Colegio.objects.get(domain=host)
        except Colegio.DoesNotExist:
            # Si no se encuentra un colegio para el dominio, request.colegio permanecerá como None.
            # Las vistas se encargarán de manejar este caso (mostrar un error 404, una página de bienvenida, etc.).
            pass

        # Pasamos la petición (ahora con 'request.colegio' adjunto) a la siguiente capa (la vista).
        response = self.get_response(request)

        return response
