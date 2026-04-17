from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0004_order_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_reference',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='order',
            name='verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
