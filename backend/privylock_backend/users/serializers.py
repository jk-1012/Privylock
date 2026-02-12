"""
Serializers for user authentication API - UPDATED FOR PRIVYLOCK

MAJOR CHANGES:
✅ Removed encrypted_email handling
✅ Added plain email field
✅ Added mobile_number field (REQUIRED, no verification)
✅ Added Google OAuth support
✅ Added email verification serializer
✅ Removed all mobile verification/OTP code
✅ Changed LifeVault → PrivyLock branding

Handles data validation and transformation.
"""

from rest_framework import serializers
from .models import User, Device
from django.contrib.auth.password_validation import validate_password
import re


class UserRegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration (Email + Password + Mobile).

    Expected Input (from client):
    {
        "username": "84c5ae239907cf3c686ab70060924d",  # SHA-256(email)[0:30]
        "email": "user@example.com",  # Plain email (for verification)
        "mobile_number": "+911234567890",  # REQUIRED - with country code
        "password": "sha256_hash_of_password",
        "recovery_key_hash": "sha256_hash_of_recovery_key",
        "device_id": "unique_device_identifier",
        "device_name": "Chrome on MacBook Pro"
    }

    Process:
    1. Validate all fields
    2. Check email uniqueness
    3. Check mobile uniqueness
    4. Create user with provided username
    5. Send verification email
    6. Create device record
    7. Return user object
    """

    username = serializers.CharField(
        required=True,
        max_length=30,
        help_text="Username generated from email hash (frontend)"
    )

    email = serializers.EmailField(
        required=True,
        help_text="User's email address"
    )

    mobile_number = serializers.CharField(
        required=True,
        max_length=17,
        help_text="Mobile number with country code (e.g., +911234567890)"
    )

    password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Client-side SHA-256 hash of master password"
    )

    recovery_key_hash = serializers.CharField(
        required=True,
        write_only=True,
        help_text="SHA-256 hash of 12-word recovery key"
    )

    device_id = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Unique device identifier from client"
    )

    device_name = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Human-readable device name"
    )

    def validate_username(self, value):
        """Validate username format (should be hex string, 30 chars)."""
        if not value or len(value) != 30:
            raise serializers.ValidationError(
                "Username must be exactly 30 characters"
            )

        # Check if it's a valid hex string
        try:
            int(value, 16)
        except ValueError:
            raise serializers.ValidationError(
                "Username must be a valid hexadecimal string"
            )

        # Check if username already exists
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists"
            )

        return value

    def validate_email(self, value):
        """Validate email format and uniqueness."""
        # Convert to lowercase
        value = value.lower().strip()

        # Check if email already exists
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists"
            )

        return value

    def validate_mobile_number(self, value):
        """Validate mobile number format and uniqueness."""
        # Remove spaces and dashes
        value = value.replace(' ', '').replace('-', '')

        # Check format (should start with + and have 10-15 digits)
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError(
                "Mobile number must be in format: '+999999999'. Up to 15 digits allowed."
            )

        # Check if mobile already exists
        if User.objects.filter(mobile_number=value).exists():
            raise serializers.ValidationError(
                "A user with this mobile number already exists"
            )

        return value

    def validate_password(self, value):
        """Validate password hash format (SHA-256 = 64 hex chars)."""
        if len(value) != 64:
            raise serializers.ValidationError(
                "Password must be SHA-256 hash (64 characters)"
            )
        return value

    def create(self, validated_data):
        """
        Create new user and device.

        Algorithm:
        1. Extract device data
        2. Get username from frontend
        3. Get email and mobile
        4. Create user with provided username
        5. Hash password with Django's hasher
        6. Save user
        7. Generate verification token
        8. Create device record

        Returns:
            User object
        """
        # Step 1: Extract device data for later
        device_data = {
            'device_id': validated_data.pop('device_id'),
            'device_name': validated_data.pop('device_name'),
            'device_type': 'web'
        }

        # Step 2: Get username from frontend
        username = validated_data['username']

        # Step 3: Get email and mobile
        email = validated_data['email']
        mobile_number = validated_data['mobile_number']

        print(f"📝 Creating user: {email}")

        # Step 4: Create user instance
        user = User(
            username=username,
            email=email,
            mobile_number=mobile_number,
            recovery_key_hash=validated_data.get('recovery_key_hash', ''),
            auth_provider='local',
            email_verified=False,  # Must verify email
        )

        # Step 5: Hash password with Django's password hasher
        user.set_password(validated_data['password'])

        # Step 6: Save user to database
        user.save()

        print(f"✅ User created: {user.id}")

        # Step 7: Generate email verification token
        email_token = user.generate_email_verification_token()
        print(f"📧 Email verification token: {email_token}")

        # Step 8: Create device record (first device is trusted)
        device = Device.objects.create(
            user=user,
            is_trusted=True,
            **device_data
        )

        print(f"📱 Device created: {device.device_name}")

        # Note: Email will be sent in views.py
        return user


class GoogleLoginSerializer(serializers.Serializer):
    """
    Serializer for Google OAuth login.

    Expected Input:
    {
        "google_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjBkN...",
        "mobile_number": "+911234567890",  # REQUIRED for new users
        "device_id": "unique_device_identifier",
        "device_name": "Chrome on MacBook Pro"
    }

    Process:
    1. Verify Google token with Google API
    2. Extract email from Google profile
    3. Check if user exists
    4. If exists, log in
    5. If not exists, require mobile_number and create user
    6. Return user object
    """

    google_token = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Google OAuth ID token"
    )

    mobile_number = serializers.CharField(
        required=False,  # Only required for new users
        max_length=17,
        help_text="Mobile number (required for new Google users)"
    )

    device_id = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Unique device identifier from client"
    )

    device_name = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Human-readable device name"
    )

    def validate_google_token(self, value):
        """Verify Google token and extract user info."""
        from google.oauth2 import id_token
        from google.auth.transport import requests
        from django.conf import settings

        try:
            # Verify token with Google
            idinfo = id_token.verify_oauth2_token(
                value,
                requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID
            )

            # Check issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise serializers.ValidationError('Invalid token issuer')

            # Store user info for create() method
            self.context['google_user_info'] = {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'email_verified': idinfo.get('email_verified', False),
                'name': idinfo.get('name', ''),
            }

            return value

        except ValueError as e:
            raise serializers.ValidationError(f'Invalid Google token: {str(e)}')

    def validate(self, data):
        """Check if mobile_number is required."""
        google_info = self.context.get('google_user_info', {})

        # Check if user exists
        existing_user = None
        if google_info.get('google_id'):
            existing_user = User.objects.filter(google_id=google_info['google_id']).first()
        if not existing_user and google_info.get('email'):
            existing_user = User.objects.filter(email=google_info['email']).first()

        # If new user, mobile_number is REQUIRED
        if not existing_user and not data.get('mobile_number'):
            raise serializers.ValidationError({
                'mobile_number': 'Mobile number is required for new users'
            })

        # Validate mobile format if provided
        if data.get('mobile_number'):
            mobile = data['mobile_number'].replace(' ', '').replace('-', '')
            if not re.match(r'^\+?1?\d{9,15}$', mobile):
                raise serializers.ValidationError({
                    'mobile_number': "Mobile number must be in format: '+999999999'. Up to 15 digits allowed."
                })
            data['mobile_number'] = mobile

        return data

    def create(self, validated_data):
        """
        Create or get user from Google OAuth.

        If user exists (by email or google_id), log them in.
        If user doesn't exist, create new user with Google info + mobile.
        """
        google_info = self.context['google_user_info']
        device_data = {
            'device_id': validated_data['device_id'],
            'device_name': validated_data['device_name'],
            'device_type': 'web'
        }

        # Try to find existing user
        user = None

        # First, try by Google ID
        if google_info['google_id']:
            user = User.objects.filter(google_id=google_info['google_id']).first()

        # If not found, try by email
        if not user:
            user = User.objects.filter(email=google_info['email']).first()

        # If user exists
        if user:
            # Update Google ID if not set
            if not user.google_id:
                user.google_id = google_info['google_id']
                user.save(update_fields=['google_id'])

            # Create device if not exists
            Device.objects.get_or_create(
                user=user,
                device_id=device_data['device_id'],
                defaults={
                    'device_name': device_data['device_name'],
                    'device_type': device_data['device_type'],
                    'is_trusted': True
                }
            )

            print(f"✅ Existing user logged in via Google: {user.email}")
            return user

        # Create new user from Google (mobile_number is REQUIRED)
        import hashlib

        # Generate username from email
        email_hash = hashlib.sha256(google_info['email'].encode()).hexdigest()
        username = email_hash[:30]

        user = User.objects.create(
            username=username,
            email=google_info['email'],
            mobile_number=validated_data['mobile_number'],  # REQUIRED
            google_id=google_info['google_id'],
            auth_provider='google',
            email_verified=google_info['email_verified'],  # Google verifies email
        )

        # Google users don't have password (OAuth only)
        user.set_unusable_password()
        user.save()

        # Create device
        Device.objects.create(
            user=user,
            is_trusted=True,
            **device_data
        )

        print(f"✅ New user created via Google: {user.email}")

        return user


class VerifyEmailSerializer(serializers.Serializer):
    """
    Serializer for email verification.

    Expected Input:
    {
        "token": "email_verification_token_from_url"
    }
    """

    token = serializers.CharField(required=True)

    def validate_token(self, value):
        """Verify token exists and is valid."""
        user = User.objects.filter(email_verification_token=value).first()

        if not user:
            raise serializers.ValidationError("Invalid or expired verification token")

        if user.email_verified:
            raise serializers.ValidationError("Email already verified")

        self.context['user'] = user
        return value

    def save(self):
        """Mark email as verified."""
        user = self.context['user']
        user.email_verified = True
        user.email_verification_token = None
        user.save(update_fields=['email_verified', 'email_verification_token'])
        return user


class ResendVerificationSerializer(serializers.Serializer):
    """
    Serializer for resending email verification.

    Expected Input:
    {
        "email": "user@example.com"
    }
    """

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Check if user exists."""
        user = User.objects.filter(email=value).first()

        if not user:
            raise serializers.ValidationError("User not found")

        if user.email_verified:
            raise serializers.ValidationError("Email already verified")

        self.context['user'] = user
        return value

    def save(self):
        """Resend verification email."""
        user = self.context['user']
        token = user.generate_email_verification_token()
        return {'token': token}


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data.
    Returns non-sensitive user information.
    """

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'mobile_number',
            'email_verified',
            'auth_provider',
            'subscription_tier',
            'storage_used',
            'created_at',
            'last_login_at'
        ]
        read_only_fields = fields


class DeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for device information.
    """

    class Meta:
        model = Device
        fields = [
            'id',
            'device_name',
            'device_type',
            'is_trusted',
            'last_active',
            'created_at'
        ]
        read_only_fields = fields