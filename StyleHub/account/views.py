from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from product.models import Product, Category, Wishlist
from cart.models import Order
from django.views.generic import (
    CreateView, TemplateView, UpdateView, 
    DetailView, ListView, FormView, View
)
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import JsonResponse
from .models import User
from .forms import (
    UserRegistrationForm, ProfileUpdateForm,
    CustomUserChangeForm, AdminUserCreationForm
)

class HomeView(TemplateView):
    """Home page view"""
    template_name = 'account/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(is_active=True)[:8]
        context['categories'] = Category.objects.all()
        return context

class UserRegistrationView(SuccessMessageMixin, CreateView):
    """User registration view"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'account/register.html'
    success_url = reverse_lazy('account:login')
    success_message = "Registration successful! You can now login."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response

class UserLoginView(SuccessMessageMixin, LoginView):
    """User login view"""
    template_name = 'account/login.html'
    success_message = "Welcome back, %(username)s!"
    next_page = reverse_lazy('product:list')
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        elif self.request.user.role == 'admin':
            return reverse_lazy('admin_panel:dashboard')
        else:
            return reverse_lazy('account:profile')

class UserLogoutView(LogoutView):
    """User logout view"""
    next_page = reverse_lazy('product:list')
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)

class ProfileView(LoginRequiredMixin, DetailView):
    """View user profile"""
    model = User
    template_name = 'account/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_orders'] = Order.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:5]
        return context

class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update user profile"""
    model = User
    form_class = ProfileUpdateForm
    template_name = 'account/profile_update.html'
    success_message = "Profile updated successfully!"
    
    def get_object(self):
        return self.request.user
    
    def get_success_url(self):
        return reverse_lazy('account:profile')

class UserDashboardView(LoginRequiredMixin, TemplateView):
    """User dashboard"""
    template_name = 'account/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_admin:
            context['total_users'] = User.objects.count()
            context['total_products'] = Product.objects.count()
            context['total_orders'] = Order.objects.count()
            context['recent_orders'] = Order.objects.all()[:10]
        else:
            context['orders'] = Order.objects.filter(user=user)
            context['wishlist'] = Wishlist.objects.filter(user=user)
        
        return context

class ContactView(TemplateView):
    """Contact page for account app."""
    template_name = 'account/contact.html'

class AboutUsView(TemplateView):
    """About us page."""
    template_name = 'account/aboutus.html'

class FAQView(TemplateView):
    """FAQ page."""
    template_name = 'account/faq.html'

class ShippingPolicyView(TemplateView):
    """Shipping policy page."""
    template_name = 'account/shipping_policy.html'

class ReturnsExchangeView(TemplateView):
    """Returns & exchanges page."""
    template_name = 'account/returns_exchanges.html'

class TermsOfServiceView(TemplateView):
    """Terms of Service page."""
    template_name = 'account/terms_of_service.html'

class PasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    """Change password view"""
    template_name = 'account/password_change.html'
    success_message = "Password changed successfully!"
    success_url = reverse_lazy('account:profile')

class PasswordResetRequestView(PasswordResetView):
    """Password reset request"""
    template_name = 'account/password_reset.html'
    email_template_name = 'account/password_reset_email.html'
    subject_template_name = 'account/password_reset_subject.txt'
    success_url = reverse_lazy('account:password_reset_done')

class PasswordResetDoneView(PasswordResetDoneView):
    """Password reset done"""
    template_name = 'account/password_reset_done.html'

class PasswordResetConfirmView(PasswordResetConfirmView):
    """Password reset confirm"""
    template_name = 'account/password_reset_confirm.html'
    success_url = reverse_lazy('account:password_reset_complete')

class PasswordResetCompleteView(PasswordResetCompleteView):
    """Password reset complete"""
    template_name = 'account/password_reset_complete.html'
