from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'account'

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('dashboard/', views.UserDashboardView.as_view(), name='dashboard'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('about-us/', views.AboutUsView.as_view(), name='about_us'),
    path('about_us/', views.AboutUsView.as_view()),
    path('faq/', views.FAQView.as_view(), name='faq'),
    path('shipping-policy/', views.ShippingPolicyView.as_view(), name='shipping_policy'),
    path('returns-exchanges/', views.ReturnsExchangeView.as_view(), name='returns_exchanges'),
    path('terms-of-service/', views.TermsOfServiceView.as_view(), name='terms_of_service'),
    path('password-change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]