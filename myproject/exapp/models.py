from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Totalsolutions(models.Model):
    CATEGORY_CHOICES = [
        ('hardware', 'Hardware'),
        ('software', 'Software'),
        ('service', 'Service'),
        ('all', 'All Categories')
    ]

    application = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='all')
    product_name = models.CharField(max_length=255)
    make = models.CharField(max_length=255, blank=True, null=True)
    model = models.CharField(max_length=255, blank=True, null=True)
    specification = models.TextField(max_length=250, blank=True, null=True)
    uom = models.CharField(max_length=300)  # Unit of Measurement
    buying_price = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Buying price must be non-negative."
    )
    vendor = models.CharField(max_length=255, blank=True, null=True)
    quotation_received_month = models.CharField(max_length=50, blank=True, null=True)
    lead_time = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(max_length=255, blank=True, null=True)
    list_price = models.DecimalField(
        max_digits=10, decimal_places=2, 
        default=0.0, validators=[MinValueValidator(0)],
        help_text="List price must be non-negative."
    )
    discount = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount as a percentage (0 to 100)."
    )
    sales_price = models.DecimalField(
        max_digits=10, decimal_places=2, 
        default=0.0, validators=[MinValueValidator(0)],
        help_text="Sales price must be non-negative."
    )
    sales_margin = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=0.0, validators=[MinValueValidator(0)],
        help_text="Sales margin must be non-negative."
    )

    def save(self, *args, **kwargs):
        """
        Override save method to ensure sales_price and sales_margin are calculated 
        automatically based on list_price, discount, and buying_price.
        """
        try:
            # Convert list_price and discount to float for calculation
            list_price = float(self.list_price) if self.list_price else 0.0
            discount = float(self.discount) if self.discount else 0.0
            buying_price = float(self.buying_price) if self.buying_price else 0.0

            # Calculate the sales_price based on discount
            discount_decimal = discount / 100  # Convert percentage to decimal
            self.sales_price = max(list_price - (list_price * discount_decimal), 0.0)

            # Calculate the sales_margin
            if self.sales_price > 0:
                self.sales_margin = max((self.sales_price - buying_price) / self.sales_price, 0.0)
            else:
                self.sales_margin = 0.0  # Avoid division by zero

        except ValueError as e:
            raise ValueError(f"Invalid data provided for numeric fields: {e}")

        # Call the parent save method
        super().save(*args, **kwargs)

    def __str__(self):
        return self.product_name