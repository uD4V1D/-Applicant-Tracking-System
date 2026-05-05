from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD

    def validate(self, attrs):
        email = attrs.get(self.username_field)
        password = attrs.get('password')
        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed(
                'Usuário não encontrado. Verifique o e-mail e a senha. '
                'Se ainda não possuir conta, faça cadastro.'
            )

        if not user.check_password(password):
            raise AuthenticationFailed('Senha incorreta para este e-mail.')

        attrs[self.username_field] = user.email
        return super().validate(attrs)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
