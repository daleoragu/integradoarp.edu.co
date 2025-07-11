# Generated by Django 5.2.1 on 2025-06-26 04:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0020_fichaestudiante_documento'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fichaestudiante',
            old_name='documento',
            new_name='numero_documento',
        ),
        migrations.AddField(
            model_name='fichaestudiante',
            name='tipo_documento',
            field=models.CharField(choices=[('CC', 'Cédula de Ciudadanía'), ('TI', 'Tarjeta de Identidad'), ('RC', 'Registro Civil'), ('CE', 'Cédula de Extranjería'), ('OT', 'Otro')], default='TI', max_length=2, verbose_name='Tipo de Documento'),
        ),
        migrations.AlterField(
            model_name='fichaestudiante',
            name='grupo_sanguineo',
            field=models.CharField(blank=True, choices=[('O+', 'O+'), ('O-', 'O-'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-')], max_length=3, verbose_name='Grupo Sanguíneo y RH'),
        ),
    ]
