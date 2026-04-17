from io import BytesIO

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from urllib.parse import urlencode
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from .forms import CheckoutForm, PaymentVerificationForm
from .models import Order
from product.models import Product, Wishlist


@login_required
def cart_detail(request):
	"""Display user's cart/orders"""
	orders = Order.objects.filter(
		user=request.user,
		status='pending'
	).select_related('product')

	total_amount = sum(order.total_price for order in orders)

	context = {
		'orders': orders,
		'total_amount': total_amount,
		'order_count': orders.count(),
	}

	return render(request, 'cart/detail.html', context)


@login_required
def wishlist_view(request):
	"""Display user wishlist items."""
	wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
	
	context = {
		'wishlist_items': wishlist_items,
		'wishlist_count': wishlist_items.count(),
	}
	
	return render(request, 'cart/wishlist.html', context)


@login_required
def order_history(request):
	"""Display user's order history"""
	orders = Order.objects.filter(
		user=request.user
	).select_related('product').order_by('-created_at')

	total_amount = sum(order.total_price for order in orders)

	context = {
		'orders': orders,
		'total_amount': total_amount,
	}

	return render(request, 'cart/order_history.html', context)


@login_required
def add_to_cart(request, product_id):
	if request.method != 'POST':
		return HttpResponseNotAllowed(['POST'])

	try:
		product = get_object_or_404(Product, id=product_id, is_active=True, status='active')

		# Get product options from POST data
		quantity = int(request.POST.get('quantity', 1))
		size = request.POST.get('size') or product.size

		# Validate quantity
		if quantity < 1:
			quantity = 1
		if quantity > product.stock:
			quantity = product.stock

		# Check if user already has an order for this product+size
		existing_order = Order.objects.filter(
			user=request.user,
			product=product,
			size=size,
			status='pending'
		).first()

		if existing_order:
			# Update existing order quantity
			existing_order.quantity += quantity
			existing_order.save()
			message = f"Updated quantity for {product.name} ({size}) in your cart"
		else:
			# Create new order
			Order.objects.create(
				user=request.user,
				product=product,
				quantity=quantity,
				size=size,
				status='pending'
			)
			message = f"Added {product.name} ({size}) to your cart"

		# Get cart count
		cart_count = Order.objects.filter(
			user=request.user,
			status='pending'
		).count()

		return JsonResponse({
			'status': 'success',
			'message': message,
			'cart_count': cart_count
		})

	except Exception as e:
		return JsonResponse({
			'status': 'error',
			'message': 'Failed to add product to cart'
		}, status=500)


@login_required
def add_to_wishlist(request, product_id):
	if request.method != 'POST':
		return HttpResponseNotAllowed(['POST'])

	try:
		product = get_object_or_404(Product, id=product_id, is_active=True, status='active')

		wishlist_item, created = Wishlist.objects.get_or_create(
			user=request.user,
			product=product
		)

		if created:
			message = f"{product.name} added to wishlist"
		else:
			message = f"{product.name} is already in your wishlist"

		return JsonResponse({
			'status': 'success',
			'message': message,
			'in_wishlist': True
		})

	except Exception as e:
		return JsonResponse({
			'status': 'error',
			'message': 'Failed to add product to wishlist'
		}, status=500)


@login_required
def toggle_wishlist(request, product_id):
	if request.method != 'POST':
		return HttpResponseNotAllowed(['POST'])

	try:
		product = get_object_or_404(Product, id=product_id, is_active=True, status='active')
		wish_item = Wishlist.objects.filter(user=request.user, product=product)

		if wish_item.exists():
			wish_item.delete()
			return JsonResponse({
				'status': 'success',
				'message': f'{product.name} removed from wishlist',
				'in_wishlist': False
			})

		Wishlist.objects.create(user=request.user, product=product)
		return JsonResponse({
			'status': 'success',
			'message': f'{product.name} added to wishlist',
			'in_wishlist': True
		})

	except Exception as e:
		return JsonResponse({
			'status': 'error',
			'message': 'Failed to toggle wishlist item'
		}, status=500)


@login_required
def update_order_quantity(request, order_id):
	if request.method != 'POST':
		return HttpResponseNotAllowed(['POST'])

	try:
		order = get_object_or_404(Order, id=order_id, user=request.user, status='pending')
		quantity = int(request.POST.get('quantity', 1))

		# Validate quantity
		if quantity < 1:
			quantity = 1
		if quantity > order.product.stock:
			quantity = order.product.stock

		order.quantity = quantity
		order.save()

		return JsonResponse({
			'status': 'success',
			'message': 'Quantity updated successfully'
		})

	except Exception as e:
		return JsonResponse({
			'status': 'error',
			'message': 'Failed to update quantity'
		}, status=500)


@login_required
def remove_order(request, order_id):
	if request.method != 'POST':
		return HttpResponseNotAllowed(['POST'])

	try:
		order = get_object_or_404(Order, id=order_id, user=request.user, status='pending')
		order.delete()

		return JsonResponse({
			'status': 'success',
			'message': 'Item removed from cart'
		})

	except Exception as e:
		return JsonResponse({
			'status': 'error',
			'message': 'Failed to remove item'
		}, status=500)


@login_required
def checkout(request):
	"""Process checkout for pending orders"""
	orders_qs = Order.objects.filter(user=request.user, status='pending')

	if not orders_qs.exists():
		messages.error(request, 'No items in cart. Please add items before checkout.')
		return redirect('cart:detail')

	orders = list(orders_qs)
	user_info = {
		'full_name': request.user.get_full_name() or request.user.username,
		'email': request.user.email,
		'username': request.user.username,
		'phone': getattr(request.user.userprofile, 'phone', 'N/A') if hasattr(request.user, 'userprofile') else 'N/A',
	}

	if request.method == 'GET':
		form = CheckoutForm(initial={
			'payment_method': 'mtn'
		})
		return render(request, 'cart/checkout.html', {
			'orders': orders,
			'total_amount': sum(order.total_price for order in orders),
			'order_count': len(orders),
			'form': form,
			'selected_payment_method': form['payment_method'].value(),
			'user_info': user_info,
		})

	if request.method == 'POST':
		form = CheckoutForm(request.POST)
		if not form.is_valid():
			return render(request, 'cart/checkout.html', {
				'orders': orders,
				'total_amount': sum(order.total_price for order in orders),
				'order_count': len(orders),
				'form': form,
				'selected_payment_method': form.data.get('payment_method', 'N/A'),
				'user_info': user_info,
			})

		# Minimum order amount validation (can adjust as needed):
		total_amount = sum(order.total_price for order in orders)
		MIN_ORDER_AMOUNT = 5  # currency units, set your own business value
		if total_amount < MIN_ORDER_AMOUNT:
			messages.error(request, f'Minimum order amount is ${MIN_ORDER_AMOUNT}. Please add more items.')
			return render(request, 'cart/checkout.html', {
				'orders': orders,
				'total_amount': total_amount,
				'order_count': len(orders),
				'form': form,
				'selected_payment_method': form['payment_method'].value(),
				'user_info': user_info,
			})

		data = form.cleaned_data
		receipt_code = f"SH-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
		order_ids = [order.id for order in orders]

		# Generate unique payment reference for this order batch
		payment_reference = str(uuid.uuid4())

		orders_qs.update(
			status='processing',
			payment_method=data['payment_method'],
			payment_verified=False,
			payment_reference=payment_reference,
			verified_at=None,
			customer_phone=data['telephone'],
			shipping_address=f"{data.get('street_address', '')}, {data.get('cell', '')}, {data.get('sector', '')}",
			shipping_city=f"{data.get('district', '')}, {data.get('province', '')}, {data.get('country', '')}"
		)

		confirmed_orders = list(Order.objects.filter(id__in=order_ids).select_related('product'))
		receipt_ids = ','.join(str(pk) for pk in order_ids)
		receipt_url = reverse('cart:payment_receipt') + '?' + urlencode({'ids': receipt_ids, 'code': receipt_code})
		receipt_pdf_url = receipt_url + '&format=pdf'
		verify_url = reverse('cart:payment_verify') + '?' + urlencode({'ids': receipt_ids})

		submitted_info = {
			**user_info,
			'telephone': data['telephone'],
			'country': data['country'],
			'province': data['province'],
			'district': data['district'],
			'sector': data['sector'],
			'cell': data['cell'],
			'street_address': data['street_address'],
			'payment_method': data['payment_method'],
		}

		return render(request, 'cart/checkout.html', {
			'success': True,
			'success_message': f"Order placed successfully! Thank you, {user_info['full_name']}",
			'orders': orders,
			'confirmed_orders': confirmed_orders,
			'total_amount': total_amount,
			'order_count': len(orders),
			'form': CheckoutForm(initial={ 'payment_method': data['payment_method'] }),
			'selected_payment_method': data['payment_method'],
			'user_info': user_info,
			'submitted_info': submitted_info,
			'receipt_code': receipt_code,
			'receipt_url': receipt_url,
			'receipt_pdf_url': receipt_pdf_url,
			'receipt_ids': receipt_ids,
			'verify_url': verify_url,
			'payment_reference': payment_reference,
		})

	return HttpResponseNotAllowed(['GET', 'POST'])


def _build_pdf_receipt(orders, receipt_code, receipt_url, user_info, payment_method, total_amount, payment_reference=None):
	buffer = BytesIO()
	page = canvas.Canvas(buffer, pagesize=letter)
	width, height = letter
	margin = 50

	def draw_header():
		page.setFont('Helvetica-Bold', 18)
		page.drawString(margin, height - margin, 'StyleHub')
		page.setFont('Helvetica', 10)
		page.drawString(margin, height - margin - 18, 'Wedding fashion, accessories, and custom styling')
		page.drawString(margin, height - margin - 32, 'Email: support@stylehub.com | Phone: +250 788 000 000')
		page.line(margin, height - margin - 40, width - margin, height - margin - 40)

	def draw_footer(page_num):
		footer_y = margin - 20
		page.setFont('Helvetica-Oblique', 8)
		page.drawString(margin, footer_y, 'Thank you for choosing StyleHub. Your satisfaction is our priority.')
		page.drawRightString(width - margin, footer_y, f'Page {page_num}')

	page_num = 1
	draw_header()
	page.setFont('Helvetica', 9)
	page.drawString(margin, height - margin - 60, f'Receipt No: {receipt_code}')
	page.drawString(margin, height - margin - 75, f'Date: {timezone.now().strftime("%Y-%m-%d %H:%M")}')
	page.drawString(margin, height - margin - 90, f'Customer: {user_info.get("full_name", "")}')
	page.drawString(margin, height - margin - 105, f'Email: {user_info.get("email", "")}')
	page.drawString(margin, height - margin - 120, f'Phone: {user_info.get("phone", "")}')
	page.drawString(margin, height - margin - 135, f'Payment Method: {payment_method.upper() if payment_method else "N/A"}')
	if payment_reference:
		page.drawString(margin, height - margin - 150, f'Payment Reference: {payment_reference}')
		page.drawString(margin, height - margin - 165, f'Total Amount: FRw {total_amount}')
	else:
		page.drawString(margin, height - margin - 150, f'Total Amount: FRw {total_amount}')

	qr_size = 110
	qr = QrCodeWidget(receipt_url)
	bounds = qr.getBounds()
	qr_width = bounds[2] - bounds[0]
	qr_height = bounds[3] - bounds[1]
	drawing = Drawing(qr_size, qr_size, transform=[qr_size/qr_width,0,0,qr_size/qr_height,0,0])
	drawing.add(qr)
	drawing.drawOn(page, width - margin - qr_size, height - margin - qr_size)

	page.setFont('Helvetica-Bold', 11)
	if payment_reference:
		page.drawString(margin, height - margin - 190, 'Purchased Items')
		line_y = height - margin - 210
	else:
		page.drawString(margin, height - margin - 175, 'Purchased Items')
		line_y = height - margin - 195
	page.setFont('Helvetica-Bold', 10)
	page.drawString(margin, line_y, 'Product')
	page.drawString(width - 200, line_y, 'Qty')
	page.drawString(width - 100, line_y, 'Line Total')
	line_y -= 12
	page.line(margin, line_y, width - margin, line_y)
	line_y -= 18
	page.setFont('Helvetica', 10)

	for order in orders:
		if line_y < margin + 60:
			draw_footer(page_num)
			page.showPage()
			page_num += 1
			draw_header()
			page.setFont('Helvetica', 10)
			line_y = height - margin - 195
		page.drawString(margin, line_y, order.product.name)
		page.drawString(width - 200, line_y, str(order.quantity))
		page.drawRightString(width - margin, line_y, f'FRw {order.total_price}')
		line_y -= 18

	if line_y < margin + 100:
		draw_footer(page_num)
		page.showPage()
		page_num += 1
		draw_header()
		page.setFont('Helvetica', 10)
		if payment_reference:
			line_y = height - margin - 210
		else:
			line_y = height - margin - 195

	page.setFont('Helvetica-Bold', 12)
	page.drawString(margin, margin + 40, f'Order Total: FRw {total_amount}')
	draw_footer(page_num)
	page.save()

	buffer.seek(0)
	return buffer.getvalue()


@login_required
def payment_receipt(request):
	ids = request.GET.get('ids', '')
	if not ids:
		messages.error(request, 'Proof of payment not available. Please return to your orders.')
		return redirect('cart:order_history')

	order_ids = [int(pk) for pk in ids.split(',') if pk.isdigit()]
	if not order_ids:
		messages.error(request, 'Invalid receipt identifiers. Please try again.')
		return redirect('cart:order_history')

	orders = Order.objects.filter(id__in=order_ids, user=request.user, status='completed').select_related('product')
	if not orders.exists():
		messages.error(request, 'Receipt not found for this order. Please contact support.')
		return redirect('cart:order_history')

	total_amount = sum(order.total_price for order in orders)
	receipt_code = request.GET.get('code', f"SH-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}")
	format_type = request.GET.get('format')
	if format_type == 'pdf':
		pdf_content = _build_pdf_receipt(
			orders,
			receipt_code,
			request.build_absolute_uri().replace('&format=pdf', ''),
			{
				'full_name': request.user.get_full_name() or request.user.username,
				'email': request.user.email,
				'phone': orders.first().customer_phone or (getattr(request.user, 'userprofile', None) and getattr(request.user.userprofile, 'phone', 'N/A')) or 'N/A',
			},
			orders.first().payment_method,
			total_amount,
			orders.first().payment_reference,
		)
		response = HttpResponse(pdf_content, content_type='application/pdf')
		response['Content-Disposition'] = f'attachment; filename="stylehub-receipt-{receipt_code}.pdf"'
		return response

	context = {
		'orders': orders,
		'total_amount': total_amount,
		'order_count': orders.count(),
		'receipt_code': receipt_code,
		'receipt_ids': ids,
		'receipt_pdf_url': request.build_absolute_uri() + '&format=pdf' if 'format=pdf' not in request.get_full_path() else request.build_absolute_uri(),
		'verify_url': reverse('cart:payment_verify') + '?' + urlencode({'ids': ids}),
		'payment_method': orders.first().payment_method,
		'payment_reference': orders.first().payment_reference,
		'user_info': {
			'full_name': request.user.get_full_name() or request.user.username,
			'email': request.user.email,
			'username': request.user.username,
			'phone': orders.first().customer_phone or (getattr(request.user, 'userprofile', None) and getattr(request.user.userprofile, 'phone', 'N/A')) or 'N/A',
		},
	}

	return render(request, 'cart/receipt.html', context)


@login_required
def payment_verify(request):
	ids = request.GET.get('ids', '')
	if not ids:
		messages.error(request, 'No orders selected for payment verification.')
		return redirect('cart:order_history')

	order_ids = [int(pk) for pk in ids.split(',') if pk.isdigit()]
	if not order_ids:
		messages.error(request, 'Invalid order identifiers.')
		return redirect('cart:order_history')

	orders = Order.objects.filter(id__in=order_ids, user=request.user, status='processing')
	if not orders.exists():
		messages.error(request, 'Payment verification is not available for these orders.')
		return redirect('cart:order_history')

	if request.method == 'POST':
		form = PaymentVerificationForm(request.POST)
		if form.is_valid():
			transaction_reference = form.cleaned_data['transaction_reference']
			orders.update(
				status='completed',
				payment_verified=True,
				payment_reference=transaction_reference,
				verified_at=timezone.now(),
			)
			
			# Generate receipt URLs for success page
			receipt_code = f"SH-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
			receipt_url = reverse('cart:payment_receipt') + '?' + urlencode({'ids': ids, 'code': receipt_code})
			receipt_pdf_url = receipt_url + '&format=pdf'
			
			messages.success(request, 'Payment verified successfully. Your order is now complete.')
			
			return render(request, 'cart/payment_verification.html', {
				'success': True,
				'success_message': 'Payment verified successfully! Your order is now complete.',
				'orders': orders,
				'receipt_url': receipt_url,
				'receipt_pdf_url': receipt_pdf_url,
				'receipt_ids': ids,
			})
	else:
		form = PaymentVerificationForm()

	return render(request, 'cart/payment_verification.html', {
		'orders': orders,
		'form': form,
		'receipt_ids': ids,
	})


@login_required
def cart_count_api(request):
	"""API to get current cart item count"""
	count = Order.objects.filter(user=request.user, status='pending').count()
	return JsonResponse({'count': count})

