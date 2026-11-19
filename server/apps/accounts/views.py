from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

class MeView(APIView):
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        user=request.user
        return Response({
            "id":str(user.pk),
            "username":user.get_username(),
        })