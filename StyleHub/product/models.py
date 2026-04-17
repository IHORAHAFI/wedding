from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
try:
    from PIL import Image
except Exception:
    Image = None
import os

User = get_user_model()

class Category(models.Model):
    """
    Product Category Model
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('product:category_detail', kwargs={'slug': self.slug})
    
    @property
    def product_count(self):
        """Return number of active products in this category.

        When a queryset is annotated with `product_count`, Django will set this
        attribute on the model instance. Having a setter prevents the
        "property ... has no setter" error while still allowing the
        attribute to be computed when unset.
        """
        if hasattr(self, '_product_count'):
            return self._product_count
        return self.products.filter(is_active=True).count()

    @product_count.setter
    def product_count(self, value):
        self._product_count = value


class Brand(models.Model):
    """
    Product Brand Model
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Main Product Model
    """
    # Gender choices
    GENDER_CHOICES = (
        ('M', 'Men'),
        ('W', 'Women'),
        ('K', 'Kids'),
        ('U', 'Unisex'),
    )
    
    # Size choices for clothing
    SIZE_CHOICES = (
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double Extra Large'),
        ('3XL', 'Triple Extra Large'),
    )
    
    # Status choices
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
        ('discontinued', 'Discontinued'),
    )
    
    # Basic Information
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    sku = models.CharField(max_length=50, unique=True, blank=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, blank=True, help_text="Product barcode")
    
    # Relationships
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT,
        related_name='products'
    )
    brand = models.ForeignKey(
        Brand, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='products'
    )
    
    # Product Details
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)]
    )
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Supplier cost (for internal use)"
    )
    
    # Inventory
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    allow_backorder = models.BooleanField(default=False)
    
    # Attributes
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='U')
    size = models.CharField(max_length=3, choices=SIZE_CHOICES, default='M')
    color = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)
    weight = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Weight in kg"
    )
    
    # Media
    main_image = models.ImageField(upload_to='products/main/', blank=True, null=True)
    
    # SEO and Meta
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    meta_keywords = models.CharField(max_length=300, blank=True)
    
    # Status and Dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Generate SKU if not provided
        if not self.sku:
            prefix = self.category.name[:3].upper() if self.category else 'PRD'
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.sku = f"{prefix}{timestamp}"
        
        # Set published date if status becomes active
        if self.status == 'active' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('product:detail', kwargs={'slug': self.slug})
    
    @property
    def current_price(self):
        """Return discount price if available, otherwise regular price"""
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.discount_price and self.discount_price < self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock > 0 or self.allow_backorder
    
    @property
    def is_low_stock(self):
        """Check if stock is low"""
        return 0 < self.stock <= self.low_stock_threshold
    
    def reduce_stock(self, quantity):
        """Reduce stock by given quantity"""
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False
    
    def increase_stock(self, quantity):
        """Increase stock by given quantity"""
        self.stock += quantity
        self.save()


class ProductImage(models.Model):
    """
    Additional Product Images
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='additional_images'
    )
    image = models.ImageField(upload_to='products/additional/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Optimize image
        if self.image and Image is not None:
            img_path = self.image.path
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    if img.height > 800 or img.width > 800:
                        output_size = (800, 800)
                        img.thumbnail(output_size)
                        img.save(img_path)
                except Exception:
                    # If image processing fails, skip silently to avoid blocking model saves
                    pass


class ProductVariant(models.Model):
    """
    Product Variants (Size, Color combinations)
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='variants'
    )
    size = models.CharField(max_length=3, choices=Product.SIZE_CHOICES)
    color = models.CharField(max_length=50)
    sku = models.CharField(max_length=50, unique=True)
    stock = models.PositiveIntegerField(default=0)
    price_adjustment = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Price difference from base product"
    )
    image = models.ImageField(upload_to='products/variants/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['product', 'size', 'color']
    
    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"
    
    @property
    def price(self):
        """Calculate variant price"""
        return self.product.current_price + self.price_adjustment


class Review(models.Model):
    """
    Product Reviews
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # One review per user per product
    
    def __str__(self):
        return f"Review by {self.user.username} on {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Check if user has purchased this product
        from orders.models import OrderItem
        self.is_verified_purchase = OrderItem.objects.filter(
            order__user=self.user,
            product=self.product,
            order__status='delivered'
        ).exists()
        super().save(*args, **kwargs)


class Wishlist(models.Model):
    """
    User Wishlist
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='wishlist'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.product.name}"


class Tag(models.Model):
    """
    Product Tags
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    products = models.ManyToManyField(Product, related_name='tags', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductView(models.Model):
    """
    Track Product Views
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='views'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    ip_address = models.GenericIPAddressField()
    session_key = models.CharField(max_length=40, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"View of {self.product.name} at {self.viewed_at}"


class SizeGuide(models.Model):
    """
    Size Guide for different categories
    """
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='size_guides'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='size_guides/', blank=True, null=True)
    content = models.JSONField(default=dict, help_text="Size measurements in JSON format")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Size Guide: {self.category.name} - {self.title}"
