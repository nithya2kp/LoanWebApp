from rest_framework import serializers
from .models import User
from django.contrib.auth import get_user_model
import os
from django.conf import settings
from urllib.parse import urljoin

User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password','username']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists!!")
        return value
    
    def create(self, validated_data):
        user = User(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
        )
        user.set_password(validated_data.get('password'))
        user.save()
        return user

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, required=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            self.context['user'] = User.objects.get(email=value)
            return value
        else:
            raise serializers.ValidationError("Email not registerd!!")
        
    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.method == 'PUT':
            if not attrs.get('new_password'):
                raise serializers.ValidationError("New password needs to be provided!!")
        return attrs
    

class UpdateUserDetailsSerializer(serializers.Serializer):
    pancard = serializers.CharField(write_only=True, required=False)
    aadhar = serializers.CharField(write_only=True, required=False)
    location = serializers.CharField(write_only=True, required=False)
    username = serializers.CharField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)
    image = serializers.ImageField(required=False)
    
    def validate_username(self, value):
        current_user = self.context.get('user')
        if not current_user:
            raise serializers.ValidationError("Current user is not provided.")
        if User.objects.filter(username=value).exclude(pk=current_user.pk).exists():
            raise serializers.ValidationError("This username is already taken by another user.")
        return value

    def update(self, instance, validated_data):
        image_file = validated_data.pop('image', None)
        for attr, value in validated_data.items():
            if attr == 'new_password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        if image_file:
            upload_subdir = 'profile_images'
            upload_dir = os.path.join(settings.MEDIA_ROOT, upload_subdir)
            os.makedirs(upload_dir, exist_ok=True)

            filename = image_file.name
            image_path = os.path.join(upload_dir, filename)

            with open(image_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)
            relative_path = os.path.join(upload_subdir, filename)
            instance.profile_url = relative_path
        instance.save()
        return instance
    
class UploadCsvSerializer(serializers.Serializer):
    file = serializers.FileField()

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        csv_file = validated_data['file']

        upload_subdir = 'transaction_csv'
        upload_dir = os.path.join(settings.MEDIA_ROOT, upload_subdir)
        os.makedirs(upload_dir, exist_ok=True)

        filename = csv_file.name
        file_path = os.path.join(upload_dir, filename)

        # Save file to disk
        with open(file_path, 'wb+') as destination:
            for chunk in csv_file.chunks():
                destination.write(chunk)

        # Build relative and absolute URL
        relative_path = os.path.join(upload_subdir, filename).replace("\\", "/")
        media_url = request.build_absolute_uri(settings.MEDIA_URL)
        full_url = urljoin(media_url, relative_path)

        user.csv_file_url = full_url
        user.save()

        return user
    

class AuthenticationSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class TokenResponseSerializer(serializers.Serializer):
    access_token  = serializers.CharField()
    token_type    = serializers.CharField(default='Bearer')
    expires_in    = serializers.IntegerField()
    refresh_token = serializers.CharField()