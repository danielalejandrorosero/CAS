# Generated by Django 5.2.3 on 2025-06-14 05:17

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(choices=[('ADMINISTRADOR', 'Administrador'), ('INSTRUCTOR', 'Instructor'), ('APRENDIZ', 'Aprendiz')], max_length=50, unique=True)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Rol',
                'verbose_name_plural': 'Roles',
            },
        ),
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('documento', models.CharField(max_length=20, unique=True, validators=[django.core.validators.RegexValidator(code='documento_numerico', message='El documento debe ser numérico', regex='^\\d+$')])),
                ('tipo_documento', models.CharField(choices=[('CC', 'Cédula de Ciudadanía'), ('TI', 'Tarjeta de Identidad'), ('CE', 'Cédula de Extranjería'), ('PAS', 'Pasaporte')], default='CC', max_length=5)),
                ('telefono', models.CharField(blank=True, max_length=15, null=True, validators=[django.core.validators.RegexValidator('^\\+?1?\\d{9,15}$', 'Formato de teléfono inválido')])),
                ('nombres', models.CharField(max_length=100)),
                ('apellidos', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('foto_perfil', models.ImageField(blank=True, null=True, upload_to='perfiles/')),
                ('activo', models.BooleanField(default=True)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('ultimo_acceso', models.DateTimeField(blank=True, null=True)),
                ('token_recuperacion', models.CharField(blank=True, max_length=255, null=True)),
                ('token_expiracion', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('rol', models.ForeignKey(db_column='rol_id', on_delete=django.db.models.deletion.PROTECT, to='usuarios.rol')),
            ],
            options={
                'verbose_name': 'Usuario',
                'verbose_name_plural': 'Usuarios',
                'db_table': 'usuarios',
                'indexes': [models.Index(fields=['documento'], name='usuarios_documen_db8db0_idx'), models.Index(fields=['email'], name='usuarios_email_0ff7b3_idx'), models.Index(fields=['rol'], name='usuarios_rol_id_040259_idx'), models.Index(fields=['activo'], name='usuarios_activo_3d49ab_idx')],
            },
        ),
    ]
