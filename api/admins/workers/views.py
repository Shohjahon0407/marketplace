from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from api.admins.workers.serializers import WorkerCreateSerializer, WorkerUpdateSerializer, WorkerListSerializer
from apps.accounts.models import User


class WorkerCrud(ModelViewSet):
    queryset = User.objects.filter(is_worker=True)
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return WorkerCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return WorkerUpdateSerializer

        return WorkerListSerializer
