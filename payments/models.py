from django.db import models
import json
from django.conf import settings
from ads.models import Ads
from django.utils import timezone

# Create your models here.

class MpesaPayment(models.Model):
    ad = models.ForeignKey(Ads, on_delete=models.CASCADE, related_name='mpesa_payments')
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True)
    checkout_request_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PROCESSING', 'Processing'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
            ('CANCELLED', 'Cancelled')
        ],
        default='PENDING'
    )
    # Replace JSONField with TextField
    _status_history = models.TextField(db_column='status_history', default='[]')
    callback_received = models.BooleanField(default=False)
    retry_count = models.PositiveIntegerField(default=0)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('MPESA', 'M-Pesa'),
            ('CARD', 'Card'),
            ('BANK', 'Bank Transfer')
        ],
        default='MPESA'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payment for Ad {self.ad.title} - {self.amount} KES"

    # Property to handle JSON serialization/deserialization
    @property
    def status_history(self):
        return json.loads(self._status_history)

    @status_history.setter
    def status_history(self, value):
        self._status_history = json.dumps(value)

    def update_status(self, new_status, reason=None):
        history = self.status_history
        history.append({
            'status': new_status,
            'timestamp': timezone.now().isoformat(),
            'reason': reason
        })
        self.status = new_status
        self.status_history = history
        self.save(update_fields=['status', '_status_history'])
