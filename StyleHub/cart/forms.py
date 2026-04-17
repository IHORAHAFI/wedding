from django import forms

PAYMENT_METHOD_CHOICES = [
    ('mtn', 'MTN Mobile Money'),
    ('bk', 'BK Mobile Money'),
    ('credit_card', 'Credit Card'),
    ('debit_card', 'Debit Card'),
]

class CheckoutForm(forms.Form):
    # Shipping Information
    telephone = forms.CharField(
        max_length=20, 
        label='Telephone',
        widget=forms.TextInput(attrs={
            'placeholder': '+250...',
            'class': 'form-control'
        })
    )
    country = forms.CharField(
        max_length=100,
        label='Country',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Rwanda',
            'class': 'form-control'
        })
    )
    province = forms.CharField(
        max_length=100,
        label='Province/State',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Kigali',
            'class': 'form-control'
        })
    )
    district = forms.CharField(
        max_length=100,
        label='District',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Gasabo',
            'class': 'form-control'
        })
    )
    sector = forms.CharField(
        max_length=100,
        label='Sector',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Gisozi',
            'class': 'form-control'
        })
    )
    cell = forms.CharField(
        max_length=100,
        label='Cell',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Urugwiro',
            'class': 'form-control'
        })
    )
    street_address = forms.CharField(
        max_length=255,
        label='Street Address',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'House number / street name',
            'class': 'form-control'
        })
    )
    
    # Payment Method
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        label='Payment Method',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )


class PaymentVerificationForm(forms.Form):
    transaction_reference = forms.CharField(
        max_length=255,
        label='Transaction Reference',
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your payment reference or transaction ID',
            'class': 'form-control'
        })
    )
