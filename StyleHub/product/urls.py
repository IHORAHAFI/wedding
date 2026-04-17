from django.urls import path
from . import views

app_name = 'product'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('create/', views.ProductCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='detail'),
    path('<slug:slug>/update/', views.ProductUpdateView.as_view(), name='update'),
    path('<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='delete'),
    
    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/<slug:slug>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<slug:slug>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Brand URLs
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/create/', views.BrandCreateView.as_view(), name='brand_create'),
    path('brands/<slug:slug>/', views.BrandDetailView.as_view(), name='brand_detail'),
    path('brands/<slug:slug>/update/', views.BrandUpdateView.as_view(), name='brand_update'),
    path('brands/<slug:slug>/delete/', views.BrandDeleteView.as_view(), name='brand_delete'),
    
    # Review URLs
    path('<slug:slug>/review/add/', views.AddReviewView.as_view(), name='add_review'),
    path('review/<int:pk>/update/', views.ReviewUpdateView.as_view(), name='update_review'),
    path('review/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='delete_review'),
    
    # Product Variant URLs
    path('<slug:slug>/variants/add/', views.ProductVariantCreateView.as_view(), name='add_variant'),
    path('variants/<int:pk>/update/', views.ProductVariantUpdateView.as_view(), name='update_variant'),
    path('variants/<int:pk>/delete/', views.ProductVariantDeleteView.as_view(), name='delete_variant'),
    
    # AJAX endpoints
    path('api/filter/', views.ProductFilterAPIView.as_view(), name='api_filter'),
    path('api/quick-view/<int:pk>/', views.QuickProductView.as_view(), name='quick_view'),
]  # <-- Make sure this closing bracket exists!