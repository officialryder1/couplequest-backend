from rest_framework import serializers
from .models import UserProfile
from .models import CustomUser as User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = UserProfile
        fields = ['user', 'xp', 'level', 'streak', 'last_active']

    def create(self, validated_data):
        user = validated_data.pop('user')
        user_profile = UserProfile.objects.create(user=user, **validated_data)
        return user_profile

    def update(self, instance, validated_data):
        instance.xp = validated_data.get('xp', instance.xp)
        instance.level = validated_data.get('level', instance.level)
        instance.streak = validated_data.get('streak', instance.streak)
        instance.last_active = validated_data.get('last_active', instance.last_active)
        instance.save()
        return instance
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Allow login via email or username (but priority to email)
        email = attrs.get('email', None)
        username = attrs.get('username', None)

        if email:
            user = User.objects.filter(email=email).first()
        elif username:
            user = User.objects.filter(username=username).first()
        else:
            raise serializers.ValidationError("Email or username is required.")
        
        if user:
            attrs['username'] = user.username
            return super().validate(attrs)
        else:
            raise serializers.ValidationError("User not found.")
    
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = User.objects.create_superuser(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        return user
    
class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = fields