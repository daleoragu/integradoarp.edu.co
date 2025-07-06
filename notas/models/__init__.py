# notas/models/__init__.py

# Este archivo importa todos los modelos de sus respectivos archivos
# y los hace disponibles para que puedan ser importados desde 'notas.models'.

# --- CORRECCIÓN: Se añade FichaDocente a la lista de importación ---
from .perfiles import Curso, Docente, Estudiante, FichaEstudiante, FichaDocente

from .academicos import (
    AreaConocimiento, Materia, PeriodoAcademico, AsignacionDocente,
    Calificacion, IndicadorLogroPeriodo, ReporteParcial, Observacion,
    PlanDeMejoramiento, Asistencia, InasistenciasManualesPeriodo,
    ConfiguracionSistema, PublicacionBoletin, PublicacionBoletinFinal
)
from .comunicaciones import Mensaje, RegistroObservador, Notificacion
from .portal_models import DocumentoPublico, FotoGaleria, Noticia, ImagenCarrusel

# La variable __all__ es una buena práctica que define qué nombres
# se exportan cuando se hace 'from .models import *'.

# --- CORRECIÓN: Se añade FichaDocente a la lista __all__ ---
__all__ = [
    'Curso', 'Docente', 'Estudiante', 'FichaEstudiante', 'FichaDocente',
    'AreaConocimiento', 'Materia', 'PeriodoAcademico', 'AsignacionDocente',
    'Calificacion', 'IndicadorLogroPeriodo', 'ReporteParcial', 'Observacion',
    'PlanDeMejoramiento', 'Asistencia', 'InasistenciasManualesPeriodo',
    'ConfiguracionSistema', 'PublicacionBoletin', 'PublicacionBoletinFinal',
    'Mensaje', 'RegistroObservador', 'Notificacion',
    'DocumentoPublico', 'FotoGaleria', 'Noticia', 'ImagenCarrusel',
]