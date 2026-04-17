from django import forms
from django.utils.text import slugify
from .models import Product, Category, Brand, Review, ProductVariant, ProductImage

class ProductForm(forms.ModelForm):
    """
    Form for creating/updating products
    """
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'brand', 'description', 'short_description',
            'price', 'discount_price', 'cost_price', 'stock', 'low_stock_threshold',
            'allow_backorder', 'gender', 'size', 'color', 'material', 'weight',
            'main_image', 'status', 'is_featured', 'is_active',
            'meta_title', 'meta_description', 'meta_keywords'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'short_description': forms.Textarea(attrs={'rows': 3}),
            'meta_description': forms.Textarea(attrs={'rows': 3}),
            'meta_keywords': forms.TextInput(attrs={'placeholder': 'Comma-separated keywords'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        
        if discount_price and discount_price >= price:
            raise forms.ValidationError("Discount price must be less than regular price.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.name)
        if commit:
            instance.save()
        return instance


class CategoryForm(forms.ModelForm):
    """
    Form for creating/updating categories
    """
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'parent', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class BrandForm(forms.ModelForm):
    """
    Form for creating/updating brands
    """
    class Meta:
        model = Brand
        fields = ['name', 'logo', 'description', 'website', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ReviewForm(forms.ModelForm):
    """
    Form for product reviews
    """
    class Meta:
        model = Review
        fields = ['title', 'content', 'rating']
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'content': forms.Textarea(attrs={'rows': 4}),
        }


class ProductVariantForm(forms.ModelForm):
    """
    Form for product variants
    """
    class Meta:
        model = ProductVariant
        fields = ['size', 'color', 'sku', 'stock', 'price_adjustment', 'image', 'is_active']


class ProductImageForm(forms.ModelForm):
    """
    Form for product additional images
    """
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_featured', 'order']


class ProductFilterForm(forms.Form):
    """
    Form for filtering products on listing page
    """
    SORT_CHOICES = (
        ('newest', 'Newest'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low'),
        ('popular', 'Most Popular'),
        ('rated', 'Top Rated'),
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories"
    )
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.filter(is_active=True),
        required=False,
        empty_label="All Brands"
    )
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    size = forms.ChoiceField(choices=[('', 'All Sizes')] + Product.SIZE_CHOICES, required=False)
    gender = forms.ChoiceField(choices=[('', 'All')] + list(Product.GENDER_CHOICES), required=False)
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False, initial='newest')
    search = forms.CharField(required=False, max_length=100)
    
    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError("Minimum price cannot be greater than maximum price.")
        
        return cleaned_data