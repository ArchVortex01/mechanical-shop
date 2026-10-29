from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Notification
from .auth_views import send_success, send_error

class ReadNotificationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, id):
        try:
            n = Notification.objects.get(id=id, user=request.user)
            n.is_read = True
            n.save()
            return send_success('Notification marked as read')
        except Notification.DoesNotExist:
            return send_error('Notification not found', status_code=status.HTTP_404_NOT_FOUND)

class ReadAllNotificationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return send_success('All notifications marked as read')
