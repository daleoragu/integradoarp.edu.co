# Generated by Django 5.2.1 on 2025-06-25 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0018_fotogaleria_noticia'),
    ]

    operations = [
        migrations.AddField(
            model_name='noticia',
            name='estado',
            field=models.CharField(choices=[('BORRADOR', 'Borrador'), ('PUBLICADO', 'Publicado')], default='BORRADOR', max_length=10, verbose_name='Estado'),
        ),
    ]
