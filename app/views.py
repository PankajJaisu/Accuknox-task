from rest_framework.views import APIView 
from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework import status
from .models import *
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from rest_framework.pagination import PageNumberPagination

class Signup(APIView):
    def post(self, request):
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        password = request.data.get('password')

        if not email or not first_name or not last_name or not password:
            return JsonResponse({'error': 'Email, name, and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'User with this email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        User.objects.create_user(
            username=email,  
            email=email.lower(),
            password=password,
            first_name = first_name,
            last_name = last_name

        )

        return JsonResponse({"message":"Signup Successful"}, status=status.HTTP_201_CREATED)
        

class Login(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email.lower(), password=password)
        if user is None:
            return JsonResponse({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response_data = {
            'id': user.id,
            'email': user.email,
            'name':user.first_name + " "+user.last_name,
            'tokens': {
                'access': access_token,
                'refresh': refresh_token
            }
        }

        return JsonResponse(response_data, status=status.HTTP_200_OK)




class SearchUser(APIView):
    def get(self, request):
        search_keyword = request.query_params.get('q', '')

        if not search_keyword:
            return JsonResponse({'error': 'Search keyword is required'}, status=status.HTTP_400_BAD_REQUEST)

        users = User.objects.filter(
            email__icontains=search_keyword
        ) | User.objects.filter(
            first_name__icontains=search_keyword
        ) | User.objects.filter(
            last_name__icontains=search_keyword
        )

        print("users::",users)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_users = paginator.paginate_queryset(users, request)
        print("users::",paginated_users)

        serializer = UserSerializer(paginated_users, many=True)

        return paginator.get_paginated_response(serializer.data)


