from rest_framework.views import APIView 
from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework import status
from .models import *
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated 
from datetime import timedelta
from django.utils import timezone

class Signup(APIView):
    def post(self, request):
        try:
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
                username=email.lower(),  
                email=email.lower(),
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            return JsonResponse({"message": "Signup Successful"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class Login(APIView):
    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')

            if not email or not password:
                return JsonResponse({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

            user = authenticate(request, username=email, password=password)
            if user is None:
                return JsonResponse({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response_data = {
                'id': user.id,
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}",
                'tokens': {
                    'access': access_token,
                    'refresh': refresh_token
                }
            }

            return JsonResponse(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class SearchUser(APIView):
    def get(self, request):
        try:
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

            paginator = PageNumberPagination()
            paginator.page_size = 10
            paginated_users = paginator.paginate_queryset(users, request)

            serializer = UserSerializer(paginated_users, many=True)

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SendFriendRequest(APIView):
    def post(self, request):
        from_user = request.user
        to_user_id = request.data.get('to_user_id')

        if not to_user_id:
            return JsonResponse({'error': 'Recipient user ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if FriendRequest.objects.filter(from_user=from_user, to_user=to_user).exists():
            return JsonResponse({'error': 'Friend request already sent'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user has sent more than 3 friend requests in the last minute
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        recent_requests_count = FriendRequest.objects.filter(
            from_user=from_user, created_at__gte=one_minute_ago
        ).count()

        if recent_requests_count >= 3:
            return JsonResponse({'error': 'You can only send 3 friend requests per minute'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        FriendRequest.objects.create(from_user=from_user, to_user=to_user)

        return JsonResponse({'message': 'Friend request sent successfully'}, status=status.HTTP_201_CREATED)

class AcceptFriendRequest(APIView):
    permission_classes = (IsAuthenticated, )
    
    def post(self, request):
        user = request.user
        request_id = request.data.get('request_id')

        if not request_id:
            return JsonResponse({'error': 'Request ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            request_id = int(request_id)
            
            friend_request = FriendRequest.objects.get(id=request_id, to_user=user, status='pending')
            
            friend_request.status = 'accepted'
            friend_request.save()
            
            try:
                Friend.objects.get_or_create(user=user, friend=friend_request.from_user)
                Friend.objects.get_or_create(user=friend_request.from_user, friend=user)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return JsonResponse({'message': 'Friend request accepted'}, status=status.HTTP_200_OK)
        
        except FriendRequest.DoesNotExist:
            return JsonResponse({'error': 'Friend request not found or already processed'}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RejectFriendRequest(APIView):
    permission_classes = (IsAuthenticated, ) 
    def post(self, request):
        user = request.user
        request_id = request.data.get('request_id')

        if not request_id:
            return JsonResponse({'error': 'Request ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            friend_request = FriendRequest.objects.get(id=request_id, to_user=user, status='pending')
        except FriendRequest.DoesNotExist:
            return JsonResponse({'error': 'Friend request not found or already processed'}, status=status.HTTP_404_NOT_FOUND)

        friend_request.status = 'rejected'
        friend_request.save()

        return JsonResponse({'message': 'Friend request rejected'}, status=status.HTTP_200_OK)
class ListFriends(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        try:
            user = request.user
            
            friends = Friend.objects.filter(user=user)
            
            if friends.exists():
                friend_users = [friend.friend for friend in friends]
                serializer = UserSerializer(friend_users, many=True)
                return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)
            else:
                return JsonResponse({"message": "No friends found"}, status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ListPendingFriendRequests(APIView):
    permission_classes = (IsAuthenticated, ) 
    
    def get(self, request):
        try:
            user = request.user
            
            if not user:
                return JsonResponse({'error': 'User not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

            pending_requests = FriendRequest.objects.filter(to_user=user, status='pending')
            
            if not pending_requests.exists():
                return JsonResponse({'message': 'No pending friend requests'}, status=status.HTTP_204_NO_CONTENT)

            friends_with_requests = [
                {
                    'id': req.from_user.id,
                    'email': req.from_user.email,
                    'first_name': req.from_user.first_name,
                    'last_name': req.from_user.last_name,
                    'request_id': req.id
                } for req in pending_requests
            ]

            return JsonResponse(friends_with_requests, status=status.HTTP_200_OK, safe=False)

        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







