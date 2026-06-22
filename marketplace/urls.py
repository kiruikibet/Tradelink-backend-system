from django.urls import path

from . import views

urlpatterns = [
    path("verification/submit/", views.submit_verification),
    path("verification/requests/", views.verification_requests),
    path("verification/requests/<int:user_id>/", views.review_verification),
    path("conversations/", views.conversations),
    path("conversations/<int:conversation_id>/", views.conversation_detail),
    path("conversations/<int:conversation_id>/messages/", views.send_message),
    path("agreements/", views.agreements),
    path("agreements/<int:agreement_id>/", views.agreement_detail),
    path("agreements/<int:agreement_id>/confirm/", views.confirm_agreement),
    path("agreements/<int:agreement_id>/reject/", views.reject_agreement),
    path("agreements/<int:agreement_id>/complete/", views.complete_agreement),
    path("agreements/<int:agreement_id>/dispute/", views.open_dispute),
    path("payments/", views.payments),
    path("payments/pay/", views.create_payment),
    path("notifications/", views.notifications),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read),
    path("disputes/", views.disputes),
    path("disputes/<int:dispute_id>/", views.dispute_detail),
    path("disputes/<int:dispute_id>/resolve/", views.resolve_dispute),
]
