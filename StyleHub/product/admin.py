from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Brand, Product, ProductImage, 
    ProductVariant, Review, Wishlist, Tag, 
    ProductView, SizeGuide
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_featured', 'order']

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['size', 'color', 'sku', 'stock', 'price_adjustment', 'is_active']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'product_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'current_price', 'stock', 
        'status', 'is_featured', 'is_active', 'created_at'
    ]
    list_filter = ['status', 'is_featured', 'is_active', 'category', 'gender', 'created_at']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['sku', 'created_at', 'updated_at', 'product_image_preview']
    list_editable = ['status', 'is_featured', 'is_active']
    list_per_page = 25
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'barcode', 'category', 'brand')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price', 'cost_price')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Inventory', {
            'fields': ('stock', 'low_stock_threshold', 'allow_backorder')
        }),
        ('Attributes', {
            'fields': ('gender', 'size', 'color', 'material', 'weight')
        }),
        ('Media', {
            'fields': ('main_image', 'product_image_preview')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('Status', {
            'fields': ('status', 'is_featured', 'is_active', 'published_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def product_image_preview(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.main_image.url)
        return "No Image"
    product_image_preview.short_description = "Image Preview"
    
    def current_price(self, obj):
        if obj.discount_price:
            return format_html(
                '<span style="text-decoration: line-through;">${}</span> <strong style="color: green;">${}</strong>',
                obj.price, obj.discount_price
            )
        return f"${obj.price}"
    current_price.short_description = "Price"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_verified_purchase', 'is_approved', 'helpful_count', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__username', 'title', 'content']
    list_editable = ['is_approved']
    readonly_fields = ['helpful_count']
    
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"
    
    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_reviews.short_description = "Disapprove selected reviews"

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['created_at']

@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['product__name', 'user__username', 'ip_address']
    readonly_fields = ['viewed_at']

@admin.register(SizeGuide)
class SizeGuideAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'description']
