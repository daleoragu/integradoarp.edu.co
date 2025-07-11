# Generated by Django 5.2.1 on 2025-06-24 23:48

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0017_documentopublico'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FotoGaleria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(help_text='Un título o descripción corta.', max_length=150, verbose_name='Título de la Foto')),
                ('imagen', models.ImageField(upload_to='galeria_portal/', verbose_name='Fotografía')),
                ('fecha_subida', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Foto de la Galería',
                'verbose_name_plural': 'Fotos de la Galería',
                'ordering': ['-fecha_subida'],
            },
        ),
        migrations.CreateModel(
            name='Noticia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=255, verbose_name='Titular de la Noticia')),
                ('resumen', models.CharField(help_text='Un párrafo corto que aparecerá en la lista de noticias.', max_length=500, verbose_name='Resumen Corto')),
                ('cuerpo', models.TextField(verbose_name='Contenido Completo de la Noticia')),
                ('imagen_portada', models.ImageField(blank=True, null=True, upload_to='noticias_portal/', verbose_name='Imagen de Portada')),
                ('fecha_publicacion', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de Publicación')),
                ('autor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Autor')),
            ],
            options={
                'verbose_name': 'Noticia',
                'verbose_name_plural': 'Noticias',
                'ordering': ['-fecha_publicacion'],
            },
        ),
    ]
