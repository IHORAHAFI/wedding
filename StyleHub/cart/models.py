from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from product.models import Product

class Order(models.Model):
	STATUS_CHOICES = (
		('pending', _('Pending')),
		('processing', _('Processing')),
		('completed', _('Completed')),
		('cancelled', _('Cancelled')),
		('refunded', _('Refunded')),
	)

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)
	size = models.CharField(
		max_length=3,
		choices=Product.SIZE_CHOICES,
		blank=True,
		null=True,
		default=None,
	)
	customer_name = models.CharField(max_length=255, blank=True, null=True)
	customer_email = models.EmailField(blank=True, null=True)
	customer_phone = models.CharField(max_length=20, blank=True, null=True)
	shipping_address = models.TextField(blank=True, null=True)
	shipping_city = models.CharField(max_length=100, blank=True, null=True)
	shipping_postal_code = models.CharField(max_length=20, blank=True, null=True)
	payment_method = models.CharField(
		max_length=50,
		choices=(
			('mtn', _('MTN Mobile Money')),
			('bk', _('BK Mobile Money')),
			('credit_card', _('Credit/Debit Card')),
			('debit_card', _('Debit Card')),
			('cod', _('Cash on Delivery')),
			('bank_transfer', _('Bank Transfer')),
		),
		blank=True,
		null=True
	)
	payment_reference = models.CharField(max_length=255, blank=True, null=True)
	payment_verified = models.BooleanField(default=False)
	verified_at = models.DateTimeField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

	def __str__(self):
		size_info = f" ({self.get_size_display()})" if self.size else ''
		return f"Order #{self.id} by {self.user.username} - {self.product.name}{size_info}"

	@property
	def total_price(self):
		"""Total price for this order item."""
		return self.product.current_price * self.quantity
