from django.utils.timezone import now
from datetime import timedelta
from oauthlib.common import generate_token
from oauth2_provider.models import AccessToken, Application,RefreshToken
from django.http import HttpResponse
from rest_framework.decorators import api_view,permission_classes,authentication_classes,parser_classes
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated,AllowAny
from drf_yasg.utils import swagger_auto_schema
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
import os
from django.contrib.auth import authenticate
from rest_framework.parsers import MultiPartParser, FormParser

from user.serializers import SignupSerializer,PasswordResetSerializer,UpdateUserDetailsSerializer,UploadCsvSerializer,AuthenticationSerializer,TokenResponseSerializer
from .tasks import calculate_credit_score

# Create your views here.

def index(request):
    return HttpResponse("Hello World!!")

@swagger_auto_schema(method='get', tags=['user'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([OAuth2Authentication])
def  hello_world(request):
    return Response({'message': 'Hello, World!'})

@swagger_auto_schema(method='post', tags=['user'],request_body=SignupSerializer,security=[])
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def signup_view(request):
    # verification_link = f"{base_url}verification?token={token}"
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        try:
            application = Application.objects.get(name="loan-management-app")
        except Application.DoesNotExist:
            return Response({'error': 'OAuth2 application not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        token = generate_token()
        expires = now() + timedelta(days=1)

        access_token = AccessToken.objects.create(
            user=user,
            application=application,
            expires=expires,
            token=token,
            scope='read write'
        )
        
        RefreshToken.objects.create(
            user=user,
            token=generate_token(),
            application=application,
            access_token=access_token
        )

        subject = 'Verify your email'
        message = f"Welcome to our app!\n\nPlease verify your email using this token:\n\n{access_token.token}\n\nThis token will expire in 24 hours."
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        try:
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            return Response(
                {'error': f'Failed to send email: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({"message":"Please verify your email for signup completion"}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='get', tags=['user'])
@api_view(['GET'])
@authentication_classes([OAuth2Authentication])
@permission_classes([IsAuthenticated])
def login_view(request):
    access_token = request.auth
    return Response({"message":"User logged in successfully"},status=status.HTTP_200_OK)


@swagger_auto_schema(method='post', tags=['user'],request_body=PasswordResetSerializer,security=[])
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def password_reset_view(request):
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.context['user']
        
        try:
            application = Application.objects.get(name="loan-management-app")
        except Application.DoesNotExist:
            return Response({'error': 'OAuth2 application not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        token = generate_token()
        expires = now() + timedelta(days=1)

        access_token = AccessToken.objects.create(
            user=user,
            application=application,
            expires=expires,
            token=token,
            scope='read write'
        )

        subject = 'Password Reset Request'
        message = (
            "You have requested to reset your password.\n\n"
            f"Please click the following link to reset your password:\n\n{access_token.token}\n\n"
            "This link will expire in 1 hour.\n\n"
            "If you did not request this, please ignore this email."
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        try:
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            return Response(
                {'error': f'Failed to send email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response({"message":"A reset link has been sent to tour registered email."},status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='put', tags=['user'],request_body=PasswordResetSerializer)
@api_view(['PUT'])
@authentication_classes([OAuth2Authentication])
@permission_classes([IsAuthenticated])
def update_password_view(request):
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.context['user']

        if request.user != user:
            return Response({"message":"You are not allowed to update this user's password!!"},
                            status=status.HTTP_403_FORBIDDEN)

        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', tags=['user'],request_body=UpdateUserDetailsSerializer)
@api_view(['PUT'])
@parser_classes([MultiPartParser, FormParser])
@authentication_classes([OAuth2Authentication])
@permission_classes([IsAuthenticated])
def update_user_details(request):
    serializer = UpdateUserDetailsSerializer(
        instance=request.user,
        data=request.data,
        context={'user': request.user},
        partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User details updated successfully."},status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', tags=['user'],request_body=UploadCsvSerializer, consumes=['multipart/form-data'])
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@authentication_classes([OAuth2Authentication])
@permission_classes([IsAuthenticated])
def upload_csv_file(request):
    serializer = UploadCsvSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'File uploaded successfully'},
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    tags=['auth'],
    request_body=AuthenticationSerializer,
    security=[]
)
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def token_authorization_view(request):
    serializer = AuthenticationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']

    user = authenticate(request, username=username, password=password)
    if not user:
        return Response(
            {"detail": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        app = Application.objects.get(name="loan-management-app")
    except Application.DoesNotExist:
        return Response(
            {"detail": "OAuth2 application not found."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    try:
        access_token = AccessToken.objects.get(user=user, application=app)
        refresh_token = RefreshToken.objects.get(access_token=access_token)
    except (AccessToken.DoesNotExist, RefreshToken.DoesNotExist):
        return Response(
            {"detail": "Tokens not found. Please signup first."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    expires_in = int((access_token.expires - now()).total_seconds())
    if expires_in <= 0:
        access_token.delete()
        refresh_token.delete()

        new_access_token = AccessToken.objects.create(
            user=user,
            application=app,
            token=generate_token(),
            expires=now() + timedelta(days=1),
            scope='read write'
        )

        new_refresh_token = RefreshToken.objects.create(
            user=user,
            token=generate_token(),
            application=app,
            access_token=new_access_token
        )

        expires_in = int((new_access_token.expires - now()).total_seconds())

        token_data = {
            "access_token": new_access_token.token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_token": new_refresh_token.token,
        }

    else:
        token_data = {
            "access_token": access_token.token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_token": refresh_token.token,
        }

    response_serializer = TokenResponseSerializer(token_data)
    return Response(response_serializer.data, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def credit_score_calc_view(request):
    user = request.user
    if not user.csv_file_url:
        return Response({"detail": "CSV URL not set for this user."}, status=400)

    calculate_credit_score.delay(user.id)
    return Response({"message": "Credit score calculation started."}, status=202)
