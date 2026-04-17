from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class User(AbstractUser):
    """
    Custom User model with two roles: Admin and Client
    Includes personal information fields
    """
    
    # Role choices
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('client', 'Client'),
    )
    
    # Phone number validation (optional but recommended)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    # Personal information fields
    first_name = models.CharField(
        max_length=50,
        blank=False,  # Required field
        help_text="User's first name"
    )
    
    last_name = models.CharField(
        max_length=50,
        blank=False,  # Required field
        help_text="User's last name"
    )
    
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,  # Optional field
        help_text="Contact phone number"
    )
    
    # Role field
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='client',
        help_text="Designates the role of the user."
    )
    
    # Additional optional fields you might want to include
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text="Optional profile picture"
    )
    
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="User's date of birth"
    )
    
    # Address fields (optional but useful for e-commerce)
    address_line1 = models.CharField(
        max_length=255,
        blank=True,
        help_text="Street address"
    )
    
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        help_text="Apartment, suite, unit, etc."
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City"
    )
    
    state = models.CharField(
        max_length=100,
        blank=True,
        help_text="State/Province"
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="ZIP/Postal code"
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        default='USA',
        help_text="Country"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.username}) - {self.role}"
    
    def get_full_name(self):
        """
        Returns the full name of the user
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def get_short_name(self):
        """
        Returns the short name of the user
        """
        return self.first_name if self.first_name else self.username
    
    @property
    def is_admin(self):
        """
        Check if user is admin
        """
        return self.role == 'admin'
    
    @property
    def is_client(self):
        """
        Check if user is client
        """
        return self.role == 'client'
    
    @property
    def full_address(self):
        """
        Returns the complete formatted address
        """
        address_parts = []
        if self.address_line1:
            address_parts.append(self.address_line1)
        if self.address_line2:
            address_parts.append(self.address_line2)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)
        
        return ', '.join(address_parts) if address_parts else 'No address provided'