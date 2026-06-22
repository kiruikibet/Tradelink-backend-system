from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Agreement, Conversation, Dispute, Message, Notification, Payment


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source="sender.username")

    class Meta:
        model = Message
        fields = ["id", "sender", "body", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    buyer = serializers.ReadOnlyField(source="buyer.username")
    seller = serializers.ReadOnlyField(source="seller.username")
    product_id = serializers.ReadOnlyField(source="product.product_id")
    product_name = serializers.ReadOnlyField(source="product.name")
    last_message = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "buyer",
            "seller",
            "product_id",
            "product_name",
            "last_message",
            "messages",
            "updated_at",
        ]

    def get_last_message(self, obj):
        message = obj.messages.order_by("-created_at").first()
        return message.body if message else ""


class AgreementSerializer(serializers.ModelSerializer):
    buyer = serializers.ReadOnlyField(source="buyer.username")
    seller = serializers.ReadOnlyField(source="seller.username")
    product_name = serializers.ReadOnlyField(source="product.name")
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = Agreement
        fields = [
            "id",
            "conversation",
            "product",
            "product_name",
            "product_image",
            "buyer",
            "seller",
            "agreement_type",
            "status",
            "amount",
            "deposit_amount",
            "meetup_location",
            "meetup_at",
            "payment_deadline",
            "buyer_confirmed_at",
            "paid_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = ["status", "deposit_amount", "buyer_confirmed_at", "paid_at", "completed_at"]

    def get_product_image(self, obj):
        image = obj.product.images.first()
        return image.image if image else ""


class PaymentSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="agreement.product.name")
    payer = serializers.ReadOnlyField(source="payer.username")

    class Meta:
        model = Payment
        fields = ["id", "agreement", "product_name", "payer", "amount", "method", "phone", "status", "reference", "created_at", "released_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "link", "unread", "created_at"]


class DisputeSerializer(serializers.ModelSerializer):
    opened_by = serializers.ReadOnlyField(source="opened_by.username")
    product_name = serializers.ReadOnlyField(source="agreement.product.name")

    class Meta:
        model = Dispute
        fields = ["id", "agreement", "product_name", "opened_by", "reason", "evidence", "status", "resolution", "created_at", "resolved_at"]
        read_only_fields = ["status", "resolution", "resolved_at"]
