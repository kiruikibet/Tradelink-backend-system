from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User_Profile
from products.models import Product
from .models import Agreement, Conversation, Dispute, Message, Notification, Payment, expire_overdue_agreements, notify
from .serializers import AgreementSerializer, ConversationSerializer, DisputeSerializer, NotificationSerializer, PaymentSerializer


def _participant_filter(user):
    return Conversation.objects.filter(buyer=user) | Conversation.objects.filter(seller=user)


def _get_user_conversation(user, conversation_id):
    return get_object_or_404(_participant_filter(user), id=conversation_id)


def _get_user_agreement(user, agreement_id):
    return get_object_or_404(
        Agreement.objects.filter(buyer=user) | Agreement.objects.filter(seller=user),
        id=agreement_id,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_verification(request):
    profile, _ = User_Profile.objects.get_or_create(user=request.user)
    government_id = request.data.get("government_id", "").strip()
    selfie = request.data.get("selfie", "").strip()
    if not government_id or not selfie:
        return Response({"message": "Government ID and selfie are required."}, status=status.HTTP_400_BAD_REQUEST)

    profile.account_type = "seller"
    profile.verification_status = "pending"
    profile.government_id_url = government_id
    profile.selfie_url = selfie
    profile.save(update_fields=["account_type", "verification_status", "government_id_url", "selfie_url"])
    notify(request.user, "Verification submitted", "Your seller verification is pending admin review.")
    return Response({"message": "Verification submitted.", "verification_status": profile.verification_status})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verification_requests(request):
    if not request.user.is_staff:
        return Response({"message": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)
    profiles = User_Profile.objects.filter(verification_status="pending").select_related("user")
    data = [
        {
            "user_id": p.user_id,
            "username": p.user.username,
            "email": p.user.email,
            "government_id": p.government_id_url,
            "selfie": p.selfie_url,
            "status": p.verification_status,
        }
        for p in profiles
    ]
    return Response(data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def review_verification(request, user_id):
    if not request.user.is_staff:
        return Response({"message": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)
    profile = get_object_or_404(User_Profile, user_id=user_id)
    decision = request.data.get("decision")
    if decision not in {"approved", "rejected"}:
        return Response({"decision": "Use approved or rejected."}, status=status.HTTP_400_BAD_REQUEST)
    profile.verification_status = "verified" if decision == "approved" else "rejected"
    profile.save(update_fields=["verification_status"])
    notify(profile.user, "Seller verification updated", f"Your verification was {profile.verification_status}.")
    return Response({"verification_status": profile.verification_status})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def conversations(request):
    if request.method == "GET":
        qs = _participant_filter(request.user).distinct()
        return Response(ConversationSerializer(qs, many=True).data)

    seller_username = request.data.get("seller") or request.data.get("username")
    product_id = request.data.get("product")
    if not seller_username:
        return Response({"seller": "Seller username is required."}, status=status.HTTP_400_BAD_REQUEST)
    seller = get_object_or_404(User, username=seller_username)
    if seller == request.user:
        return Response({"message": "You cannot message yourself."}, status=status.HTTP_400_BAD_REQUEST)
    product = Product.objects.filter(product_id=product_id).first() if product_id else None
    conversation, _ = Conversation.objects.get_or_create(
        buyer=request.user,
        seller=seller,
        product=product,
    )
    return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    conversation = _get_user_conversation(request.user, conversation_id)
    return Response(ConversationSerializer(conversation).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request, conversation_id):
    conversation = _get_user_conversation(request.user, conversation_id)
    body = request.data.get("body", "").strip()
    if not body:
        return Response({"body": "Message cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
    message = Message.objects.create(conversation=conversation, sender=request.user, body=body)
    conversation.save(update_fields=["updated_at"])
    recipient = conversation.seller if request.user == conversation.buyer else conversation.buyer
    notify(recipient, "New message", f"{request.user.username}: {body[:80]}", f"/user/messages/{request.user.username}")
    return Response({"id": message.id, "sender": request.user.username, "body": message.body, "created_at": message.created_at}, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def agreements(request):
    expire_overdue_agreements()
    if request.method == "GET":
        qs = Agreement.objects.filter(buyer=request.user) | Agreement.objects.filter(seller=request.user)
        return Response(AgreementSerializer(qs.distinct(), many=True).data)

    conversation = _get_user_conversation(request.user, request.data.get("conversation"))
    if request.user != conversation.seller:
        return Response({"message": "Only the seller can create agreements."}, status=status.HTTP_403_FORBIDDEN)
    product = conversation.product or get_object_or_404(Product, product_id=request.data.get("product"))
    if product.user != request.user:
        return Response({"message": "You can only create agreements for your own products."}, status=status.HTTP_403_FORBIDDEN)
    if product.status not in [Product.STATUS_AVAILABLE, Product.STATUS_NEGOTIATING]:
        return Response({"message": "Product is not available for agreement."}, status=status.HTTP_400_BAD_REQUEST)

    agreement_type = request.data.get("agreement_type", Agreement.TYPE_PURCHASE)
    if agreement_type not in [Agreement.TYPE_PURCHASE, Agreement.TYPE_BOOKING]:
        return Response({"agreement_type": "Use purchase or booking."}, status=status.HTTP_400_BAD_REQUEST)

    amount = Decimal(str(request.data.get("amount") or product.price))
    meetup_at = request.data.get("meetup_at")
    payment_deadline = request.data.get("payment_deadline")
    if not meetup_at:
        return Response({"meetup_at": "Meetup date and time are required."}, status=status.HTTP_400_BAD_REQUEST)

    deadline = timezone.datetime.fromisoformat(payment_deadline.replace("Z", "+00:00")) if payment_deadline else timezone.now() + timezone.timedelta(hours=6)
    agreement = Agreement.objects.create(
        conversation=conversation,
        product=product,
        buyer=conversation.buyer,
        seller=conversation.seller,
        agreement_type=agreement_type,
        amount=amount,
        meetup_location=request.data.get("meetup_location", "").strip() or "To be arranged",
        meetup_at=timezone.datetime.fromisoformat(meetup_at.replace("Z", "+00:00")),
        payment_deadline=deadline,
    )
    product.status = Product.STATUS_PENDING_CONFIRMATION if agreement_type == Agreement.TYPE_PURCHASE else Product.STATUS_PENDING_BOOKING
    product.save(update_fields=["status"])
    notify(agreement.buyer, "Agreement created", f"Review {product.name} and confirm.", f"/user/agreements/{agreement.id}")
    return Response(AgreementSerializer(agreement).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def agreement_detail(request, agreement_id):
    agreement = _get_user_agreement(request.user, agreement_id)
    return Response(AgreementSerializer(agreement).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_agreement(request, agreement_id):
    agreement = _get_user_agreement(request.user, agreement_id)
    if request.user != agreement.buyer:
        return Response({"message": "Only the buyer can confirm."}, status=status.HTTP_403_FORBIDDEN)
    if agreement.status != Agreement.STATUS_PENDING:
        return Response({"message": "Agreement cannot be confirmed."}, status=status.HTTP_400_BAD_REQUEST)
    agreement.status = Agreement.STATUS_AWAITING_PAYMENT
    agreement.buyer_confirmed_at = timezone.now()
    agreement.save(update_fields=["status", "buyer_confirmed_at", "updated_at"])
    notify(agreement.seller, "Agreement accepted", f"{agreement.buyer.username} accepted {agreement.product.name}.")
    return Response(AgreementSerializer(agreement).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_agreement(request, agreement_id):
    agreement = _get_user_agreement(request.user, agreement_id)
    if request.user != agreement.buyer:
        return Response({"message": "Only the buyer can reject."}, status=status.HTTP_403_FORBIDDEN)
    agreement.status = Agreement.STATUS_REJECTED
    agreement.save(update_fields=["status", "updated_at"])
    agreement.product.status = Product.STATUS_AVAILABLE
    agreement.product.save(update_fields=["status"])
    notify(agreement.seller, "Agreement rejected", f"{agreement.buyer.username} rejected {agreement.product.name}.")
    return Response(AgreementSerializer(agreement).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment(request):
    agreement = _get_user_agreement(request.user, request.data.get("agreement"))
    if request.user != agreement.buyer:
        return Response({"message": "Only the buyer can pay."}, status=status.HTTP_403_FORBIDDEN)
    if agreement.status not in [Agreement.STATUS_AWAITING_PAYMENT, Agreement.STATUS_PENDING]:
        return Response({"message": "Agreement is not payable."}, status=status.HTTP_400_BAD_REQUEST)
    amount = agreement.deposit_amount if agreement.agreement_type == Agreement.TYPE_BOOKING else agreement.amount
    payment = Payment.objects.create(
        agreement=agreement,
        payer=request.user,
        amount=amount,
        method=request.data.get("method", "mpesa"),
        phone=request.data.get("phone", ""),
        reference=f"LM-{uuid4().hex[:12].upper()}",
    )
    agreement.status = Agreement.STATUS_RESERVED if agreement.agreement_type == Agreement.TYPE_BOOKING else Agreement.STATUS_IN_ESCROW
    agreement.paid_at = timezone.now()
    agreement.save(update_fields=["status", "paid_at", "updated_at"])
    agreement.product.status = Product.STATUS_BOOKED if agreement.agreement_type == Agreement.TYPE_BOOKING else Product.STATUS_SOLD_PENDING_RELEASE
    agreement.product.save(update_fields=["status"])
    notify(agreement.seller, "Payment received", f"Funds for {agreement.product.name} are held in escrow.")
    return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payments(request):
    qs = Payment.objects.filter(agreement__buyer=request.user) | Payment.objects.filter(agreement__seller=request.user)
    return Response(PaymentSerializer(qs.distinct(), many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_agreement(request, agreement_id):
    agreement = _get_user_agreement(request.user, agreement_id)
    if request.user != agreement.buyer:
        return Response({"message": "Only the buyer can confirm receipt."}, status=status.HTTP_403_FORBIDDEN)
    if agreement.status not in [Agreement.STATUS_IN_ESCROW, Agreement.STATUS_RESERVED]:
        return Response({"message": "Agreement is not ready to complete."}, status=status.HTTP_400_BAD_REQUEST)
    agreement.status = Agreement.STATUS_COMPLETED
    agreement.completed_at = timezone.now()
    agreement.save(update_fields=["status", "completed_at", "updated_at"])
    agreement.product.status = Product.STATUS_COMPLETED
    agreement.product.save(update_fields=["status"])
    for payment in agreement.payments.filter(status__in=[Payment.STATUS_HELD, Payment.STATUS_FROZEN]):
        payment.status = Payment.STATUS_RELEASED
        payment.released_at = timezone.now()
        payment.save(update_fields=["status", "released_at"])
    notify(agreement.seller, "Funds released", f"{agreement.product.name} has been completed.")
    return Response(AgreementSerializer(agreement).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def open_dispute(request, agreement_id):
    agreement = _get_user_agreement(request.user, agreement_id)
    if request.user not in [agreement.buyer, agreement.seller]:
        return Response({"message": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
    dispute, created = Dispute.objects.get_or_create(
        agreement=agreement,
        defaults={
            "opened_by": request.user,
            "reason": request.data.get("reason", "Issue reported"),
            "evidence": request.data.get("evidence", ""),
        },
    )
    agreement.status = Agreement.STATUS_DISPUTED
    agreement.save(update_fields=["status", "updated_at"])
    agreement.product.status = Product.STATUS_DISPUTE
    agreement.product.save(update_fields=["status"])
    agreement.payments.filter(status=Payment.STATUS_HELD).update(status=Payment.STATUS_FROZEN)
    notify(agreement.seller if request.user == agreement.buyer else agreement.buyer, "Dispute opened", f"A dispute was opened for {agreement.product.name}.")
    return Response(DisputeSerializer(dispute).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notifications(request):
    return Response(NotificationSerializer(Notification.objects.filter(recipient=request.user), many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.unread = False
    notification.save(update_fields=["unread"])
    return Response(NotificationSerializer(notification).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def disputes(request):
    if request.user.is_staff:
        qs = Dispute.objects.all()
    else:
        qs = Dispute.objects.filter(agreement__buyer=request.user) | Dispute.objects.filter(agreement__seller=request.user)
    return Response(DisputeSerializer(qs.distinct(), many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dispute_detail(request, dispute_id):
    qs = Dispute.objects.all() if request.user.is_staff else Dispute.objects.filter(agreement__buyer=request.user) | Dispute.objects.filter(agreement__seller=request.user)
    return Response(DisputeSerializer(get_object_or_404(qs, id=dispute_id)).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resolve_dispute(request, dispute_id):
    if not request.user.is_staff:
        return Response({"message": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)
    dispute = get_object_or_404(Dispute, id=dispute_id)
    decision = request.data.get("decision")
    if decision not in {"refund_buyer", "release_seller"}:
        return Response({"decision": "Use refund_buyer or release_seller."}, status=status.HTTP_400_BAD_REQUEST)
    dispute.status = Dispute.STATUS_REFUNDED if decision == "refund_buyer" else Dispute.STATUS_RELEASED
    dispute.resolution = request.data.get("resolution", "")
    dispute.resolved_at = timezone.now()
    dispute.save(update_fields=["status", "resolution", "resolved_at"])
    payment_status = Payment.STATUS_REFUNDED if decision == "refund_buyer" else Payment.STATUS_RELEASED
    dispute.agreement.payments.filter(status=Payment.STATUS_FROZEN).update(status=payment_status)
    dispute.agreement.status = Agreement.STATUS_COMPLETED
    dispute.agreement.product.status = Product.STATUS_COMPLETED
    dispute.agreement.save(update_fields=["status", "updated_at"])
    dispute.agreement.product.save(update_fields=["status"])
    notify(dispute.agreement.buyer, "Dispute resolved", f"Resolution: {dispute.status}")
    notify(dispute.agreement.seller, "Dispute resolved", f"Resolution: {dispute.status}")
    return Response(DisputeSerializer(dispute).data)
