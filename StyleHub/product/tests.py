from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Product, Category, Brand, Review
from .forms import ProductForm, ReviewForm

User = get_user_model()

class ProductModelTest(TestCase):
    """Test Product Model"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name="Test Category",
            description="Test Description"
        )
        self.brand = Brand.objects.create(
            name="Test Brand",
            description="Test Brand Description"
        )
        self.product = Product.objects.create(
            name="Test Product",
            category=self.category,
            brand=self.brand,
            price=100.00,
            description="Test Description",
            stock=10,
            size='M',
            gender='U'
        )
    
    def test_product_creation(self):
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.current_price, 100.00)
        self.assertTrue(self.product.is_in_stock)
    
    def test_product_slug_generation(self):
        self.assertEqual(self.product.slug, "test-product")
    
    def test_product_stock_reduction(self):
        self.product.reduce_stock(5)
        self.assertEqual(self.product.stock, 5)


class ProductViewTest(TestCase):
    """Test Product Views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            password='admin123',
            role='admin'
        )
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(
            name="Test Product",
            category=self.category,
            price=100.00,
            description="Test Description",
            stock=10,
            status='active',
            is_active=True
        )
    
    def test_product_list_view(self):
        response = self.client.get(reverse('product:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product/product_list.html')
    
    def test_product_detail_view(self):
        response = self.client.get(
            reverse('product:detail', kwargs={'slug': self.product.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
    
    def test_product_create_view_admin(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('product:create'))
        self.assertEqual(response.status_code, 200)
    
    def test_product_create_view_non_admin(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('product:create'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_add_review(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('product:add_review', kwargs={'slug': self.product.slug}),
            {
                'title': 'Great Product',
                'content': 'Really liked it',
                'rating': 5
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Review.objects.count(), 1)
