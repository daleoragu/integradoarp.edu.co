#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Instalar las dependencias
pip install -r requirements.txt

# 2. Recolectar archivos estáticos
python manage.py collectstatic --no-input

# 3. Aplicar las migraciones de la base de datos
# Esta es la línea más importante. Asegurará que el esquema de la BD
# coincida con tus modelos de Django.
python manage.py migrate

# (Opcional) Si sigues teniendo problemas, puedes usar el comando 'flush'
# para borrar TODOS los datos de la base de datos antes de migrar.
# ¡CUIDADO! Esto borrará todos los usuarios y colegios que hayas creado.
# Descomenta la siguiente línea solo si es absolutamente necesario.
# python manage.py flush --no-input
