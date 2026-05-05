from django.db import models

class Vaga(models.Model):
    empresa = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    nome = models.CharField(max_length=255)

    FAIXA_SALARIAL = [
        ('1', 'Até 1000'),
        ('2', '1000-2000'),
        ('3', '2000-3000'),
        ('4', 'Acima de 3000'),
    ]
    faixa_salarial = models.CharField(max_length=1, choices=FAIXA_SALARIAL)

    requisitos = models.TextField()

    ESCOLARIDADE = [
        ('fundamental', 'Fundamental'),
        ('medio', 'Médio'),
        ('tecnologo', 'Tecnólogo'),
        ('superior', 'Superior'),
        ('pos', 'Pós/MBA/Mestrado'),
        ('doutorado', 'Doutorado'),
    ]
    escolaridade_minima = models.CharField(max_length=20, choices=ESCOLARIDADE)

    STATUS = [
        ('aberta', 'Aberta'),
        ('encerrada', 'Encerrada'),
        ('preenchida', 'Preenchida'),
    ]
    status = models.CharField(max_length=15, choices=STATUS, default='aberta')

    criada_em = models.DateTimeField(auto_now_add=True)
