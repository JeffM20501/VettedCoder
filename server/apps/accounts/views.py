from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics,status
from rest_framework_simplejwt.tokens import RefreshToken


from .serializers import RegisterSerlizer
class MeView(APIView):
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        user=request.user
        return Response({
            "id":str(user.pk),
            "username":user.get_username(),
        })

class RegisterView(generics.CreateAPIView):
    serializer_class=RegisterSerlizer
    permission_classes=[AllowAny]
    authentication_classes=[]
    
    def create(self, request, *args, **kwargs):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user=serializer.save()
        
        refresh=RefreshToken.for_user(user)
        return Response(
            {
                "user": {"id":user.id, "username":user.username, "email":user.email},
                "access": str(refresh.access_token),
                "refresh":str(refresh)
            }, 
            status=status.HTTP_201_CREATED,
        )