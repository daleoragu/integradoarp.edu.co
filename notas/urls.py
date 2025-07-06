# notas/urls.py
from django.urls import path
# --- Se actualizan las importaciones de las vistas ---
from .views import (
    auth_views,
    dashboard_views,
    admin_tools_views,
    ingreso_notas_views,
    indicador_views,
    plan_mejoramiento_views,
    observador_views,
    asistencia_views,
    consulta_views,
    reporte_views,
    boletin_views,
    export_views,
    import_views,     
    reporte_parcial_views,
    estadisticas_views,
    sabana_views,
    mensajeria_views,
    importar_asistencia_views,
    estudiante_observador_views,
    notificaciones_views,
    publicacion_views,
    estudiante_boletin_views,
    portal_views,
    portal_admin_views,
    impersonation_views,
    # Se añaden los nuevos módulos de vistas de gestión
    gestion_docentes_views,
    gestion_estudiantes_views,
    gestion_academica_views,
)

urlpatterns = [
    # --- Rutas del Portal Público y Autenticación ---
    path('', portal_views.portal_vista, name='portal'),
    path('logout/', auth_views.logout_vista, name='logout'),
    path('logout/confirmacion/', auth_views.logout_confirmacion_vista, name='logout_confirmacion'),
    path('dashboard/', dashboard_views.dashboard_vista, name='dashboard'),
    path('perfil/cambiar-password/', auth_views.cambiar_password_vista, name='cambiar_password'),

    # --- Rutas de Paneles de Usuario ---
    path('panel-administrador/', dashboard_views.admin_dashboard_vista, name='admin_dashboard'),
    path('panel-docente/', dashboard_views.docente_dashboard_vista, name='panel_docente'),
    path('panel-estudiante/', dashboard_views.estudiante_dashboard_vista, name='panel_estudiante'),

    # --- Rutas de Herramientas de Administración General ---
    path('panel-administrador/control-periodos/', admin_tools_views.panel_control_periodos_vista, name='panel_control_periodos'),
    path('panel-administrador/control-promocion/', admin_tools_views.panel_control_promocion_vista, name='panel_control_promocion'),
    path('panel-administrador/estadisticas/', estadisticas_views.panel_estadisticas_vista, name='panel_estadisticas'),
    path('panel-administrador/publicar-boletines/', publicacion_views.panel_publicacion_vista, name='panel_publicacion'),

    # --- RUTAS PARA EL PANEL DE CONFIGURACIÓN DEL PORTAL ---
    path('panel-administrador/configuracion-portal/', portal_admin_views.configuracion_portal_vista, name='configuracion_portal'),
    path('panel-administrador/gestion-documentos/', portal_admin_views.gestion_documentos_vista, name='gestion_documentos'),
    path('panel-administrador/eliminar-documento/<int:pk>/', portal_admin_views.eliminar_documento_vista, name='eliminar_documento'),
    path('panel-administrador/gestion-galeria/', portal_admin_views.gestion_galeria_vista, name='gestion_galeria'),
    path('panel-administrador/eliminar-foto/<int:pk>/', portal_admin_views.eliminar_foto_vista, name='eliminar_foto'),
    path('panel-administrador/gestion-noticias/', portal_admin_views.gestion_noticias_vista, name='gestion_noticias'),
    path('panel-administrador/crear-noticia/', portal_admin_views.crear_noticia_vista, name='crear_noticia'),
    path('panel-administrador/editar-noticia/<int:pk>/', portal_admin_views.editar_noticia_vista, name='editar_noticia'),
    path('panel-administrador/eliminar-noticia/<int:pk>/', portal_admin_views.eliminar_noticia_vista, name='eliminar_noticia'),
    path('portal/noticia/<int:pk>/', portal_views.noticia_detalle_vista, name='noticia_detalle'),
    path('panel-administrador/publicar-noticia/<int:pk>/', portal_admin_views.publicar_noticia_vista, name='publicar_noticia'),
    path('panel-administrador/gestion-carrusel/', portal_admin_views.gestion_carrusel_vista, name='gestion_carrusel'),
    path('panel-administrador/eliminar-imagen-carrusel/<int:pk>/', portal_admin_views.eliminar_imagen_carrusel_vista, name='eliminar_imagen_carrusel'),
    
    # --- Rutas del Panel Docente ---
    path('docente/ingresar-notas/', ingreso_notas_views.ingresar_notas_periodo_vista, name='ingresar_notas_periodo'),
    path('docente/reporte-parcial/', reporte_parcial_views.reporte_parcial_vista, name='reporte_parcial'),
    path('docente/planes-mejoramiento/', plan_mejoramiento_views.plan_mejoramiento_vista, name='plan_mejoramiento'),
    path('docente/asistencia/', asistencia_views.asistencia_vista, name='asistencia'),
    path('docente/consulta-asistencia/', consulta_views.consulta_asistencia_vista, name='consulta_asistencia'),
    path('docente/importar-asistencia/', importar_asistencia_views.importar_asistencia_excel_vista, name='importar_asistencia_excel'),

    # --- Rutas para CRUD de Indicadores ---
    path('indicador/crear/', indicador_views.crear_indicador_vista, name='crear_indicador'),
    path('indicador/<int:indicador_id>/editar/', indicador_views.editar_indicador_vista, name='editar_indicador'),
    path('indicador/<int:indicador_id>/eliminar/', indicador_views.eliminar_indicador_vista, name='eliminar_indicador'),

    # --- Rutas de Reportes y Plantillas ---
    path('reportes/consolidado-excel/', reporte_views.generar_reporte_consolidado_excel, name='generar_reporte_consolidado_excel'),
    path('reportes/consolidado-pdf/', reporte_views.generar_reporte_consolidado_pdf, name='generar_reporte_consolidado_pdf'),
    path('reportes/individual-excel/', reporte_views.generar_reporte_individual_excel, name='generar_reporte_individual_excel'),
    path('reportes/individual-pdf/', reporte_views.generar_reporte_individual_pdf, name='generar_reporte_individual_pdf'),

    # --- Rutas para Lógica AJAX ---
    path('ajax/guardar-todo/', ingreso_notas_views.guardar_todo_ajax, name='guardar_todo_ajax'),
    path('ajax/obtener-meses/', reporte_views.obtener_meses_periodo_ajax, name='ajax_obtener_meses'),
    path('ajax/guardar-asistencia/', asistencia_views.guardar_inasistencia_ajax, name='guardar_inasistencia_ajax'),
    path('ajax/datos-graficos/', estadisticas_views.datos_graficos_ajax, name='datos_graficos_ajax'),
    path('ajax/directorio-docentes/', portal_views.directorio_docentes_json, name='ajax_directorio_docentes'),
    path('ajax/documentos-publicos/', portal_views.documentos_publicos_json, name='ajax_documentos_publicos'),
    path('ajax/galeria-fotos/', portal_views.galeria_fotos_json, name='ajax_galeria_fotos'),
    path('ajax/noticias/', portal_views.noticias_json, name='ajax_noticias'),
    path('ajax/carrusel/', portal_views.carrusel_imagenes_json, name='ajax_carrusel'),
    
    # --- INICIO: NUEVAS RUTAS AJAX PARA SECCIONES DEL COLEGIO ---
    path('ajax/historia/', portal_views.ajax_historia, name='ajax_historia'),
    path('ajax/mision-vision/', portal_views.ajax_mision_vision, name='ajax_mision_vision'),
    path('ajax/modelo-pedagogico/', portal_views.ajax_modelo_pedagogico, name='ajax_modelo_pedagogico'),
    # --- FIN: NUEVAS RUTAS AJAX ---

    # --- Rutas de Boletines y Sábanas ---
    path('docente/selector-boletines/', boletin_views.selector_boletin_vista, name='selector_boletines'),
    path('docente/generar-boletin/', boletin_views.generar_boletin_vista, name='generar_boletin'),
    path('docente/selector-sabana/', sabana_views.selector_sabana_vista, name='selector_sabana'),
    path('docente/generar-sabana/', sabana_views.generar_sabana_vista, name='generar_sabana'),
    path('docente/exportar-sabana-excel/', sabana_views.exportar_sabana_excel, name='exportar_sabana_excel'),
    path('docente/generar-sabana-pdf/', sabana_views.generar_sabana_pdf, name='generar_sabana_pdf'),
 
    # --- URLs para CofraMail (Mensajería Interna) ---
    path('mensajes/componer/', mensajeria_views.componer_mensaje_vista, name='componer_mensaje'),
    path('mensajes/bandeja-entrada/', mensajeria_views.bandeja_entrada_vista, name='bandeja_entrada'),
    path('mensajes/ver/<int:mensaje_id>/', mensajeria_views.ver_mensaje_vista, name='ver_mensaje'),
    path('mensajes/enviados/', mensajeria_views.mensajes_enviados_vista, name='mensajes_enviados'),
    path('mensajes/borrar/<int:mensaje_id>/', mensajeria_views.borrar_mensaje_vista, name='borrar_mensaje'),
    path('mensajes/papelera/', mensajeria_views.papelera_vista, name='papelera'),
    path('mensajes/restaurar/<int:mensaje_id>/', mensajeria_views.restaurar_mensaje_vista, name='restaurar_mensaje'),
    path('mensajes/borrar-definitivo/<int:mensaje_id>/', mensajeria_views.borrar_definitivamente_vista, name='borrar_permanentemente_mensaje'),
    path('mensajes/borradores/', mensajeria_views.borradores_vista, name='borradores'),

    # --- URLs para el Observador (Docente/Admin) ---
    path('observador/seleccionar/', observador_views.observador_selector_vista, name='observador_selector'),
    path('observador/detalle/<int:estudiante_id>/', observador_views.vista_detalle_observador, name='vista_detalle_observador'),
    path('observador/crear/<int:estudiante_id>/', observador_views.crear_registro_observador_vista, name='crear_registro_observador'),
    path('observador/ficha/<int:estudiante_id>/editar/', observador_views.editar_ficha_vista, name='editar_ficha'),
    path('observador/pdf/<int:estudiante_id>/', observador_views.generar_observador_pdf_vista, name='generar_observador_pdf'),

    # --- URLs para el Panel del Estudiante ---
    path('estudiante/panel/', dashboard_views.estudiante_dashboard_vista, name='panel_estudiante'),
    path('estudiante/mi-observador/', estudiante_observador_views.mi_observador_vista, name='mi_observador'),
    path('estudiante/mis-boletines/', estudiante_boletin_views.mis_boletines_vista, name='mi_boletin'),
    
    # --- URLs para el Sistema de Notificaciones ---
    path('notificaciones/', notificaciones_views.lista_notificaciones_vista, name='lista_notificaciones'),
    path('ajax/obtener-notificaciones/', notificaciones_views.obtener_notificaciones_dropdown_ajax, name='obtener_notificaciones_dropdown'),
    path('ajax/marcar-leida/', notificaciones_views.marcar_notificacion_leida_ajax, name='marcar_notificacion_leida'),

    # ===============================================================
    # RUTAS ACTUALIZADAS APUNTANDO A LOS NUEVOS ARCHIVOS DE VISTAS
    # ===============================================================

    # --- Rutas de Suplantación ---
    path('suplantar/iniciar/<int:user_id>/', impersonation_views.iniciar_suplantacion, name='iniciar_suplantacion'),
    path('suplantar/detener/', impersonation_views.detener_suplantacion, name='detener_suplantacion'),

    # --- Panel Principal de Asignación Académica ---
    path('panel-administrador/asignacion-academica/', gestion_academica_views.gestion_asignacion_academica_vista, name='gestion_asignacion_academica'),
    path('panel-administrador/asignacion/crear/', gestion_academica_views.crear_asignacion_vista, name='crear_asignacion'),
    path('panel-administrador/asignacion/eliminar/<int:asignacion_id>/', gestion_academica_views.eliminar_asignacion_vista, name='eliminar_asignacion'),

    # --- Gestión de Docentes ---
    path('panel-administrador/gestion-docentes/', gestion_docentes_views.gestion_docentes_vista, name='gestion_docentes'),
    path('panel-administrador/gestion-docentes/crear/', gestion_docentes_views.crear_docente_vista, name='crear_docente'),
    path('panel-administrador/gestion-docentes/editar/<int:docente_id>/', gestion_docentes_views.editar_docente_vista, name='editar_docente'),
    path('panel-administrador/gestion-docentes/eliminar/<int:docente_id>/', gestion_docentes_views.eliminar_docente_vista, name='eliminar_docente'),

    # --- Gestión de Cursos / Grados ---
    path('panel-administrador/gestion-cursos/', gestion_academica_views.gestion_cursos_vista, name='gestion_cursos'),
    path('panel-administrador/gestion-cursos/crear/', gestion_academica_views.crear_curso_vista, name='crear_curso'),
    path('panel-administrador/gestion-cursos/editar/<int:curso_id>/', gestion_academica_views.editar_curso_vista, name='editar_curso'),
    path('panel-administrador/gestion-cursos/eliminar/<int:curso_id>/', gestion_academica_views.eliminar_curso_vista, name='eliminar_curso'),
    
    # --- Gestión de Estudiantes ---
    path('panel-administrador/gestion-estudiantes/', gestion_estudiantes_views.gestion_estudiantes_vista, name='gestion_estudiantes'),
    path('panel-administrador/gestion-estudiantes/crear/', gestion_estudiantes_views.crear_estudiante_vista, name='crear_estudiante'),
    path('panel-administrador/gestion-estudiantes/editar/<int:estudiante_id>/', gestion_estudiantes_views.editar_estudiante_vista, name='editar_estudiante'),
    path('panel-administrador/gestion-estudiantes/eliminar/<int:estudiante_id>/', gestion_estudiantes_views.eliminar_estudiante_vista, name='eliminar_estudiante'),
    
    # --- Gestión de Materias y Áreas ---
    path('panel-administrador/gestion-materias/', gestion_academica_views.gestion_materias_vista, name='gestion_materias'),
    path('panel-administrador/gestion-materias/crear/', gestion_academica_views.crear_materia_vista, name='crear_materia'),
    path('panel-administrador/gestion-materias/editar/<int:materia_id>/', gestion_academica_views.editar_materia_vista, name='editar_materia'),
    path('panel-administrador/gestion-materias/eliminar/<int:materia_id>/', gestion_academica_views.eliminar_materia_vista, name='eliminar_materia'),
    path('panel-administrador/gestion-areas/', gestion_academica_views.gestion_areas_vista, name='gestion_areas'),
    path('panel-administrador/gestion-areas/crear/', gestion_academica_views.crear_area_vista, name='crear_area'),
    path('panel-administrador/gestion-areas/editar/<int:area_id>/', gestion_academica_views.editar_area_vista, name='editar_area'),
    path('panel-administrador/gestion-areas/eliminar/<int:area_id>/', gestion_academica_views.eliminar_area_vista, name='eliminar_area'),

    # --- RUTAS PARA IMPORTACIÓN Y EXPORTACIÓN MASIVA ---
    path('panel-administrador/importar/', import_views.importacion_vista, name='importacion_datos'),
    path('panel-administrador/exportar-estudiantes/', export_views.exportar_estudiantes_excel, name='exportar_estudiantes_excel'),
    path('panel-administrador/descargar-plantilla-estudiantes/', export_views.descargar_plantilla_estudiantes, name='descargar_plantilla_estudiantes'),
    path('panel-administrador/exportar-materias/', export_views.exportar_materias_excel, name='exportar_materias_excel'),
    path('panel-administrador/descargar-plantilla-materias/', export_views.descargar_plantilla_materias, name='descargar_plantilla_materias'),
    path('panel-administrador/descargar-plantilla-docentes/', export_views.descargar_plantilla_docentes, name='descargar_plantilla_docentes'),   

     # --- INICIO: NUEVAS RUTAS AJAX PARA COMUNIDAD ---
    path('ajax/recursos-educativos/', portal_views.ajax_recursos_educativos, name='ajax_recursos_educativos'),
    path('ajax/redes-sociales/', portal_views.ajax_redes_sociales, name='ajax_redes_sociales'),
    # --- FIN: NUEVAS RUTAS AJAX ---
       
]
