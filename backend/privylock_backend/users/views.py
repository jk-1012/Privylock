"""
API views for user authentication - FIXED FOR PASSWORD AUTHENTICATION

CRITICAL FIX: Authentication Backend
✅ Custom authentication backend that uses SHA-256 comparison
✅ No longer relies on Django's PBKDF2 hasher
✅ Frontend sends SHA-256(password)
✅ Backend compares SHA-256 directly

Handles registration, login, token management, email verification.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer,
    GoogleLoginSerializer,
    VerifyEmailSerializer,
    ResendVerificationSerializer,
    UserSerializer,
    DeviceSerializer
)
from .models import Device
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register new user.

    POST /api/auth/register/

    Request Body:
    {
        "username": "hash_from_email",
        "email": "user@example.com",
        "mobile_number": "+911234567890",
        "password": "sha256_hash",
        "recovery_key_hash": "sha256_hash",
        "device_id": "unique_id",
        "device_name": "Chrome on Mac"
    }

    Response (201 Created):
    {
        "success": true,
        "user_id": "uuid",
        "email_verified": false,
        "mobile_verified": true,
        "message": "Registration successful. Please verify your email to login."
    }

    Response (400 Bad Request):
    {
        "success": false,
        "errors": {...}
    }

    ✅ NO AUTO-LOGIN! User must verify email and login manually.
    """
    try:
        serializer = UserRegistrationSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            # Create user (NO auto-login!)
            user = serializer.save()

            logger.info(f"✅ New user registered: {user.email}")

            # Send verification email
            try:
                send_verification_email(user, user.email_verification_token)
                logger.info(f"📧 Verification email sent to: {user.email}")
                if not email_sent:
                    logger.warning(f"⚠️ Email not sent but registration completed for {user.email}")
            except Exception as e:
                logger.error(f"❌ Failed to send verification email: {e}")

            return Response({
                'success': True,
                'user_id': str(user.id),
                'email_verified': user.email_verified,
                'mobile_verified': True,  # Always true (no OTP)
                'message': 'Registration successful. Please check your email to verify your account, then login.'
            }, status=status.HTTP_201_CREATED)

        # Return validation errors
        logger.warning(f"❌ Registration failed: {serializer.errors}")
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        # Log unexpected errors
        logger.error(f"❌ Registration error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'An error occurred during registration'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Authenticate user and return JWT tokens.

    POST /api/auth/login/

    Request Body:
    {
        "username": "hash_of_email",
        "password": "sha256_hash"
    }

    Response (200 OK):
    {
        "access": "jwt_access_token",
        "refresh": "jwt_refresh_token"
    }

    Response (401 Unauthorized):
    {
        "detail": "Invalid credentials"
    }

    Response (403 Forbidden):
    {
        "detail": "Please verify your email before logging in."
    }

    ✅ FIXED: Uses custom SHA-256 authentication (not Django's PBKDF2)
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            'detail': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Find user by username
        user = User.objects.get(username=username)

        logger.info(f"🔐 Login attempt for user: {user.email}")

        # ✅ CRITICAL FIX: Use custom check_password() method
        # This compares SHA-256 hashes directly
        if not user.check_password(password):
            logger.warning(f"❌ Failed login attempt for username: {username}")
            return Response({
                'detail': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Check email verification
        if not user.email_verified:
            logger.warning(f"⚠️ Login blocked - email not verified: {user.email}")
            return Response({
                'detail': 'Please verify your email before logging in. Check your inbox for the verification link.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        # Update last login
        from django.utils import timezone
        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])

        logger.info(f"✅ User logged in successfully: {user.email}")

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.warning(f"❌ Failed login attempt for username: {username}")
        return Response({
            'detail': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Login or register with Google OAuth.

    POST /api/auth/google/

    Request Body:
    {
        "google_token": "google_id_token",
        "mobile_number": "+911234567890",  # Required for new users
        "device_id": "unique_device_id",
        "device_name": "Chrome on Mac"
    }

    Response (200 OK):
    {
        "access": "jwt_access_token",
        "refresh": "jwt_refresh_token",
        "user": {...},
        "is_new_user": true/false
    }
    """
    try:
        serializer = GoogleLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Generate tokens
            refresh = RefreshToken.for_user(user)

            # Update last login
            from django.utils import timezone
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])

            is_new_user = serializer.context.get('is_new_user', False)

            logger.info(f"✅ Google OAuth successful: {user.email} (new={is_new_user})")

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
                'is_new_user': is_new_user
            }, status=status.HTTP_200_OK)

        logger.warning(f"❌ Google OAuth failed: {serializer.errors}")
        return Response({
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ Google OAuth error: {str(e)}", exc_info=True)
        return Response({
            'error': 'Google authentication failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def verify_email(request, token=None):
    """
    Verify user's email address.

    GET /api/auth/verify-email/{token}/
    POST /api/auth/verify-email/ with {"token": "..."}

    Response (200 OK):
    {
        "success": true,
        "message": "Email verified successfully! You can now login."
    }

    Response (400 Bad Request):
    {
        "error": "Invalid or expired token"
    }
    """
    # Handle both GET (token in URL) and POST (token in body)
    if request.method == 'GET':
        verification_token = token
    else:
        verification_token = request.data.get('token')

    if not verification_token:
        return Response({
            'error': 'Verification token is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        serializer = VerifyEmailSerializer(data={'token': verification_token})

        if serializer.is_valid():
            user = serializer.save()

            logger.info(f"✅ Email verified: {user.email}")

            return Response({
                'success': True,
                'message': 'Email verified successfully! You can now login.'
            }, status=status.HTTP_200_OK)

        logger.warning(f"❌ Email verification failed: {serializer.errors}")
        return Response({
            'error': serializer.errors.get('token', ['Invalid verification token'])[0]
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ Email verification error: {str(e)}", exc_info=True)
        return Response({
            'error': 'Email verification failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification(request):
    """
    Resend email verification link.

    POST /api/auth/resend-verification/

    Request Body:
    {
        "email": "user@example.com"
    }

    Response (200 OK):
    {
        "success": true,
        "message": "Verification email sent! Please check your inbox."
    }
    """
    try:
        serializer = ResendVerificationSerializer(data=request.data)

        if serializer.is_valid():
            result = serializer.save()

            # Send verification email
            user = serializer.context['user']
            send_verification_email(user, result['token'])

            logger.info(f"📧 Verification email resent to: {user.email}")

            return Response({
                'success': True,
                'message': 'Verification email sent! Please check your inbox.'
            }, status=status.HTTP_200_OK)

        return Response({
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"❌ Resend verification error: {str(e)}", exc_info=True)
        return Response({
            'error': 'Failed to resend verification email'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """
    Get current user's profile information.

    GET /api/auth/me/

    Headers:
    Authorization: Bearer <access_token>

    Response (200 OK):
    {
        "id": "uuid",
        "email": "user@example.com",
        "mobile_number": "+911234567890",
        "email_verified": true,
        "auth_provider": "local",
        "subscription_tier": "FREE",
        "storage_used": 1234567,
        "created_at": "2026-01-30T00:00:00Z",
        "last_login_at": "2026-01-30T12:00:00Z"
    }
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_devices(request):
    """
    List all devices for current user.

    GET /api/auth/devices/

    Response:
    [
        {
            "id": "uuid",
            "device_name": "Chrome on MacBook",
            "device_type": "web",
            "is_trusted": true,
            "last_active": "2026-01-30T12:00:00Z"
        }
    ]
    """
    devices = request.user.devices.all()
    serializer = DeviceSerializer(devices, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_device(request, device_id):
    """
    Remove a device from user's trusted devices.

    DELETE /api/auth/devices/{device_id}/

    Response (200 OK):
    {
        "success": true,
        "message": "Device removed successfully"
    }

    Response (404 Not Found):
    {
        "error": "Device not found"
    }
    """
    try:
        device = Device.objects.get(
            id=device_id,
            user=request.user
        )

        device_name = device.device_name
        device.delete()

        logger.info(f"🗑️ Device {device_id} removed by user {request.user.id}")

        return Response({
            'success': True,
            'message': f'Device "{device_name}" removed successfully'
        }, status=status.HTTP_200_OK)

    except Device.DoesNotExist:
        return Response({
            'error': 'Device not found'
        }, status=status.HTTP_404_NOT_FOUND)


def send_verification_email(user, token):
    """
    Send email verification link to user.

    Uses Django's email backend to send verification email.

    TODO: Configure email settings in settings.py:
    - EMAIL_BACKEND
    - EMAIL_HOST
    - EMAIL_PORT
    - EMAIL_HOST_USER
    - EMAIL_HOST_PASSWORD
    - EMAIL_USE_TLS
    - DEFAULT_FROM_EMAIL
    """
    from django.core.mail import send_mail
    from django.conf import settings

    verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"

    subject = "Verify your PrivyLock email address"
    message = f"""
    Welcome to PrivyLock!

    Please verify your email address by clicking the link below:

    {verification_url}

    This link will expire in 24 hours.

    If you didn't create an account with PrivyLock, please ignore this email.

    Thanks,
    The PrivyLock Team
    """

    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4CAF50;">Welcome to PrivyLock! 🔐</h2>

            <p>Thank you for creating an account with PrivyLock.</p>

            <p>Please verify your email address by clicking the button below:</p>

            <p style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}"
                   style="background-color: #4CAF50; color: white; padding: 12px 30px;
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Verify Email Address
                </a>
            </p>

            <p style="color: #666; font-size: 14px;">
                Or copy and paste this link into your browser:<br>
                <a href="{verification_url}">{verification_url}</a>
            </p>

            <p style="color: #666; font-size: 14px;">
                This link will expire in 24 hours.
            </p>

            <hr style="border: 1px solid #eee; margin: 30px 0;">

            <p style="color: #999; font-size: 12px;">
                If you didn't create an account with PrivyLock, please ignore this email.
            </p>

            <p style="color: #999; font-size: 12px;">
                Thanks,<br>
                The PrivyLock Team
            </p>
        </div>
    </body>
    </html>
    """

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send verification email: {str(e)}", exc_info=True)
        return False