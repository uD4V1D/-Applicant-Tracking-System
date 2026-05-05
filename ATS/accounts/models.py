from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    nome_completo = models.CharField(max_length=255, blank=True, default='')
    data_nascimento = models.DateField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    TIPO_USUARIO = (
        ('empresa', 'Empresa'),
        ('candidato', 'Candidato'),
    )
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO)


class PerfilCandidato(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)

    ESCOLARIDADE = [
        ('fundamental', 'Ensino fundamental'),
        ('medio', 'Ensino médio'),
        ('tecnologo', 'Tecnólogo'),
        ('superior', 'Ensino Superior'),
        ('pos', 'Pós / MBA / Mestrado'),
        ('doutorado', 'Doutorado'),
    ]

    pretensao_salarial = models.IntegerField()
    experiencia = models.TextField(blank=True, default='')
    escolaridade = models.CharField(max_length=20, choices=ESCOLARIDADE)


class ExperienciaProfissional(models.Model):
    perfil = models.ForeignKey(
        'accounts.PerfilCandidato',
        on_delete=models.CASCADE,
        related_name='experiencias',
    )
    nome_empresa = models.CharField(max_length=255)
    data_inicio = models.DateField(null=True, blank=True)
    data_saida = models.DateField(null=True, blank=True)
    principais_responsabilidades = models.TextField()
    emprego_atual = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)


class PerfilEmpresa(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='perfil_empresa')
    nome_empresa = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=14, unique=True)
