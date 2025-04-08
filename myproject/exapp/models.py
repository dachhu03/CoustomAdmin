from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


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
    product_image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    make = models.CharField(max_length=255, blank=True, null=True)
    model = models.CharField(max_length=255, blank=True, null=True)
    specification = models.TextField(max_length=250, blank=True, null=True)
    uom = models.CharField(max_length=300)  # Unit of Measurement
    buying_price = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="Buying price must be non-negative."
    )
    vendor = models.CharField(max_length=255, blank=True, null=True)
    quotation_received_month = models.CharField(max_length=50, blank=True, null=True)
    lead_time = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(max_length=255, blank=True, null=True)
    list_price = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="List price must be non-negative."
    )
    discount = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount as a percentage (0 to 100)."
    )
    sales_price = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="Sales price must be non-negative."
    )
    sales_margin = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Sales margin as a percentage (non-negative)."
    )
    buying_price_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the last direct update to buying_price."
    )

    def save(self, *args, **kwargs):
        """
        Override save method to:
        1. Calculate sales_price and sales_margin automatically.
        2. Update buying_price_updated_at only if buying_price changes directly.
        """
        try:
            # Check if this is an update (instance already exists)
            if self.pk is not None:
                old_instance = Totalsolutions.objects.get(pk=self.pk)
                if old_instance.buying_price != self.buying_price:
                    self.buying_price_updated_at = timezone.now()
            else:
                # For new instances, set buying_price_updated_at if buying_price is non-zero
                if self.buying_price != 0.0:
                    self.buying_price_updated_at = timezone.now()

            # Use float values for calculations
            list_price = float(self.list_price if self.list_price is not None else 0.0)
            discount = float(self.discount if self.discount is not None else 0)
            buying_price = float(self.buying_price if self.buying_price is not None else 0.0)

            # Calculate sales_price
            self.sales_price = max(list_price - (list_price * discount / 100), 0.0)

            # Calculate sales_margin
            if self.sales_price > 0:
                self.sales_margin = int((self.sales_price - buying_price) / self.sales_price * 100)
            else:
                self.sales_margin = 0

        except Totalsolutions.DoesNotExist:
            if self.buying_price != 0.0:
                self.buying_price_updated_at = timezone.now()
        except Exception as e:
            raise ValueError(f"Invalid data provided for numeric fields: {e}")

        super().save(*args, **kwargs)

    @property
    def buying_price_color(self):
        """Return the color based on buying_price_updated_at."""
        if not self.buying_price_updated_at:
            return 'red'
        days_diff = (timezone.now() - self.buying_price_updated_at).days
        if days_diff <= 30:
            return 'green'
        elif days_diff <= 90:
            return 'orange'
        else:
            return 'red'

    def __str__(self):
        return self.product_name
    



    # SI Project model with a ForeignKey to Totalsolutions
class SIProject(models.Model):
    project_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField()  # Duration in days
    si_name = models.CharField(max_length=255)
    product = models.ForeignKey(Totalsolutions, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_name

# Direct Project model with a ForeignKey to Totalsolutions
class DirectProject(models.Model):
    project_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField()  # Duration in days
    product = models.ForeignKey(Totalsolutions, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_name