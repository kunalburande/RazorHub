from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.text import slugify
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Address, CustomerProfile, User
from .serializers import AddressSerializer, CustomerProfileSerializer, RegisterSerializer, UserSerializer
from .email_utils import send_password_reset_email, send_promo_email

# ── Seeded demo users: bypass OTP verification on login ──────────────
SEEDED_EMAILS = frozenset([
    # New seeded users
    "priya.sharma@razorhub.com", "rahul.verma@razorhub.com", "vikram.reddy@razorhub.com",
    "ananya.gupta@razorhub.com", "amit.singh@razorhub.com", "kavya.iyer@razorhub.com",
    "isha.banerjee@razorhub.com", "ramesh.sinha@razorhub.com", "saanvi.joshi@razorhub.com",
    "deepak.tiwari@razorhub.com", "sneha.patel@razorhub.com", "rohit.das@razorhub.com",
    "neha.bose@razorhub.com", "suresh.chatterjee@razorhub.com", "pooja.mishra@razorhub.com",
    "vikram.mehta@razorhub.com", "riya.pandey@razorhub.com", "manoj.yadav@razorhub.com",
    "ajay.kulkarni@razorhub.com", "diya.deshpande@razorhub.com",
    # Legacy seeded test users
    "admin@razorhub.in", "admin@razorhub.local", "seller@techvista.in", "seller@stylecraft.in",
    "seller@homeessentials.in", "seller@glamourbox.in", "seller.saanvi0@store.in",
    "customer.demo@kinahub.local", "customer.demo@razorhub.local",
    "aarav.singh@customer.in", "diya.mehta@customer.in", "vihaan.kumar@customer.in",
    "ananya.gupta@customer.in", "reyansh.iyer@customer.in", "isha.patel@customer.in",
    "kabir.das@customer.in", "myra.joshi@customer.in", "aryan.nair@customer.in",
    "saanvi.rao@customer.in", "advait.mishra@customer.in", "kiara.verma@customer.in",
    "vivaan.chopra@customer.in", "anika.bose@customer.in", "dhruv.thakur@customer.in",
    "riya.agarwal@customer.in", "rohan.shetty@customer.in", "tara.pillai@customer.in",
    "ishaan.saxena@customer.in", "zara.khan@customer.in",
])


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.to_representation(user), status=201)


@api_view(["GET", "PATCH", "PUT"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    user = request.user
    if request.method in ["PATCH", "PUT"]:
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        if "full_name" in request.data:
            parts = str(request.data["full_name"]).strip().split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if "phone" in request.data:
            user.phone = request.data["phone"]
        if "address" in request.data:
            user.address = request.data["address"]
        user.save()

        # If user has a seller profile, update business name and bio
        if hasattr(user, "seller_profile"):
            sp = user.seller_profile
            if "business_name" in request.data and request.data["business_name"]:
                sp.business_name = request.data["business_name"]
            if "phone" in request.data and request.data["phone"]:
                sp.phone = request.data["phone"]
            sp.save()

            if hasattr(sp, "store"):
                store = sp.store
                if "business_name" in request.data and request.data["business_name"]:
                    store.name = request.data["business_name"]
                if "bio" in request.data:
                    store.description = request.data["bio"]
                elif "store_description" in request.data:
                    store.description = request.data["store_description"]
                store.save()

        return Response(UserSerializer(user).data)
    return Response(UserSerializer(user).data)


class IsAdminOrSellerUserRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.effective_role in ["admin", "seller"])


from rest_framework.pagination import PageNumberPagination


class UserPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    pagination_class = UserPagination
    permission_classes = [IsAdminOrSellerUserRole]

    def get_queryset(self):
        user = self.request.user
        if user.effective_role == "admin":
            return User.objects.all().order_by("-date_joined")
        if user.effective_role == "seller":
            return User.objects.filter(role=User.ROLE_CUSTOMER).order_by("-date_joined")
        return User.objects.filter(id=user.id)


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.effective_role == "admin":
            return Address.objects.select_related("user")
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CustomerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.effective_role == "admin":
            return CustomerProfile.objects.select_related("user")
        return CustomerProfile.objects.filter(user=self.request.user)

import requests as http_requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from crm.models import ActivityLog, CustomerRecord
from sellers.models import SellerProfile, Store


def _create_or_refresh_local_google_user(email: str, first_name: str, last_name: str, role: str, business_name: str):
    user = User.objects.filter(email=email).first()
    if not user:
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
        )
    else:
        updates = []
        if first_name and not user.first_name:
            user.first_name = first_name
            updates.append("first_name")
        if last_name and not user.last_name:
            user.last_name = last_name
            updates.append("last_name")
        if role and user.role != role:
            user.role = role
            updates.append("role")
        if updates:
            user.save(update_fields=updates)

    if role == "seller":
        seller, _ = SellerProfile.objects.get_or_create(
            user=user,
            defaults={"business_name": business_name or f"{first_name} {last_name}".strip() or "Local Demo Store"},
        )
        if business_name and seller.business_name != business_name:
            seller.business_name = business_name
            seller.save(update_fields=["business_name"])
        Store.objects.get_or_create(
            seller=seller,
            defaults={
                "name": seller.business_name,
                "slug": slugify(seller.business_name),
            },
        )
    else:
        CustomerProfile.objects.get_or_create(
            user=user,
            defaults={"full_name": f"{first_name} {last_name}".strip() or user.email.split("@")[0]},
        )

    if role == "seller":
        CustomerRecord.objects.get_or_create(user=user)
        seller_profile = SellerProfile.objects.filter(user=user).first()
        if seller_profile:
            from crm.models import SellerRecord
            SellerRecord.objects.get_or_create(seller=seller_profile)
    else:
        CustomerRecord.objects.get_or_create(user=user)

    ActivityLog.objects.get_or_create(
        actor=user,
        verb="registered_with_google_local",
        target_type="user",
        target_id=str(user.id),
        defaults={"metadata": {"role": role, "source": "local-dev"}},
    )
    return user

class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        access_token = request.data.get("access_token")
        role = request.data.get("role", "customer")
        business_name = request.data.get("business_name", "")
        seller_code = request.data.get("seller_code", "")
        local_email = request.data.get("email") or ""
        local_name = request.data.get("name") or ""

        if not access_token:
            return Response({"error": "No access token provided"}, status=400)

        if role == "seller":
            if not business_name:
                return Response({"error": "Business name is required for seller accounts."}, status=400)
            if seller_code != getattr(settings, 'SELLER_REGISTRATION_CODE', 'mafia'):
                return Response({"error": "Invalid seller code. Unauthorized access prevented."}, status=400)

        if settings.DEBUG and (not settings.GOOGLE_OAUTH2_CLIENT_ID or access_token.startswith("__local_demo__")):
            email = local_email or f"{role}.demo@razorhub.local"
            name_parts = (local_name or ("Seller Demo" if role == "seller" else "Customer Demo")).split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            user = _create_or_refresh_local_google_user(email, first_name, last_name, role, business_name)
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            })

        try:
            # Fetch user info from Google using the access token
            resp = http_requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            if resp.status_code != 200:
                return Response({"error": "Invalid Google token"}, status=400)

            info = resp.json()
            email = info.get("email")
            first_name = info.get("given_name", "")
            last_name = info.get("family_name", "")

            if not email:
                return Response({"error": "Google account missing email"}, status=400)

            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                )
                from crm.models import SellerRecord
                from sellers.models import SellerProfile, Store
                
                if role == "seller":
                    seller = SellerProfile.objects.create(user=user, business_name=business_name)
                    Store.objects.create(seller=seller, name=business_name)
                    SellerRecord.objects.create(seller=seller)
                else:
                    CustomerProfile.objects.create(user=user, full_name=f"{first_name} {last_name}".strip())
                    CustomerRecord.objects.create(user=user)
                
                ActivityLog.objects.create(
                    actor=user, verb="registered_with_google",
                    target_type="user", target_id=str(user.id),
                    metadata={"role": role}
                )

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            })

        except Exception as e:
            return Response({"error": f"Google login failed: {str(e)}"}, status=400)


from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone
import random
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken

class LoginWithOTPView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        # Validate credentials (email & password)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.user
        if user.effective_role == "seller" and user.email not in SEEDED_EMAILS:
            seller_code = request.data.get("seller_code")
            valid_codes = {getattr(settings, 'SELLER_REGISTRATION_CODE', 'demo'), 'demo', 'mafia'}
            if seller_code not in valid_codes:
                return Response({"error": "Invalid seller code for seller account."}, status=400)

        # ── OTP bypass for seeded demo users ──
        if user.email in SEEDED_EMAILS:
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            })

        otp = f"{random.randint(100000, 999999)}"
        user.otp_code = otp
        user.otp_created_at = timezone.now()
        user.save(update_fields=['otp_code', 'otp_created_at'])
        
        subject = "Your RazorHub Login Code"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email
        
        html_content = render_to_string("emails/otp_login.html", {"otp": otp})
        text_content = f"Your login verification code is: {otp}. It expires in 5 minutes."
        
        try:
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
        except Exception:
            pass
        
        return Response({
            "require_2fa": True,
            "user_id": user.id,
            "message": "A verification code has been sent to your email."
        })

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user_id = request.data.get("user_id")
        otp_code = request.data.get("otp_code")
        
        if not user_id or not otp_code:
            return Response({"error": "Missing user_id or otp_code"}, status=400)
            
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"error": "Invalid user"}, status=400)
            
        if user.otp_code != str(otp_code):
            return Response({"error": "Invalid verification code"}, status=400)
            
        if not user.otp_created_at or (timezone.now() - user.otp_created_at).total_seconds() > 300:
            return Response({"error": "Verification code expired"}, status=400)
            
        user.otp_code = ""
        user.otp_created_at = None
        user.save(update_fields=['otp_code', 'otp_created_at'])
        
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data
        })


class RequestDeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        otp = f"{random.randint(100000, 999999)}"
        user.otp_code = otp
        user.otp_created_at = timezone.now()
        user.save(update_fields=['otp_code', 'otp_created_at'])

        subject = "RazorHub — Account Deletion Verification"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email

        html_content = render_to_string("emails/otp_delete_account.html", {
            "otp": otp,
            "email": user.email,
        })
        text_content = (
            f"You requested to delete your RazorHub account ({user.email}).\n"
            f"Your verification code is: {otp}\n"
            f"This code expires in 5 minutes.\n\n"
            f"If you did not request this, please change your password immediately."
        )

        try:
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
        except Exception:
            pass

        return Response({"message": "A verification code has been sent to your email."})


class ConfirmDeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        otp_code = request.data.get("otp_code")
        if not otp_code:
            return Response({"error": "Verification code is required."}, status=400)

        user = request.user

        if user.otp_code != str(otp_code):
            return Response({"error": "Invalid verification code."}, status=400)

        if not user.otp_created_at or (timezone.now() - user.otp_created_at).total_seconds() > 300:
            return Response({"error": "Verification code has expired."}, status=400)

        # Permanently delete
        user.delete()
        return Response({"message": "Your account has been permanently deleted."})


class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        if not email:
            return Response({"error": "Email is required."}, status=400)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"message": "If the email exists, a reset code has been sent."})

        otp = f"{random.randint(100000, 999999)}"
        user.otp_code = otp
        user.otp_created_at = timezone.now()
        user.save(update_fields=['otp_code', 'otp_created_at'])
        try:
            send_password_reset_email(user.email, otp)
        except Exception:
            pass

        return Response({"message": "If the email exists, a reset code has been sent."})


class ConfirmPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        otp_code = (request.data.get("otp_code") or "").strip()
        new_password = request.data.get("new_password") or ""

        if not email or not otp_code or not new_password:
            return Response({"error": "Email, OTP code, and new password are required."}, status=400)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Invalid reset request."}, status=400)

        if user.otp_code != str(otp_code):
            return Response({"error": "Invalid verification code."}, status=400)

        if not user.otp_created_at or (timezone.now() - user.otp_created_at).total_seconds() > 300:
            return Response({"error": "Verification code expired."}, status=400)

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            return Response({"error": exc.messages[0] if exc.messages else "Password is too weak."}, status=400)

        user.set_password(new_password)
        user.otp_code = ""
        user.otp_created_at = None
        user.save(update_fields=['password', 'otp_code', 'otp_created_at'])
        return Response({"message": "Password reset successfully."})


class SendPromoEmailView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        subject = request.data.get("subject") or "RazorHub special offer"
        headline = request.data.get("headline") or "Special offers from RazorHub"
        body = request.data.get("body") or "Discover discounts, events, and special sales from local seller stores."
        cta_text = request.data.get("cta_text") or "Shop now"
        cta_url = request.data.get("cta_url") or "http://localhost:5173/products"
        recipients = request.data.get("recipients") or []

        if not recipients:
            recipients = list(User.objects.filter(is_active=True).values_list("email", flat=True)[:500])

        sent = 0
        for email in recipients:
            try:
                send_promo_email(email, subject, headline, body, cta_text=cta_text, cta_url=cta_url)
                sent += 1
            except Exception:
                continue

        return Response({"message": f"Promo emails sent to {sent} users."})
