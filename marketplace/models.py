from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from products.models import Product


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=120)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    unread = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} -> {self.recipient.username}"


class Conversation(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buyer_conversations")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seller_conversations")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("buyer", "seller", "product")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.buyer.username} <-> {self.seller.username}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Agreement(models.Model):
    TYPE_PURCHASE = "purchase"
    TYPE_BOOKING = "booking"
    AGREEMENT_TYPES = [
        (TYPE_PURCHASE, "Purchase"),
        (TYPE_BOOKING, "Booking"),
    ]

    STATUS_PENDING = "pending_buyer_confirmation"
    STATUS_AWAITING_PAYMENT = "awaiting_payment"
    STATUS_IN_ESCROW = "in_escrow"
    STATUS_RESERVED = "reserved"
    STATUS_REJECTED = "rejected"
    STATUS_EXPIRED = "expired"
    STATUS_COMPLETED = "completed"
    STATUS_DISPUTED = "disputed"
    STATUS_CANCELLED = "cancelled"
    STATUSES = [
        (STATUS_PENDING, "Pending Buyer Confirmation"),
        (STATUS_AWAITING_PAYMENT, "Awaiting Payment"),
        (STATUS_IN_ESCROW, "In Escrow"),
        (STATUS_RESERVED, "Reserved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_DISPUTED, "Disputed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="agreements")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="agreements")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buyer_agreements")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seller_agreements")
    agreement_type = models.CharField(max_length=20, choices=AGREEMENT_TYPES)
    status = models.CharField(max_length=40, choices=STATUSES, default=STATUS_PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    meetup_location = models.CharField(max_length=255)
    meetup_at = models.DateTimeField()
    payment_deadline = models.DateTimeField()
    buyer_confirmed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.agreement_type == self.TYPE_BOOKING and not self.deposit_amount:
            self.deposit_amount = (self.amount * Decimal("0.25")).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)


class Payment(models.Model):
    STATUS_HELD = "held"
    STATUS_RELEASED = "released"
    STATUS_REFUNDED = "refunded"
    STATUS_FROZEN = "frozen"
    STATUSES = [
        (STATUS_HELD, "Held in escrow"),
        (STATUS_RELEASED, "Released"),
        (STATUS_REFUNDED, "Refunded"),
        (STATUS_FROZEN, "Frozen"),
    ]

    agreement = models.ForeignKey(Agreement, on_delete=models.CASCADE, related_name="payments")
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments_made")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=40, default="mpesa")
    phone = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default=STATUS_HELD)
    reference = models.CharField(max_length=80, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class Dispute(models.Model):
    STATUS_OPEN = "open"
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_REFUNDED = "refunded"
    STATUS_RELEASED = "released_to_seller"
    STATUS_CLOSED = "closed"
    STATUSES = [
        (STATUS_OPEN, "Open"),
        (STATUS_UNDER_REVIEW, "Under Review"),
        (STATUS_REFUNDED, "Refunded"),
        (STATUS_RELEASED, "Released to Seller"),
        (STATUS_CLOSED, "Closed"),
    ]

    agreement = models.OneToOneField(Agreement, on_delete=models.CASCADE, related_name="dispute")
    opened_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="opened_disputes")
    reason = models.TextField()
    evidence = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUSES, default=STATUS_OPEN)
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


def notify(recipient, title, message, link=""):
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        link=link,
    )


def expire_overdue_agreements():
    overdue = Agreement.objects.filter(
        status__in=[Agreement.STATUS_PENDING, Agreement.STATUS_AWAITING_PAYMENT],
        payment_deadline__lt=timezone.now(),
    )
    for agreement in overdue:
        agreement.status = Agreement.STATUS_EXPIRED
        agreement.save(update_fields=["status", "updated_at"])
        product = agreement.product
        product.status = Product.STATUS_AVAILABLE
        product.save(update_fields=["status"])
        notify(agreement.buyer, "Agreement expired", f"{product.name} is available again.")
        notify(agreement.seller, "Agreement expired", f"{product.name} returned to available.")
