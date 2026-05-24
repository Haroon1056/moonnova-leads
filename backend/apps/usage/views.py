from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import get_usage_summary


class MyUsageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_usage_summary(request.user))