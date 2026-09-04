"""
RazorHub Realistic Demo Dataset Seeder
======================================
Deterministically populates realistic commerce, banking, and autonomous agent telemetry:
  - 350 Payments
  - 290 Orders
  - 50 Refunds (with Audio Gear surge triggering ~17.2% vs 4.2% baseline anomaly)
  - 50 Invoices (30 Receivables [15 Overdue with follow-up logs], 20 Payables [3 large vendor payables due in 4-6 days])
  - 20 Payouts (15 Processed, 3 Queued, 2 Failed)
  - 60 Settlements (54 Processed, 4 Delayed, 2 Failed)

Intentional Anomaly Patterns:
  1. Refund spike (concentrated on audio equipment: rate 17.24% vs 4.2% baseline)
  2. Failed payment cluster (18 failed attempts during August 28 gateway downtime with Dunning RecoveryTasks)
  3. Abandoned carts (25 abandoned carts with items & RevenueOpportunity records)
  4. Overdue invoices (15 B2B receivables overdue with autonomous agent follow-up logs)
  5. Upcoming cashflow shortage (₹3,20,000 vendor payables due in days 4-6 creating liquidity deficit)
  6. Suspicious high-value transaction (₹2,45,000 order triggering FinancialRiskRecord & TransactionDecision review)
  7. Failed subscription renewals (AgentPaymentAuthorization with limit/decline ledgers)
  8. Delayed settlement (4 uncleared gateway batches totaling ~₹1,42,800 flagged in banking reconciliation)

Preserves all 4 admins, 12 sellers, 20 customers, 719 products, and 13 stores without data loss.
Reproducible via random.seed(42).
"""

import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import random
import uuid
from decimal import Decimal
from datetime import datetime, timedelta, time
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

# Models
from products.models import Product, Category
from sellers.models import Store
from orders.models import Order, OrderItem, Payment, Refund, Payout, Settlement, Cart, CartItem, TransactionDecision
from agent_runtime.models import (
    BusinessInvoice, InvoiceFollowUp, BookkeepingEntry,
    Agent, AgentExecution, AgentAuditLog, AuditEventType, AuditSeverity,
    RefundAnomalyRecord, FinancialRiskRecord, FinancialRiskLevel,
    AgentPaymentAuthorization, AgentAuthorizationLedger
)
from intelligence.models import Campaign, ProductRelationship, RevenueOpportunity, RecoveryTask

User = get_user_model()


def seed_demo_dataset():
    print("=========================================================")
    print("RazorHub Realistic Demo Dataset Seeder Starting...")
    print("=========================================================")
    random.seed(42)

    now = timezone.now()
    today = now.date()

    # 1. Fetch Existing Entities
    customer_users = list(User.objects.filter(is_staff=False, is_superuser=False))
    if not customer_users:
        print("[!] No customer users found. Please run baseline user seeder first.")
        return
    print(f"[i] Found {len(customer_users)} customer accounts.")

    stores = list(Store.objects.all())
    if not stores:
        print("[!] No stores found.")
        return
    print(f"[i] Found {len(stores)} merchant stores.")

    all_products = list(Product.objects.all())
    if not all_products:
        print("[!] No products found.")
        return
    print(f"[i] Found {len(all_products)} products.")

    audio_products = list(
        Product.objects.filter(category__name__icontains="Audio") |
        Product.objects.filter(name__icontains="Headphone") |
        Product.objects.filter(name__icontains="Earbud")
    )
    if not audio_products:
        audio_products = all_products[:10]
    print(f"[i] Found {len(audio_products)} audio products for refund spike clustering.")

    agent_obj = Agent.objects.first()

    # 2. Idempotent cleanup of prior demo transactions (clean reset without touching users/stores/products)
    print("\n[-] Cleaning prior seed artifacts to ensure exact deterministic counts...")
    with transaction.atomic():
        Refund.objects.all().delete()
        Payout.objects.all().delete()
        Settlement.objects.all().delete()
        BusinessInvoice.objects.all().delete()
        InvoiceFollowUp.objects.all().delete()
        RefundAnomalyRecord.objects.all().delete()
        FinancialRiskRecord.objects.all().delete()
        RevenueOpportunity.objects.filter(opportunity_type="abandoned_cart").delete()
        RecoveryTask.objects.filter(task_id__startswith="REC-2026-AUG28-").delete()
        AgentPaymentAuthorization.objects.all().delete()
        AgentAuthorizationLedger.objects.all().delete()

        # Delete orders and standalone payments beyond baseline 59
        Order.objects.filter(id__gt=223).delete()
        Payment.objects.filter(order__isnull=True).delete()
        Payment.objects.filter(id__gt=223).delete()

        # Reset the 59 baseline payments (55 paid, 3 pending, 1 refunded)
        baseline_payments = list(Payment.objects.filter(id__lte=223).order_by("id"))
        for idx, p in enumerate(baseline_payments):
            if idx == 0:
                p.status = Payment.STATUS_REFUNDED
            elif idx in [1, 2, 3]:
                p.status = Payment.STATUS_PENDING
            else:
                p.status = Payment.STATUS_PAID
            p.save(update_fields=["status"])

    existing_order_count = Order.objects.count()
    print(f"[+] Baseline preserved: {existing_order_count} orders, {Payment.objects.count()} payments.")

    # 3. Generate Orders to reach EXACTLY 290 orders
    target_orders = 290
    orders_to_create = target_orders - existing_order_count
    print(f"\n[+] Generating {orders_to_create} new realistic orders to reach exactly {target_orders}...")

    # Designate statuses:
    # 49 refunded + 1 baseline refunded = 50 refunds
    # 5 pending (with failed payment)
    # 10 processing
    # 20 shipped
    # Remainder (147) delivered (paid)
    new_orders = []
    new_order_payments = []

    # Identify customer addresses or fallbacks
    cities = [
        ("Mumbai", "Maharashtra", "400001"),
        ("Bengaluru", "Karnataka", "560001"),
        ("Delhi", "Delhi", "110001"),
        ("Hyderabad", "Telangana", "500001"),
        ("Pune", "Maharashtra", "411001"),
        ("Chennai", "Tamil Nadu", "600001"),
        ("Kolkata", "West Bengal", "700001"),
        ("Ahmedabad", "Gujarat", "380001"),
    ]

    for i in range(orders_to_create):
        cust = customer_users[i % len(customer_users)]
        day_offset = (i * 45) // orders_to_create  # spread over last 45 days
        order_time = now - timedelta(days=day_offset, hours=random.randint(1, 18), minutes=random.randint(0, 59))

        city, state, pin = random.choice(cities)
        shipping_addr = f"Flat {random.randint(101, 804)}, Building {chr(65 + (i % 6))}, Tech Park Road, {city}, {state} - {pin}"

        # Status allocation
        if i < 49:
            status = Order.STATUS_CHOICES[3][0]  # 'delivered' then refunded
            pay_status = Payment.STATUS_REFUNDED
            is_refund_target = True
        elif i < 54:
            status = Order.STATUS_CHOICES[0][0]  # 'pending'
            pay_status = Payment.STATUS_FAILED
            is_refund_target = False
        elif i < 64:
            status = Order.STATUS_CHOICES[1][0]  # 'processing'
            pay_status = Payment.STATUS_PAID
            is_refund_target = False
        elif i < 84:
            status = Order.STATUS_CHOICES[2][0]  # 'shipped'
            pay_status = Payment.STATUS_PAID
            is_refund_target = False
        else:
            status = Order.STATUS_CHOICES[3][0]  # 'delivered'
            pay_status = Payment.STATUS_PAID
            is_refund_target = False

        # Pattern 6: Suspicious High-Value Order
        is_suspicious_order = (i == 100)
        if is_suspicious_order:
            cust = User.objects.filter(email="aarav.singh@customer.in").first() or cust
            total_price = Decimal("245000.00")
            status = Order.STATUS_CHOICES[0][0]  # pending review
            pay_status = Payment.STATUS_PENDING
        else:
            total_price = Decimal("0.00")

        order = Order(
            user=cust,
            status=status,
            payment_method=Order.PAYMENT_RAZORPAY if random.random() > 0.15 else Order.PAYMENT_COD,
            delivery_eta="3-5 Business Days",
            delivery_fee=Decimal("50.00") if total_price < Decimal("999.00") else Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total_price=total_price,
            shipping_address=shipping_addr,
            customer_note=f"[DemoSeed] Order #{i+1}",
        )
        order.save()
        Order.objects.filter(id=order.id).update(created_at=order_time)

        # Populate Order Items
        calculated_total = Decimal("0.00")
        if is_suspicious_order:
            # 4x Premium Laptops (₹53,386 each = ₹2,13,544) + Sony WH-1000XM6 (₹29,990) + accessories = ₹2,45,000
            laptop = Product.objects.filter(price__gte=45000).first() or all_products[0]
            sony = Product.objects.filter(name__icontains="Sony Wh 1000xm6").first() or audio_products[0]
            hub = Product.objects.filter(name__icontains="USB C Hub").first() or all_products[1]

            OrderItem.objects.create(order=order, product=laptop, quantity=4, price=Decimal("53386.00"))
            OrderItem.objects.create(order=order, product=sony, quantity=1, price=Decimal("29990.00"))
            OrderItem.objects.create(order=order, product=hub, quantity=1, price=Decimal("1466.00"))
            calculated_total = Decimal("245000.00")
        else:
            # For 28 of the 49 refunded orders, pick audio products (Pattern 1: Refund Spike)
            if is_refund_target and i < 28:
                item_prod = random.choice(audio_products)
                qty = 1
                OrderItem.objects.create(order=order, product=item_prod, quantity=qty, price=item_prod.price)
                calculated_total += item_prod.price * qty
            else:
                num_items = random.randint(1, 3)
                chosen_prods = random.sample(all_products, num_items)
                for prod in chosen_prods:
                    qty = random.randint(1, 2)
                    OrderItem.objects.create(order=order, product=prod, quantity=qty, price=prod.price)
                    calculated_total += prod.price * qty

        Order.objects.filter(id=order.id).update(total_price=calculated_total)

        # Create linked Payment
        payment = Payment.objects.create(
            order=order,
            method=order.payment_method,
            status=pay_status,
            amount=calculated_total,
            provider_reference=f"pay_seed_{order.id}_{uuid.uuid4().hex[:8]}",
        )
        Payment.objects.filter(id=payment.id).update(created_at=order_time)

        # Pattern 6 Decision & Forensic Risk Record
        if is_suspicious_order:
            TransactionDecision.objects.create(
                order=order,
                decision="REQUIRE_USER_CONFIRMATION",
                risk_score=Decimal("0.8850"),
                amount=Decimal("245000.00"),
                actor_type="autonomous_shopping_agent",
                actor_id="agent_shopping_v2",
                policy_version="v2.4-enterprise",
                reason_codes=[
                    "HIGH_VALUE_OUTLIER",
                    "VELOCITY_SPIKE",
                    "NEW_IP_LOCATION",
                    "AGENT_BUDGET_CAP_EXCEEDED"
                ],
                inventory_snapshot={"items_count": 6, "warehouse": "BOM-CENTRAL-01"},
            )
            FinancialRiskRecord.objects.create(
                user=cust,
                agent=agent_obj,
                transaction_amount=Decimal("245000.00"),
                risk_score=89,
                risk_level=FinancialRiskLevel.CRITICAL,
                critical_rule_triggered=True,
                reasons=["HIGH_VALUE_OUTLIER", "VELOCITY_SPIKE", "NEW_IP_LOCATION"],
                explanation="High-value transaction ₹2,45,000 exceeds standard customer baseline by 8.4x. Multi-factor anomaly triggered; mandatory MFA confirmation required.",
                rule_breakdown=[
                    {"rule": "TRANSACTION_AMOUNT_CEILING", "score": 95, "threshold": 50000},
                    {"rule": "DEVICE_VELOCITY_RISK", "score": 82, "threshold": 60},
                    {"rule": "GEO_IP_DISTANCE", "score": 88, "threshold": 75},
                ],
            )
            print(f"[!] Pattern 6 seeded: Suspicious high-value order #{order.id} (Rs. 2,45,000) with CRITICAL RiskRecord.")

    total_orders_final = Order.objects.count()
    print(f"[OK] Orders created. Total Order count = {total_orders_final}")

    # 4. Standalone Payments to reach EXACTLY 350 total payments
    order_payments_count = Payment.objects.count()
    standalone_needed = 350 - order_payments_count
    print(f"\n[+] Generating {standalone_needed} standalone payment records to reach exactly 350...")

    # Distribution of 60 standalone payments:
    # - 18 Failed payments (Pattern 2: August 28 Downtime cluster with Dunning RecoveryTasks)
    # - 7 Failed payments (Pattern 7: Recurring subscription renewal decline)
    # - 5 Pending payments
    # - 30 Paid micropayments (x402 protocol, agent execution payments)
    aug28_base = timezone.make_aware(datetime(2026, 8, 28, 14, 5, 0)) if timezone.is_naive(now) else datetime(2026, 8, 28, 14, 5, 0, tzinfo=now.tzinfo)

    recovery_tasks_data = [
        ("Pending", "Autonomous Dunning: SMS retry scheduled (T+4h)", Decimal("12499.00")),
        ("In_Progress", "WhatsApp recovery link dispatched with 5% discount voucher", Decimal("8999.00")),
        ("In_Progress", "Email invoice link dispatched with 1-click Razorpay checkout", Decimal("15450.00")),
        ("Recovered", "Auto-retried on secondary card via standing mandate. Recovered ₹7,200", Decimal("7200.00")),
        ("Recovered", "Customer clicked WhatsApp recovery link and settled via UPI", Decimal("4999.00")),
        ("Escalated", "Escalated to human support after attempt 3 (PhonePe switch timeout)", Decimal("18990.00")),
    ]

    for idx in range(18):
        cust = customer_users[idx % len(customer_users)]
        fail_time = aug28_base + timedelta(minutes=idx * 7)
        task_status, action, amount = recovery_tasks_data[idx % len(recovery_tasks_data)]

        pay = Payment.objects.create(
            order=None,
            method="razorpay",
            status=Payment.STATUS_FAILED,
            amount=amount,
            provider_reference=f"pay_cluster_aug28_{idx:03d}_{uuid.uuid4().hex[:6]}",
        )
        Payment.objects.filter(id=pay.id).update(created_at=fail_time)

        # Create linked RecoveryTask (Pattern 2)
        store = stores[idx % len(stores)]
        RecoveryTask.objects.create(
            store=store,
            task_id=f"REC-2026-AUG28-{idx+1:03d}",
            customer_email=cust.email,
            cart_value=amount,
            status=task_status,
            agent_action=action,
        )

    print("[!] Pattern 2 seeded: 18 failed payments clustered on Aug 28 with RecoveryTasks.")

    # 7 Failed recurring renewal payments (Pattern 7)
    for idx in range(7):
        cust = customer_users[(idx + 5) % len(customer_users)]
        pay = Payment.objects.create(
            order=None,
            method="razorpay",
            status=Payment.STATUS_FAILED,
            amount=Decimal("2999.00") if idx % 2 == 0 else Decimal("4999.00"),
            provider_reference=f"pay_sub_renewal_fail_{idx}_{uuid.uuid4().hex[:6]}",
        )
        Payment.objects.filter(id=pay.id).update(created_at=now - timedelta(days=idx * 3 + 2))

    # 5 Pending payments
    for idx in range(5):
        pay = Payment.objects.create(
            order=None,
            method="razorpay",
            status=Payment.STATUS_PENDING,
            amount=Decimal(random.randint(1500, 8500)),
            provider_reference=f"pay_pending_standalone_{idx}_{uuid.uuid4().hex[:6]}",
        )
        Payment.objects.filter(id=pay.id).update(created_at=now - timedelta(hours=idx * 4 + 1))

    # 30 Paid micropayments / instant retries
    for idx in range(30):
        pay = Payment.objects.create(
            order=None,
            method="razorpay",
            status=Payment.STATUS_PAID,
            amount=Decimal(random.randint(250, 4500)),
            provider_reference=f"pay_x402_micropay_{idx}_{uuid.uuid4().hex[:6]}",
        )
        Payment.objects.filter(id=pay.id).update(created_at=now - timedelta(days=idx % 30, hours=random.randint(2, 20)))

    total_payments_final = Payment.objects.count()
    print(f"[OK] Payments created. Total Payment count = {total_payments_final}")

    # 5. Populate Refunds (reach EXACTLY 50 total refunds)
    print("\n[+] Creating exactly 50 Refund records & configuring Pattern 1 (Audio Refund Spike)...")
    refunded_payments = list(Payment.objects.filter(status=Payment.STATUS_REFUNDED).select_related("order"))
    print(f"[i] Found {len(refunded_payments)} payments with status='refunded'.")

    # If count is slightly off from 50, adjust payments to have exactly 50
    if len(refunded_payments) < 50:
        shortfall = 50 - len(refunded_payments)
        extra_payments = Payment.objects.filter(status=Payment.STATUS_PAID)[:shortfall]
        for ep in extra_payments:
            ep.status = Payment.STATUS_REFUNDED
            ep.save(update_fields=["status"])
        refunded_payments = list(Payment.objects.filter(status=Payment.STATUS_REFUNDED).select_related("order"))
    elif len(refunded_payments) > 50:
        excess = len(refunded_payments) - 50
        for ep in refunded_payments[:excess]:
            ep.status = Payment.STATUS_PAID
            ep.save(update_fields=["status"])
        refunded_payments = list(Payment.objects.filter(status=Payment.STATUS_REFUNDED).select_related("order"))

    # Reasons distribution
    # 28 audio defective (Pattern 1), 7 late delivery, 6 customer refusal, 5 sizing issue, 4 duplicate order
    reasons_list = (
        ["defective_product"] * 28 +
        ["late_delivery"] * 7 +
        ["customer_refusal"] * 6 +
        ["sizing_issue"] * 5 +
        ["duplicate_order"] * 4
    )

    audio_affected_names = [p.name for p in audio_products[:4]]

    for idx, p in enumerate(refunded_payments[:50]):
        reason = reasons_list[idx]
        is_audio_defect = (reason == "defective_product" and idx < 28)
        notes = (
            "Hardware batch #QC-AUG-44 audio dropout on Bluetooth 5.3 chipset. Auto-approved."
            if is_audio_defect
            else "Standard return initiated and approved by merchant policy."
        )

        refund_order = p.order
        if not refund_order:
            # Fallback to an existing order
            refund_order = Order.objects.first()

        Refund.objects.create(
            refund_id=f"rfnd_{idx+1:04d}_{uuid.uuid4().hex[:6]}",
            order=refund_order,
            payment=p,
            amount=p.amount,
            currency="INR",
            reason=reason,
            status=Refund.STATUS_PROCESSED,
            notes=notes,
        )

    # Persist RefundAnomalyRecord for Pattern 1
    RefundAnomalyRecord.objects.create(
        agent=agent_obj,
        current_refund_rate=Decimal("17.24"),
        baseline_refund_rate=Decimal("4.20"),
        delta=Decimal("13.04"),
        threshold_multiplier=Decimal("3.10"),
        is_anomaly=True,
        severity="CRITICAL",
        refund_count=50,
        total_orders_count=290,
        refund_amount=Decimal("382450.00"),
        total_sales_amount=Decimal("2218400.00"),
        affected_products=audio_affected_names,
        by_product=[
            {"product_name": name, "refund_count": 7, "refund_rate": 24.1, "refund_amount": 95000.0}
            for name in audio_affected_names
        ],
        by_customer=[
            {"customer_email": c.email, "refund_count": 3, "total_refunded": 28500.0}
            for c in customer_users[:5]
        ],
        by_payment_method=[
            {"method": "UPI - PhonePe", "refund_count": 28, "total_amount": 210000.0},
            {"method": "Axis Credit Card", "refund_count": 14, "total_amount": 125000.0},
            {"method": "Cash on Delivery", "refund_count": 8, "total_amount": 47450.0},
        ],
        by_day=[
            {"date": (today - timedelta(days=d)).strftime("%Y-%m-%d"), "refund_count": random.randint(5, 12)}
            for d in range(7, 0, -1)
        ],
        explanation=(
            "Autonomous telemetry detected a critical 4.1x refund spike (17.24% vs 4.20% baseline) "
            "concentrated in ANC Wireless Audio Gear. Firmware telemetry confirms audio dropout in Bluetooth 5.3 SoC. "
            "Autonomous vendor warranty claim filed and product page advisory enabled."
        ),
        likely_reasons=[
            "Bluetooth 5.3 SoC firmware disconnection bug in batch #QC-AUG-44",
            "Improper factory packaging causing driver distortion during transit",
            "Customer sizing dissatisfaction on over-ear headband tension",
        ],
        recommended_actions=[
            "Quarantine stock batch #QC-AUG-44 across all fulfillment centers",
            "Contact manufacturer for rapid firmware OTA update patch",
            "Convert high-return SKUs to prepaid-only with mandatory sizing verification",
        ],
    )
    print(f"[OK] Exactly {Refund.objects.count()} Refunds created. Pattern 1 RefundAnomalyRecord saved.")

    # 6. Populate Invoices (reach EXACTLY 50 total BusinessInvoice)
    print("\n[+] Creating exactly 50 BusinessInvoice records (Pattern 4 Overdue & Pattern 5 Cashflow Shortage)...")
    # 30 Receivables: 15 Overdue (Pattern 4), 10 Paid, 5 Pending
    # 20 Payables: 3 Large vendor payables in 4-6 days (Pattern 5), 7 Paid, 10 Pending

    receivable_clients = [
        ("TechCorp Solutions Pvt Ltd", "45000.00", 12),
        ("Zomato Partner Merchant Hub", "62500.00", 8),
        ("Flipkart Commerce Fulfillment", "78000.00", 19),
        ("Blinkit Express Hub Okhla", "34000.00", 6),
        ("Dunzo Wholesale Logistics", "28500.00", 25),
        ("Reliance Retail Distribution", "89000.00", 14),
        ("Tata 1mg Health Network", "41000.00", 22),
        ("Swiggy Instamart Warehouse", "53000.00", 11),
        ("Nykaa Beauty Marketplace", "36500.00", 17),
        ("Pepperfry Studio Partners", "49000.00", 9),
        ("Urban Company Service Depot", "29500.00", 31),
        ("Purplle Logistics Hub", "31000.00", 7),
        ("Zepto Darkstore Koramangala", "58000.00", 15),
        ("Meesho Seller Aggregator", "47500.00", 28),
        ("BigBasket Farm Distribution", "66000.00", 10),
    ]

    # Pattern 4: 15 Overdue Receivables with follow-ups
    for idx, (client, amt, days_ago) in enumerate(receivable_clients):
        inv_date = today - timedelta(days=days_ago)
        inv = BusinessInvoice.objects.create(
            invoice_number=f"INV-2026-REC-{idx+1:03d}",
            vendor_or_customer=client,
            invoice_type=BusinessInvoice.InvoiceType.RECEIVABLE,
            amount=Decimal(amt),
            due_date=inv_date,
            status=BusinessInvoice.InvoiceStatus.OVERDUE,
            priority=BusinessInvoice.PriorityLevel.HIGH if Decimal(amt) > Decimal("50000.00") else BusinessInvoice.PriorityLevel.MEDIUM,
            follow_up_count=random.randint(1, 3),
            last_follow_up_at=now - timedelta(days=random.randint(1, 4)),
            bank_account_number=f"918273645{idx:02d}",
            ifsc_code="HDFC0001234",
            category="B2B Marketplace Commission",
            notes=f"Overdue debtor account: {client}. Auto-communications dispatched.",
        )
        # Seed InvoiceFollowUp communication logs
        InvoiceFollowUp.objects.create(
            invoice=inv,
            channel=InvoiceFollowUp.Channel.EMAIL,
            message=(
                f"Dear Accounts Team at {client},\n\n"
                f"Invoice #{inv.invoice_number} for ₹{inv.amount:,.2f} is currently overdue by {days_ago} days. "
                f"Please settle via instant bank transfer or click the RazorHub debtor link: https://razorhub.io/pay/{inv.invoice_number}\n\n"
                f"Regards,\nAutonomous Receivables Agent"
            ),
            sent_by="Autonomous Receivables Agent",
        )
        if inv.follow_up_count >= 2:
            InvoiceFollowUp.objects.create(
                invoice=inv,
                channel=InvoiceFollowUp.Channel.WHATSAPP,
                message=f"Urgent: Overdue payment reminder for #{inv.invoice_number} (₹{inv.amount:,.2f}). Immediate attention requested.",
                sent_by="Autonomous Receivables Agent",
            )

    print("[!] Pattern 4 seeded: 15 overdue B2B receivables with autonomous communication logs.")

    # 10 Paid Receivables
    for idx in range(10):
        paid_date = today - timedelta(days=idx * 3 + 5)
        inv = BusinessInvoice.objects.create(
            invoice_number=f"INV-2026-REC-PAID-{idx+1:03d}",
            vendor_or_customer=f"Enterprise Retail Partner {chr(65+idx)}",
            invoice_type=BusinessInvoice.InvoiceType.RECEIVABLE,
            amount=Decimal(random.randint(15000, 48000)),
            due_date=paid_date,
            status=BusinessInvoice.InvoiceStatus.PAID,
            priority=BusinessInvoice.PriorityLevel.MEDIUM,
            bank_account_number=f"918200114{idx:02d}",
            ifsc_code="ICIC0005521",
            category="Wholesale Merchant Fees",
            notes="Settled via NEFT nodal account.",
        )
        BookkeepingEntry.objects.create(
            transaction_reference=f"REC-{inv.invoice_number}",
            amount=inv.amount,
            entry_type=BookkeepingEntry.EntryType.CREDIT,
            accounting_category=BookkeepingEntry.AccountingCategory.REVENUE_SALES,
            notes=f"Debtor settlement received for invoice {inv.invoice_number}",
        )

    # 5 Pending Receivables (due in future)
    for idx in range(5):
        due_future = today + timedelta(days=idx * 4 + 7)
        BusinessInvoice.objects.create(
            invoice_number=f"INV-2026-REC-FUT-{idx+1:03d}",
            vendor_or_customer=f"Regional Franchise Outlet {idx+1}",
            invoice_type=BusinessInvoice.InvoiceType.RECEIVABLE,
            amount=Decimal(random.randint(22000, 65000)),
            due_date=due_future,
            status=BusinessInvoice.InvoiceStatus.PENDING,
            priority=BusinessInvoice.PriorityLevel.MEDIUM,
            bank_account_number=f"918233441{idx:02d}",
            ifsc_code="SBIN0009876",
            category="Platform Subscriptions",
            notes="Scheduled monthly recurring invoice.",
        )

    # 20 Payables (Pattern 5: Upcoming Cashflow Shortage with 3 large vendor payables in days 4-6)
    shortage_payables = [
        ("INV-2026-PAY-AWS01", "AWS Cloud Infrastructure & Dedicated Neon Postgres", "145000.00", 4),
        ("INV-2026-PAY-LOG02", "BlueDart Air Express & Delhivery Freight Logistics", "95000.00", 5),
        ("INV-2026-PAY-PKG03", "EcoPack Sustainable Bulk Packaging Materials", "80000.00", 6),
    ]
    for inv_num, vendor, amt, days_ahead in shortage_payables:
        BusinessInvoice.objects.create(
            invoice_number=inv_num,
            vendor_or_customer=vendor,
            invoice_type=BusinessInvoice.InvoiceType.PAYABLE,
            amount=Decimal(amt),
            due_date=today + timedelta(days=days_ahead),
            status=BusinessInvoice.InvoiceStatus.PENDING,
            priority=BusinessInvoice.PriorityLevel.HIGH,
            bank_account_number="98765432101",
            ifsc_code="HDFC0000001",
            category="Cloud Infrastructure" if "AWS" in vendor else "Logistics & Supply",
            notes="CRITICAL: Major vendor payable due in upcoming treasury cycle. Projected cash outflow surge.",
        )
    print("[!] Pattern 5 seeded: 3 massive vendor payables (Rs. 3,20,000 total) due in 4-6 days creating cashflow shortage.")

    # 7 Paid Payables
    for idx in range(7):
        paid_date = today - timedelta(days=idx * 4 + 3)
        inv = BusinessInvoice.objects.create(
            invoice_number=f"INV-2026-PAY-PAID-{idx+1:03d}",
            vendor_or_customer=f"Vendor Services Provider #{idx+1}",
            invoice_type=BusinessInvoice.InvoiceType.PAYABLE,
            amount=Decimal(random.randint(12000, 38000)),
            due_date=paid_date,
            status=BusinessInvoice.InvoiceStatus.PAID,
            priority=BusinessInvoice.PriorityLevel.MEDIUM,
            bank_account_number=f"987650011{idx:02d}",
            ifsc_code="KKBK0001928",
            category="Operational Expenses",
            notes="Disbursed via automated batch payout.",
        )
        BookkeepingEntry.objects.create(
            transaction_reference=f"PAY-{inv.invoice_number}",
            amount=inv.amount,
            entry_type=BookkeepingEntry.EntryType.DEBIT,
            accounting_category=BookkeepingEntry.AccountingCategory.CLOUD_INFRASTRUCTURE if idx % 2 == 0 else BookkeepingEntry.AccountingCategory.PAYROLL_CONTRACTORS,
            notes=f"Vendor disbursement for invoice {inv.invoice_number}",
        )

    # 10 Pending Payables (spread across days 8 to 28)
    for idx in range(10):
        due_future = today + timedelta(days=idx * 2 + 8)
        BusinessInvoice.objects.create(
            invoice_number=f"INV-2026-PAY-FUT-{idx+1:03d}",
            vendor_or_customer=f"Contractor & Marketing Partner {idx+1}",
            invoice_type=BusinessInvoice.InvoiceType.PAYABLE,
            amount=Decimal(random.randint(8500, 24000)),
            due_date=due_future,
            status=BusinessInvoice.InvoiceStatus.PENDING,
            priority=BusinessInvoice.PriorityLevel.MEDIUM,
            bank_account_number=f"987659988{idx:02d}",
            ifsc_code="AXIS0009988",
            category="Marketing & Affiliate Payouts",
            notes="Scheduled routine contractor disbursement.",
        )

    print(f"[OK] Exactly {BusinessInvoice.objects.count()} BusinessInvoices created (30 Receivables, 20 Payables).")

    # 7. Populate Payouts (reach EXACTLY 20 total Payout)
    print("\n[+] Creating exactly 20 Payout records...")
    # 15 Processed, 3 Queued, 2 Failed
    payout_vendors = [
        ("TechVista Electronics Settlement Hub", "TechVista Electronics", "98500.00"),
        ("StyleCraft Fashion Merchandising", "StyleCraft Fashion", "74200.00"),
        ("Ananya Electronics Vendor Pool", "Ananya Electronics Hub", "88900.00"),
        ("HomeEssentials India Logistics", "HomeEssentials India", "43500.00"),
        ("Sinha Sports Equipment Supply", "Sinha Sports & Sneakers", "61000.00"),
        ("Joshi Jewels Diamond Suppliers", "Joshi Jewels & Accessories", "115000.00"),
        ("Deepak Tiwari Books & Retail", "Deepak Grocery & Books", "26400.00"),
        ("Kavya Photo Studio Media", "Kavya Photo Studio", "38000.00"),
        ("Amit Fashion House Mill Agency", "Amit Fashion House", "52800.00"),
        ("Isha Home Decor Imports", "Isha Home & Living", "49200.00"),
        ("RazorHub Cloud Hosting & DevOps", "TechVista Electronics", "31500.00"),
        ("Apex Courier Priority Fleet", "HomeEssentials India", "44000.00"),
        ("SecureShield Payment Gateway Fees", "StyleCraft Fashion", "18500.00"),
        ("OmniChannel SMS & WhatsApp Gateway", "Ananya Electronics Hub", "22400.00"),
        ("Legal & Tax Compliance Advisory", "Joshi Jewels & Accessories", "35000.00"),
    ]

    for idx, (recipient, store_name, amt) in enumerate(payout_vendors):
        store = Store.objects.filter(name__icontains=store_name.split()[0]).first() or stores[idx % len(stores)]
        payout = Payout.objects.create(
            payout_id=f"pout_{idx+1:04d}_{uuid.uuid4().hex[:6]}",
            store=store,
            recipient_name=recipient,
            recipient_account=f"5010029384{idx:02d}",
            amount=Decimal(amt),
            currency="INR",
            mode=random.choice(["NEFT", "RTGS", "IMPS"]),
            status=Payout.STATUS_PROCESSED,
            utr=f"UTR{random.randint(100000000000, 999999999999)}",
            narration=f"Settlement disbursement to {store_name}",
        )
        BookkeepingEntry.objects.create(
            transaction_reference=f"PAYOUT-{payout.payout_id}",
            amount=payout.amount,
            entry_type=BookkeepingEntry.EntryType.DEBIT,
            accounting_category=BookkeepingEntry.AccountingCategory.PAYROLL_CONTRACTORS,
            notes=f"Disbursement to {recipient} (Ref: {payout.utr})",
        )

    # 3 Queued Payouts
    for idx in range(3):
        store = stores[idx % len(stores)]
        Payout.objects.create(
            payout_id=f"pout_queued_{idx+1:02d}_{uuid.uuid4().hex[:6]}",
            store=store,
            recipient_name=f"Merchant Queue Beneficiary #{idx+1}",
            recipient_account=f"5010099887{idx:02d}",
            amount=Decimal(random.randint(14000, 42000)),
            currency="INR",
            mode="NEFT",
            status=Payout.STATUS_QUEUED,
            utr="",
            narration="Batch queued for 17:00 IST clearance cycle.",
        )

    # 2 Failed Payouts
    failed_reasons = [
        ("INVALID_IFSC_CODE", "Branch IFSC closed / merged under RBI scheme"),
        ("BENEFICIARY_NAME_MISMATCH", "Beneficiary name does not match nodal bank record"),
    ]
    for idx, (code, desc) in enumerate(failed_reasons):
        store = stores[(idx + 4) % len(stores)]
        Payout.objects.create(
            payout_id=f"pout_fail_{idx+1:02d}_{uuid.uuid4().hex[:6]}",
            store=store,
            recipient_name=f"Rejected Vendor #{idx+1} ({code})",
            recipient_account=f"5010011223{idx:02d}",
            amount=Decimal(random.randint(19000, 55000)),
            currency="INR",
            mode="IMPS",
            status=Payout.STATUS_FAILED,
            utr="",
            narration=f"Disbursement rejected by bank gateway: {desc}",
        )

    print(f"[OK] Exactly {Payout.objects.count()} Payout records created (15 Processed, 3 Queued, 2 Failed).")

    # 8. Populate Settlements (reach EXACTLY 60 total Settlement)
    print("\n[+] Creating exactly 60 Settlement records (Pattern 8 Delayed Settlements)...")
    # 54 Processed, 4 Delayed (Pattern 8), 2 Failed
    # 60 records spanning last 60 days
    for day_idx in range(60):
        settle_date = today - timedelta(days=day_idx)
        store = stores[day_idx % len(stores)]

        # Pattern 8: 4 Delayed Settlements on days 3, 4, 5, 6
        if day_idx in [3, 4, 5, 6]:
            gross = Decimal(random.randint(32000, 42000))
            fee = round(gross * Decimal("0.02"), 2)
            tax = round(fee * Decimal("0.18"), 2)
            net = gross - fee - tax

            Settlement.objects.create(
                settlement_id=f"setl_delay_{day_idx}_{uuid.uuid4().hex[:6]}",
                store=store,
                amount=gross,
                fees=fee,
                tax=tax,
                net_amount=net,
                status=Settlement.STATUS_DELAYED,
                utr="",
                settlement_date=settle_date,
                is_delayed=True,
                notes="Gateway settlement batch hold: Nodal clearing delay under bank inquiry.",
            )
        elif day_idx in [12, 27]:
            # 2 Failed Settlements
            gross = Decimal(random.randint(18000, 35000))
            Settlement.objects.create(
                settlement_id=f"setl_fail_{day_idx}_{uuid.uuid4().hex[:6]}",
                store=store,
                amount=gross,
                fees=Decimal("0.00"),
                tax=Decimal("0.00"),
                net_amount=gross,
                status=Settlement.STATUS_FAILED,
                utr="",
                settlement_date=settle_date,
                is_delayed=False,
                notes="Bank network maintenance downtime: Rescheduled for next working day.",
            )
        else:
            # 54 Processed Settlements
            gross = Decimal(random.randint(25000, 85000))
            fee = round(gross * Decimal("0.02"), 2)
            tax = round(fee * Decimal("0.18"), 2)
            net = gross - fee - tax

            Settlement.objects.create(
                settlement_id=f"setl_proc_{day_idx}_{uuid.uuid4().hex[:6]}",
                store=store,
                amount=gross,
                fees=fee,
                tax=tax,
                net_amount=net,
                status=Settlement.STATUS_PROCESSED,
                utr=f"UTR{random.randint(100000000000, 999999999999)}",
                settlement_date=settle_date,
                is_delayed=False,
                notes="Credited to merchant current account via Razorpay automated settlement.",
            )

    print(f"[OK] Exactly {Settlement.objects.count()} Settlement records created (54 Processed, 4 Delayed, 2 Failed).")
    print("[!] Pattern 8 seeded: 4 delayed settlements (~Rs. 1,42,800) visible in Banking Reconciliation.")

    # 9. Pattern 3: Abandoned Carts & RevenueOpportunity
    print("\n[+] Creating Pattern 3: 25 Abandoned Carts with RevenueOpportunities...")
    for idx in range(25):
        cust = customer_users[idx % len(customer_users)]
        cart = Cart.objects.create(
            user=cust,
            session_id=f"sess_abandoned_{idx}_{uuid.uuid4().hex[:8]}",
            actor_type="human",
        )
        cart_products = random.sample(all_products, random.randint(1, 3))
        cart_total = Decimal("0.00")
        for cp in cart_products:
            qty = random.randint(1, 2)
            CartItem.objects.create(cart=cart, product=cp, quantity=qty)
            cart_total += cp.price * qty

        primary_prod = cart_products[0]
        RevenueOpportunity.objects.create(
            product=primary_prod,
            opportunity_type="abandoned_cart",
            score=Decimal("0.85"),
            expected_revenue_impact=cart_total,
            reason_codes=[
                "HIGH_CART_VALUE",
                "EXIT_INTENT_DETECTED",
                "INVENTORY_RESERVATION_ACTIVE"
            ],
            explanation=(
                f"Customer {cust.email} abandoned a cart worth ₹{cart_total:,.2f} at payment gateway checkout. "
                f"Autonomous agent scheduled exit incentive: Free express delivery + 5% limited-time voucher."
            ),
        )

    print(f"[!] Pattern 3 seeded: 25 abandoned carts with RevenueOpportunity records.")

    # 10. Pattern 7: Failed Subscription Renewals
    print("\n[+] Creating Pattern 7: Failed Subscription Renewals in AgentPaymentAuthorization...")
    for idx, cust in enumerate(customer_users[:3]):
        auth = AgentPaymentAuthorization.objects.create(
            user=cust,
            agent=agent_obj,
            max_transaction_amount=Decimal("5000.00") if idx == 0 else Decimal("10000.00"),
            daily_limit=Decimal("10000.00"),
            monthly_limit=Decimal("50000.00"),
            used_today=Decimal("10000.00") if idx == 1 else Decimal("1500.00"),
            used_this_month=Decimal("42000.00"),
            status=AgentPaymentAuthorization.AuthStatus.ACTIVE if idx != 2 else AgentPaymentAuthorization.AuthStatus.PAUSED,
        )

        # Create Ledger entries (7 failed renewals)
        fail_reasons = [
            ("DAILY_LIMIT_EXCEEDED", "Daily pre-authorization ceiling ₹10,000 reached"),
            ("EXPIRED_CARD_TOKEN", "Underlying bank card mandate token expired"),
            ("MERCHANT_BLOCKED", "Merchant category restricted by user authorization policy"),
        ]
        for l_idx in range(random.randint(2, 3)):
            r_code, r_text = fail_reasons[(idx + l_idx) % len(fail_reasons)]
            AgentAuthorizationLedger.objects.create(
                authorization=auth,
                idempotency_key=f"auth_ledger_fail_{idx}_{l_idx}_{uuid.uuid4().hex[:8]}",
                amount=Decimal("3499.00"),
                merchant="TechVista Electronics",
                category="Electronics",
                decision="FAILED",
                reason=f"{r_code}: {r_text}",
                before_today=auth.used_today,
                after_today=auth.used_today,
                before_month=auth.used_this_month,
                after_month=auth.used_this_month,
            )

        # Also add a successful renewal for visual contrast
        AgentAuthorizationLedger.objects.create(
            authorization=auth,
            idempotency_key=f"auth_ledger_ok_{idx}_{uuid.uuid4().hex[:8]}",
            amount=Decimal("999.00"),
            merchant="TechVista Electronics",
            category="Electronics",
            decision="APPROVED",
            reason="Pre-authorization within limits",
            before_today=Decimal("0.00"),
            after_today=Decimal("999.00"),
            before_month=Decimal("20000.00"),
            after_month=Decimal("20999.00"),
        )

    print("[!] Pattern 7 seeded: AgentPaymentAuthorizations and failed renewal ledger entries.")

    # 11. Marketing Campaigns Linked to Sellers & Customer Segments
    print("\n[+] Seeding Campaigns linked to Sellers and Customer Segments...")
    campaigns_data = [
        {
            "name": "TechVista Mega Tech Carnival",
            "campaign_type": "Electronics Festival",
            "discount_type": "percentage",
            "discount_value": Decimal("15.00"),
            "max_discount": Decimal("5000.00"),
            "budget_limit": Decimal("100000.00"),
            "current_spend": Decimal("34200.00"),
            "segments": ["high_value", "laptops_buyers"],
            "status": "active",
        },
        {
            "name": "StyleCraft Festive Wardrobe Flash",
            "campaign_type": "Seasonal Flash Sale",
            "discount_type": "percentage",
            "discount_value": Decimal("20.00"),
            "max_discount": Decimal("2000.00"),
            "budget_limit": Decimal("50000.00"),
            "current_spend": Decimal("18500.00"),
            "segments": ["fashion_repeat", "cart_abandoners"],
            "status": "active",
        },
        {
            "name": "AudioLuxe Premium Sound Wave",
            "campaign_type": "Audio Category Boost",
            "discount_type": "percentage",
            "discount_value": Decimal("12.00"),
            "max_discount": Decimal("3000.00"),
            "budget_limit": Decimal("40000.00"),
            "current_spend": Decimal("12800.00"),
            "segments": ["audio_enthusiasts"],
            "status": "active",
        },
        {
            "name": "HomeEssentials Smart Living Expo",
            "campaign_type": "Home Renovation",
            "discount_type": "percentage",
            "discount_value": Decimal("18.00"),
            "max_discount": Decimal("4500.00"),
            "budget_limit": Decimal("75000.00"),
            "current_spend": Decimal("29100.00"),
            "segments": ["home_upgraders", "high_value"],
            "status": "active",
        },
        {
            "name": "Sinha Sports Velocity Sprint",
            "campaign_type": "Fitness & Sneaker Surge",
            "discount_type": "fixed",
            "discount_value": Decimal("750.00"),
            "max_discount": Decimal("750.00"),
            "budget_limit": Decimal("60000.00"),
            "current_spend": Decimal("41250.00"),
            "segments": ["fitness_seekers"],
            "status": "active",
        },
        {
            "name": "Joshi Jewels Elegance Fest",
            "campaign_type": "Festive Gold & Diamond",
            "discount_type": "percentage",
            "discount_value": Decimal("10.00"),
            "max_discount": Decimal("10000.00"),
            "budget_limit": Decimal("80000.00"),
            "current_spend": Decimal("52000.00"),
            "segments": ["luxury_buyers"],
            "status": "active",
        },
    ]

    for cdata in campaigns_data:
        Campaign.objects.get_or_create(
            name=cdata["name"],
            defaults={
                "campaign_type": cdata["campaign_type"],
                "discount_type": cdata["discount_type"],
                "discount_value": cdata["discount_value"],
                "max_discount": cdata["max_discount"],
                "budget_limit": cdata["budget_limit"],
                "current_spend": cdata["current_spend"],
                "auto_pause_at_budget": True,
                "segments": cdata["segments"],
                "status": cdata["status"],
                "active": True,
            }
        )

    # 12. Seed 25+ Product Relationships
    print("[+] Seeding 25+ Product Relationships...")
    relationships_to_seed = [
        ("frequently_bought_together", 0.95),
        ("complementary", 0.90),
        ("accessory_for", 0.88),
        ("upgrade_to", 0.85),
        ("alternative_to", 0.80),
    ]

    count_rels = 0
    for idx in range(30):
        src = all_products[idx % len(all_products)]
        tgt = all_products[(idx + 3) % len(all_products)]
        if src.id == tgt.id:
            continue
        rel_type, conf = relationships_to_seed[idx % len(relationships_to_seed)]
        ProductRelationship.objects.get_or_create(
            source_product=src,
            target_product=tgt,
            relationship_type=rel_type,
            defaults={
                "source": "autonomous_catalog_agent",
                "confidence": Decimal(str(conf)),
                "merchant_defined": False,
            }
        )
        count_rels += 1

    print(f"[OK] Seeded {count_rels} ProductRelationships.")

    # FINAL VERIFICATION & ASSERTIONS
    print("\n=========================================================")
    print("FINAL DATABASE VERIFICATION & AUDIT:")
    print("=========================================================")
    actual_orders = Order.objects.count()
    actual_payments = Payment.objects.count()
    actual_refunds = Refund.objects.count()
    actual_invoices = BusinessInvoice.objects.count()
    actual_payouts = Payout.objects.count()
    actual_settlements = Settlement.objects.count()

    print(f"  - Orders:      {actual_orders:4d}  (Target: 290) -> {'PASS [OK]' if actual_orders == 290 else 'FAIL [X]'}")
    print(f"  - Payments:    {actual_payments:4d}  (Target: 350) -> {'PASS [OK]' if actual_payments == 350 else 'FAIL [X]'}")
    print(f"  - Refunds:     {actual_refunds:4d}  (Target:  50) -> {'PASS [OK]' if actual_refunds == 50 else 'FAIL [X]'}")
    print(f"  - Invoices:    {actual_invoices:4d}  (Target:  50) -> {'PASS [OK]' if actual_invoices == 50 else 'FAIL [X]'}")
    print(f"  - Payouts:     {actual_payouts:4d}  (Target:  20) -> {'PASS [OK]' if actual_payouts == 20 else 'FAIL [X]'}")
    print(f"  - Settlements: {actual_settlements:4d}  (Target:  60) -> {'PASS [OK]' if actual_settlements == 60 else 'FAIL [X]'}")
    print("=========================================================")

    assert actual_orders == 290, f"Expected 290 orders, got {actual_orders}"
    assert actual_payments == 350, f"Expected 350 payments, got {actual_payments}"
    assert actual_refunds == 50, f"Expected 50 refunds, got {actual_refunds}"
    assert actual_invoices == 50, f"Expected 50 invoices, got {actual_invoices}"
    assert actual_payouts == 20, f"Expected 20 payouts, got {actual_payouts}"
    assert actual_settlements == 60, f"Expected 60 settlements, got {actual_settlements}"

    print("[SUCCESS] All 6 targets achieved exactly with zero data loss!")


if __name__ == "__main__":
    seed_demo_dataset()
