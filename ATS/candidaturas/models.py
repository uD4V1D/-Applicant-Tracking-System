from django.db import models

class Candidatura(models.Model):
    candidato = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    vaga = models.ForeignKey('vagas.Vaga', on_delete=models.CASCADE)

    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('candidato', 'vaga')
