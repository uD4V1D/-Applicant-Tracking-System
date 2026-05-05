from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PerfilCandidato
from .serializers import (
    PerfilCandidatoSerializer,
    RegisterSerializer,
    UserProfileReadSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)


class MeView(RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UserProfileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return Response(UserProfileReadSerializer(request.user).data)

    def put(self, request):
        serializer = UserProfileUpdateSerializer(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserProfileReadSerializer(user).data)

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserProfileReadSerializer(user).data)


class PerfilCandidatoView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def _get_profile(self, user):
        if user.tipo != 'candidato':
            raise PermissionDenied('Apenas candidatos podem gerenciar perfil.')
        try:
            return user.perfilcandidato
        except ObjectDoesNotExist:
            return None

    def get(self, request):
        profile = self._get_profile(request.user)
        if profile is None:
            return Response({'detail': 'Perfil de candidato não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PerfilCandidatoSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile = self._get_profile(request.user)
        if profile is None:
            profile = PerfilCandidato(user=request.user)
        serializer = PerfilCandidatoSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data)

    def patch(self, request):
        profile = self._get_profile(request.user)
        if profile is None:
            profile = PerfilCandidato(user=request.user)
        serializer = PerfilCandidatoSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data)
