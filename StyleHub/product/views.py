from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import (
    ListView, DetailView, CreateView, 
    UpdateView, DeleteView, TemplateView, View
)
from django.db.models import Q, Count, Avg, Min, Max
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.cache import cache
from .models import (
    Product, Category, Brand, Review, 
    ProductVariant, ProductImage, Wishlist, 
    Tag, ProductView, SizeGuide
)
from .forms import (
    ProductForm, CategoryForm, BrandForm, 
    ReviewForm, ProductVariantForm, ProductImageForm,
    ProductFilterForm
)
try:
    from cart.models import Cart
except Exception:
    Cart = None
from django.contrib.auth import get_user_model

User = get_user_model()

# ==================== MIXINS ====================

class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin to restrict access to admin users only"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_admin:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('account:home')
        return super().dispatch(request, *args, **kwargs)


class ProductTrackingMixin:
    """Mixin to track product views"""
    
    def track_product_view(self, request, product):
        """Track product view for analytics"""
        if request.user.is_authenticated:
            user = request.user
        else:
            user = None
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Create view record
        ProductView.objects.create(
            product=product,
            user=user,
            ip_address=ip,
            session_key=request.session.session_key
        )


# ==================== PRODUCT VIEWS ====================

class ProductListView(ListView):
    """List all products with filtering, searching, and pagination"""
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(
            is_active=True, 
            status='active'
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            'reviews', 'additional_images'
        )
        
        # Apply filters from form (validation and search/price/gender sorting)
        form = ProductFilterForm(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data
            
            # Search
            if data.get('search'):
                queryset = queryset.filter(
                    Q(name__icontains=data['search']) |
                    Q(description__icontains=data['search']) |
                    Q(sku__icontains=data['search']) |
                    Q(category__name__icontains=data['search']) |
                    Q(brand__name__icontains=data['search']) |
                    Q(tags__name__icontains=data['search'])
                ).distinct()

            # Gender filter
            if data.get('gender'):
                queryset = queryset.filter(gender=data['gender'])

            # Price range
            if data.get('min_price'):
                queryset = queryset.filter(price__gte=data['min_price'])
            if data.get('max_price'):
                queryset = queryset.filter(price__lte=data['max_price'])

            # Sorting
            sort = data.get('sort', 'newest')
            if sort == 'price_low':
                queryset = queryset.order_by('price')
            elif sort == 'price_high':
                queryset = queryset.order_by('-price')
            elif sort == 'popular':
                queryset = queryset.annotate(
                    order_count=Count('orderitem')
                ).order_by('-order_count', '-created_at')
            elif sort == 'rated':
                queryset = queryset.annotate(
                    avg_rating=Avg('reviews__rating')
                ).order_by('-avg_rating', '-created_at')
            else:  # newest
                queryset = queryset.order_by('-created_at')

        # Category/brand/size are passed as slugs in the URL (often as multiple values via checkboxes). Use GET values directly.
        category_slugs = self.request.GET.getlist('category')
        if category_slugs:
            queryset = queryset.filter(category__slug__in=category_slugs)

        brand_slugs = self.request.GET.getlist('brand')
        if brand_slugs:
            queryset = queryset.filter(brand__slug__in=brand_slugs)

        sizes = self.request.GET.getlist('size')
        if sizes:
            queryset = queryset.filter(size__in=sizes)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter form
        context['filter_form'] = ProductFilterForm(self.request.GET)
        
        # Get all categories with product counts (only active + published products)
        context['categories'] = Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count(
                'products',
                filter=Q(products__is_active=True, products__status='active')
            )
        )
        
        # Get all brands with product counts (only active + published products)
        context['brands'] = Brand.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count(
                'products',
                filter=Q(products__is_active=True, products__status='active')
            )
        )
        
        # Get price range for filtering
        price_range = Product.objects.filter(
            is_active=True, status='active'
        ).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        context['min_price'] = price_range['min_price'] or 0
        context['max_price'] = price_range['max_price'] or 1000
        
        # Get popular tags
        context['popular_tags'] = Tag.objects.annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0)[:10]
        
        # Current filters for template
        context['current_filters'] = self.request.GET

        # Selected filter values (used for checkbox highlights and category pill state)
        context['selected_categories'] = self.request.GET.getlist('category')
        context['selected_brands'] = self.request.GET.getlist('brand')
        context['selected_sizes'] = self.request.GET.getlist('size')
        context['current_category'] = self.request.GET.get('category') if self.request.GET.getlist('category') else None

        return context


class ProductDetailView(DetailView, ProductTrackingMixin):
    """Display product details"""
    model = Product
    template_name = 'product/product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(
            is_active=True,
            status='active'
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            'additional_images',
            'variants',
            'reviews__user',
            'tags'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Track product view
        self.track_product_view(self.request, product)
        
        # Get related products (same category)
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True,
            status='active'
        ).exclude(id=product.id)[:4]
        
        # Get products from same brand
        if product.brand:
            context['brand_products'] = Product.objects.filter(
                brand=product.brand,
                is_active=True,
                status='active'
            ).exclude(id=product.id)[:4]
        
        # Get reviews with pagination
        reviews = product.reviews.filter(is_approved=True).select_related('user')
        paginator = Paginator(reviews, 5)
        page_number = self.request.GET.get('page')
        context['reviews'] = paginator.get_page(page_number)
        
        # Calculate average rating
        context['avg_rating'] = reviews.aggregate(Avg('rating'))['rating__avg']
        context['total_reviews'] = reviews.count()
        
        # Rating distribution
        rating_distribution = []
        for i in range(5, 0, -1):
            count = reviews.filter(rating=i).count()
            percentage = (count / context['total_reviews'] * 100) if context['total_reviews'] > 0 else 0
            rating_distribution.append({
                'stars': i,
                'count': count,
                'percentage': round(percentage)
            })
        context['rating_distribution'] = rating_distribution
        
        # Check if product is in wishlist
        if self.request.user.is_authenticated:
            context['in_wishlist'] = Wishlist.objects.filter(
                user=self.request.user,
                product=product
            ).exists()
            
            # Check if user has already reviewed
            context['user_reviewed'] = product.reviews.filter(
                user=self.request.user
            ).exists()
        
        # Get size guide if available
        try:
            context['size_guide'] = SizeGuide.objects.get(category=product.category)
        except SizeGuide.DoesNotExist:
            context['size_guide'] = None
        
        # Stock status
        if product.stock > 10:
            context['stock_status'] = 'in_stock'
            context['stock_message'] = 'In Stock'
        elif product.stock > 0:
            context['stock_status'] = 'low_stock'
            context['stock_message'] = f'Only {product.stock} left in stock'
        else:
            context['stock_status'] = 'out_of_stock'
            context['stock_message'] = 'Out of Stock'
        
        return post
    
    def post(self, request, *args, **kwargs):
        """Handle AJAX requests for quick add to cart"""
        product = self.get_object()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity > product.stock:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Only {product.stock} items available'
                })
            
            # Add to cart logic here
            return JsonResponse({
                'status': 'success',
                'message': f'{product.name} added to cart',
                'cart_count': Cart.get_cart_count(request) if Cart is not None else 0
            })
        
        return super().get(request, *args, **kwargs)


class ProductCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    """Create new product (Admin only)"""
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_message = "Product '%(name)s' created successfully!"
    
    def get_success_url(self):
        return reverse_lazy('product:detail', kwargs={'slug': self.object.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Product'
        context['button_text'] = 'Create Product'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Handle additional images
        images = self.request.FILES.getlist('additional_images')
        for index, image in enumerate(images):
            ProductImage.objects.create(
                product=self.object,
                image=image,
                order=index
            )
        
        return response


class ProductUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update existing product (Admin only)"""
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_message = "Product '%(name)s' updated successfully!"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Update Product: {self.object.name}'
        context['button_text'] = 'Update Product'
        context['product_images'] = self.object.additional_images.all()
        return context
    
    def get_success_url(self):
        return reverse_lazy('product:detail', kwargs={'slug': self.object.slug})


class ProductDeleteView(AdminRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete product (Admin only)"""
    model = Product
    template_name = 'product/product_confirm_delete.html'
    success_url = reverse_lazy('product:list')
    success_message = "Product deleted successfully!"
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


# ==================== CATEGORY VIEWS ====================

class CategoryListView(ListView):
    """List all categories"""
    model = Category
    template_name = 'product/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).order_by('name')


class CategoryDetailView(DetailView):
    """Display category details and products in that category"""
    model = Category
    template_name = 'product/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        
        # Get products in this category
        products = Product.objects.filter(
            category=category,
            is_active=True,
            status='active'
        ).select_related('brand')
        
        # Apply filters
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'price_low':
            products = products.order_by('price')
        elif sort == 'price_high':
            products = products.order_by('-price')
        else:
            products = products.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(products, 12)
        page_number = self.request.GET.get('page')
        context['products'] = paginator.get_page(page_number)
        
        # Get subcategories
        context['subcategories'] = Category.objects.filter(
            parent=category,
            is_active=True
        ).annotate(product_count=Count('products'))
        
        return context


class CategoryCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    """Create new category (Admin only)"""
    model = Category
    form_class = CategoryForm
    template_name = 'product/category_form.html'
    success_url = reverse_lazy('product:category_list')
    success_message = "Category '%(name)s' created successfully!"


class CategoryUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update category (Admin only)"""
    model = Category
    form_class = CategoryForm
    template_name = 'product/category_form.html'
    success_url = reverse_lazy('product:category_list')
    success_message = "Category '%(name)s' updated successfully!"


class CategoryDeleteView(AdminRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete category (Admin only)"""
    model = Category
    template_name = 'product/category_confirm_delete.html'
    success_url = reverse_lazy('product:category_list')
    success_message = "Category deleted successfully!"


# ==================== BRAND VIEWS ====================

class BrandListView(ListView):
    """List all brands"""
    model = Brand
    template_name = 'product/brand_list.html'
    context_object_name = 'brands'
    
    def get_queryset(self):
        return Brand.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).order_by('name')


class BrandDetailView(DetailView):
    """Display brand details and products"""
    model = Brand
    template_name = 'product/brand_detail.html'
    context_object_name = 'brand'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.get_object()
        
        # Get products by this brand
        products = Product.objects.filter(
            brand=brand,
            is_active=True,
            status='active'
        )
        
        # Pagination
        paginator = Paginator(products, 12)
        page_number = self.request.GET.get('page')
        context['products'] = paginator.get_page(page_number)
        
        return context


class BrandCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    """Create new brand (Admin only)"""
    model = Brand
    form_class = BrandForm
    template_name = 'product/brand_form.html'
    success_url = reverse_lazy('product:brand_list')
    success_message = "Brand '%(name)s' created successfully!"


class BrandUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update brand (Admin only)"""
    model = Brand
    form_class = BrandForm
    template_name = 'product/brand_form.html'
    success_url = reverse_lazy('product:brand_list')
    success_message = "Brand '%(name)s' updated successfully!"


class BrandDeleteView(AdminRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete brand (Admin only)"""
    model = Brand
    template_name = 'product/brand_confirm_delete.html'
    success_url = reverse_lazy('product:brand_list')
    success_message = "Brand deleted successfully!"


# ==================== REVIEW VIEWS ====================

class AddReviewView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Add product review"""
    model = Review
    form_class = ReviewForm
    template_name = 'product/review_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(
            Product, 
            slug=self.kwargs['slug'],
            is_active=True
        )
        
        # Check if user already reviewed
        if Review.objects.filter(product=self.product, user=request.user).exists():
            messages.error(request, "You have already reviewed this product.")
            return redirect('product:detail', slug=self.product.slug)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.product = self.product
        form.instance.user = self.request.user
        messages.success(self.request, "Your review has been submitted and is pending approval.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('product:detail', kwargs={'slug': self.product.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context


class ReviewUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update user's review"""
    model = Review
    form_class = ReviewForm
    template_name = 'product/review_form.html'
    pk_url_kwarg = 'pk'
    success_message = "Your review has been updated!"
    
    def dispatch(self, request, *args, **kwargs):
        review = self.get_object()
        if review.user != request.user and not request.user.is_admin:
            messages.error(request, "You don't have permission to edit this review.")
            return redirect('product:detail', slug=review.product.slug)
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('product:detail', kwargs={'slug': self.object.product.slug})


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    """Delete user's review"""
    model = Review
    template_name = 'product/review_confirm_delete.html'
    pk_url_kwarg = 'pk'
    
    def dispatch(self, request, *args, **kwargs):
        review = self.get_object()
        if review.user != request.user and not request.user.is_admin:
            messages.error(request, "You don't have permission to delete this review.")
            return redirect('product:detail', slug=review.product.slug)
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        messages.success(self.request, "Review deleted successfully!")
        return reverse_lazy('product:detail', kwargs={'slug': self.object.product.slug})


# ==================== WISHLIST VIEWS ====================

class AddToWishlistView(LoginRequiredMixin, View):
    """Add product to wishlist"""
    
    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            message = f"{product.name} added to wishlist!"
        else:
            message = f"{product.name} is already in your wishlist."
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': message,
                'in_wishlist': True
            })
        
        messages.success(request, message)
        return redirect('product:detail', slug=product.slug)


class RemoveFromWishlistView(LoginRequiredMixin, View):
    """Remove product from wishlist"""
    
    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        
        deleted = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).delete()
        
        if deleted[0] > 0:
            message = f"{product.name} removed from wishlist."
        else:
            message = "Product not found in wishlist."
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': message,
                'in_wishlist': False
            })
        
        messages.success(request, message)
        return redirect('product:detail', slug=product.slug)


# ==================== VARIANT VIEWS ====================

class ProductVariantCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    """Create product variant"""
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'product/variant_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=self.kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.product = self.product
        messages.success(self.request, "Variant created successfully!")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('product:update', kwargs={'slug': self.product.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context


class ProductVariantUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update product variant"""
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'product/variant_form.html'
    pk_url_kwarg = 'pk'
    success_message = "Variant updated successfully!"
    
    def get_success_url(self):
        return reverse_lazy('product:update', kwargs={'slug': self.object.product.slug})


class ProductVariantDeleteView(AdminRequiredMixin, DeleteView):
    """Delete product variant"""
    model = ProductVariant
    template_name = 'product/variant_confirm_delete.html'
    pk_url_kwarg = 'pk'
    
    def get_success_url(self):
        messages.success(self.request, "Variant deleted successfully!")
        return reverse_lazy('product:update', kwargs={'slug': self.object.product.slug})


# ==================== AJAX API VIEWS ====================

class ProductFilterAPIView(View):
    """AJAX endpoint for product filtering"""
    
    def get(self, request):
        products = Product.objects.filter(is_active=True, status='active')
        
        # Apply filters
        category_id = request.GET.get('category')
        if category_id:
            products = products.filter(category_id=category_id)
        
        brand_id = request.GET.get('brand')
        if brand_id:
            products = products.filter(brand_id=brand_id)
        
        min_price = request.GET.get('min_price')
        if min_price:
            products = products.filter(price__gte=min_price)
        
        max_price = request.GET.get('max_price')
        if max_price:
            products = products.filter(price__lte=max_price)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        paginator = Paginator(products, 12)
        products_page = paginator.get_page(page)
        
        # Prepare response data
        data = {
            'products': [
                {
                    'id': p.id,
                    'name': p.name,
                    'slug': p.slug,
                    'price': str(p.price),
                    'discount_price': str(p.discount_price) if p.discount_price else None,
                    'image': p.main_image.url if p.main_image else None,
                    'stock': p.stock,
                }
                for p in products_page
            ],
            'has_next': products_page.has_next(),
            'has_previous': products_page.has_previous(),
            'total_pages': paginator.num_pages,
            'current_page': page,
        }
        
        return JsonResponse(data)


class QuickProductView(View):
    """AJAX endpoint for quick product view modal"""
    
    def get(self, request, pk):
        product = get_object_or_404(
            Product, 
            id=pk, 
            is_active=True, 
            status='active'
        )
        
        data = {
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': str(product.current_price),
            'original_price': str(product.price) if product.discount_price else None,
            'description': product.short_description or product.description[:200],
            'image': product.main_image.url if product.main_image else None,
            'stock': product.stock,
            'in_stock': product.is_in_stock,
            'category': product.category.name,
            'brand': product.brand.name if product.brand else None,
            'rating': product.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg'],
            'review_count': product.reviews.filter(is_approved=True).count(),
        }
        
        return JsonResponse(data)


class ProductSearchAPIView(View):
    """AJAX endpoint for product search autocomplete"""
    
    def get(self, request):
        query = request.GET.get('q', '')
        
        if len(query) >= 2:
            products = Product.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(brand__name__icontains=query),
                is_active=True,
                status='active'
            )[:10]
            
            data = [
                {
                    'id': p.id,
                    'name': p.name,
                    'slug': p.slug,
                    'price': str(p.current_price),
                    'image': p.main_image.url if p.main_image else None,
                    'category': p.category.name,
                }
                for p in products
            ]
        else:
            data = []
        
        return JsonResponse({'results': data})
