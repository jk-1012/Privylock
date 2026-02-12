"""
Users App URL Configuration - UPDATED FOR PRIVYLOCK

Authentication and user management endpoints.

NEW ENDPOINTS:
✅ POST /api/auth/google/ - Google OAuth login
✅ GET /api/auth/verify-email/{token}/ - Email verification
✅ POST /api/auth/resend-verification/ - Resend verification email

REMOVED ENDPOINTS:
❌ POST /api/auth/verify-mobile/ - Mobile verification (removed)

Endpoints:
- POST /api/auth/register/ - Register new user (email + password + mobile)
- POST /api/auth/login/ - Login user (email/username + password)
- POST /api/auth/google/ - Login with Google OAuth
- POST /api/auth/token/refresh/ - Refresh JWT token
- GET /api/auth/verify-email/{token}/ - Verify email address
- POST /api/auth/verify-email/ - Verify email (POST with token in body)
- POST /api/auth/resend-verification/ - Resend verification email
- GET /api/auth/me/ - Get current user info
- GET /api/auth/devices/ - List user's devices
- DELETE /api/auth/devices/{id}/ - Remove device
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # ========================================
    # REGISTRATION & LOGIN
    # ========================================

    # Traditional email/password/mobile registration
    path('register/', views.register, name='register'),

    # Traditional email/password login
    path('login/', views.login, name='login'),

    # ✅ NEW: Google OAuth login (mobile required for new users)
    path('google/', views.google_login, name='google_login'),

    # ========================================
    # JWT TOKEN MANAGEMENT
    # ========================================

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ========================================
    # EMAIL VERIFICATION (ONLY)
    # ========================================

    # ✅ Email verification (GET with token in URL)
    path('verify-email/<str:token>/', views.verify_email, name='verify_email_get'),

    # ✅ Email verification (POST with token in body)
    path('verify-email/', views.verify_email, name='verify_email_post'),

    # ✅ Resend verification email
    path('resend-verification/', views.resend_verification, name='resend_verification'),

    # ========================================
    # USER PROFILE
    # ========================================

    path('me/', views.get_user_info, name='user_info'),

    # ========================================
    # DEVICE MANAGEMENT
    # ========================================

    path('devices/', views.list_devices, name='list_devices'),
    path('devices/<uuid:device_id>/', views.remove_device, name='remove_device'),

    # ========================================
    # ACCOUNT RECOVERY (Future Implementation)
    # ========================================

    # path('recover/', views.recover_account, name='recover_account'),
    # path('reset-password/', views.reset_password, name='reset_password'),
]