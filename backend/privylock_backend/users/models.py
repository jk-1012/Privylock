"""
User authentication models for PrivyLock - FIXED FOR PASSWORD AUTHENTICATION

CRITICAL FIX: Password Handling
✅ Frontend sends SHA-256(password)
✅ Backend stores SHA-256 directly (NOT PBKDF2)
✅ Backend checks password by comparing SHA-256 hashes
✅ This makes frontend and backend compatible

CHANGES FROM PREVIOUS VERSION:
✅ Changed encrypted_email to plain email (for verification)
✅ Added mobile_number field (REQUIRED, no OTP verification)
✅ Added google_id field (for Google OAuth)
✅ Added email_verified field
✅ Added auth_provider field (local or google)
✅ FIXED: Password stored as SHA-256, not PBKDF2
✅ FIXED: check_password() compares SHA-256 hashes directly

SECURITY NOTES:
- Email stored in plaintext (required for verification & OAuth)
- Mobile number stored in plaintext (for contact, no verification)
- Documents remain encrypted (zero-knowledge maintained)
- Password is SHA-256 hash (frontend generates it)
- Recovery key is SHA-256 hash
- Username is derived from SHA-256(email)
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
import uuid
import hashlib


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Fields:
    - id: UUID primary key
    - username: Auto-generated from email hash (SHA-256)
    - email: Plain email address (for verification)
    - mobile_number: Plain mobile number with country code
    - password: SHA-256 hash of password (NOT Django's PBKDF2!)
    - recovery_key_hash: SHA-256 hash for account recovery
    - google_id: Google OAuth ID (if registered via Google)
    - auth_provider: Authentication method (local or google)
    - email_verified: Whether email is verified
    - subscription_tier: User's subscription level
    - storage_used: Current storage usage in bytes
    """

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique user identifier"
    )

    # Username is SHA-256 hash of email (first 30 chars)
    username = models.CharField(
        max_length=255,
        unique=True,
        help_text="Hash of email for authentication"
    )

    # ✅ NEW: Plain email (required for verification and OAuth)
    email = models.EmailField(
        unique=True,
        help_text="User's email address (for verification and login)"
    )

    # ✅ NEW: Mobile number with validation (REQUIRED, no verification)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Mobile number must be in format: '+999999999'. Up to 15 digits allowed."
    )
    mobile_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        unique=True,
        help_text="Mobile number with country code (e.g., +911234567890)"
    )

    # ✅ NEW: Email verification status
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether email address is verified"
    )

    # ✅ NEW: Email verification token
    email_verification_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Token for email verification"
    )

    # ✅ NEW: Google OAuth integration
    google_id = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text="Google OAuth user ID"
    )

    # ✅ NEW: Authentication provider
    auth_provider = models.CharField(
        max_length=20,
        choices=[
            ('local', 'Local (Email/Password)'),
            ('google', 'Google OAuth'),
        ],
        default='local',
        help_text="How user registered"
    )

    recovery_key_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 hash of recovery key"
    )

    subscription_tier = models.CharField(
        max_length=20,
        choices=[
            ('FREE', 'Free'),
            ('PREMIUM', 'Premium'),
            ('FAMILY', 'Family'),
            ('LIFETIME', 'Lifetime'),
        ],
        default='FREE',
        help_text="User's subscription level"
    )

    storage_used = models.BigIntegerField(
        default=0,
        help_text="Total storage used in bytes"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.email} ({self.get_auth_provider_display()})"

    def set_password(self, raw_password):
        """
        ✅ CRITICAL FIX: Store SHA-256 hash directly (NOT PBKDF2)

        Frontend sends SHA-256(password), so we just store it as-is.
        No additional hashing needed!

        This makes the password hash consistent between:
        - Registration: frontend sends SHA-256 → backend stores SHA-256
        - Login: frontend sends SHA-256 → backend compares SHA-256
        """
        # If already a SHA-256 hash (64 hex chars), store as-is
        if len(raw_password) == 64 and all(c in '0123456789abcdef' for c in raw_password):
            self.password = raw_password
        else:
            # If plain password (shouldn't happen), hash it
            self.password = hashlib.sha256(raw_password.encode()).hexdigest()

    def check_password(self, raw_password):
        """
        ✅ CRITICAL FIX: Compare SHA-256 hashes directly

        Frontend sends SHA-256(password), so we just compare it
        with the stored SHA-256 hash.

        No PBKDF2, no Django password hashing - just direct comparison!
        """
        # If already a SHA-256 hash (64 hex chars), compare directly
        if len(raw_password) == 64 and all(c in '0123456789abcdef' for c in raw_password):
            password_hash = raw_password
        else:
            # If plain password (shouldn't happen), hash it first
            password_hash = hashlib.sha256(raw_password.encode()).hexdigest()

        return self.password == password_hash

    def has_storage_space(self, file_size):
        """Check if user has enough storage for file."""
        from django.conf import settings
        limits = {
            'FREE': 1073741824,        # 1 GB
            'PREMIUM': 26843545600,    # 25 GB
            'FAMILY': 107374182400,    # 100 GB
            'LIFETIME': 10737418240,   # 10 GB
        }
        limit = limits.get(self.subscription_tier, limits['FREE'])
        return (self.storage_used + file_size) <= limit

    def generate_email_verification_token(self):
        """Generate unique token for email verification."""
        import secrets
        self.email_verification_token = secrets.token_urlsafe(32)
        self.save(update_fields=['email_verification_token'])
        return self.email_verification_token


class Device(models.Model):
    """
    Represents a trusted device for a user.
    Used for device-based authentication and security.

    Fields:
    - device_id: Unique identifier from client
    - device_name: Human-readable name (e.g., "Chrome on MacBook")
    - device_type: Platform (web, android, ios)
    - is_trusted: Whether device is verified
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='devices'
    )

    device_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Client-generated unique device identifier"
    )

    device_name = models.CharField(
        max_length=255,
        help_text="User-friendly device name"
    )

    device_type = models.CharField(
        max_length=50,
        choices=[
            ('web', 'Web Browser'),
            ('android', 'Android App'),
            ('ios', 'iOS App'),
        ],
        default='web'
    )

    is_trusted = models.BooleanField(
        default=False,
        help_text="Whether this device is verified and trusted"
    )

    last_active = models.DateTimeField(
        auto_now=True,
        help_text="Last time this device was used"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'devices'
        unique_together = ['user', 'device_id']
        ordering = ['-last_active']

    def __str__(self):
        return f"{self.device_name} ({self.device_type})"