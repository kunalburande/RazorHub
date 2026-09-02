"""
Campaign Intelligence & Orchestration Service for RazorHub Agentic Commerce.

Handles the full promotional campaign lifecycle:
  1. Plan: Recommend data-driven promotions per customer segment
  2. Create: Budget-bounded campaign creation with tracked Razorpay assets
  3. Monitor: Real-time spend tracking and conversion analytics
  4. Optimize: Auto-pause on budget exhaustion and A/B variant adjustments
"""
import uuid
import logging
from decimal import Decimal
from django.utils import timezone
from intelligence.models import Campaign, MerchantConfig
from intelligence.services.commerce_audit import CommerceAuditService
from intelligence.services.razorpay_service import RazorpayService

logger = logging.getLogger(__name__)


class CampaignIntelligenceService:
    @classmethod
    def get_active_campaigns(cls, product=None):
        """Get active, non-paused campaigns within the valid date range."""
        now = timezone.now()
        
        campaigns = Campaign.objects.filter(
            active=True,
            status='active',
        ).filter(
            models_q_start(now) & models_q_end(now)
        )
        
        if product:
            valid_campaigns = []
            for c in campaigns:
                # Check budget cap before applying
                if c.auto_pause_at_budget and c.current_spend >= c.budget_limit:
                    cls.auto_pause_campaign(c, reason="Budget limit reached")
                    continue
                if c.eligible_products.exists():
                    if c.eligible_products.filter(id=product.id).exists():
                        valid_campaigns.append(c)
                else:
                    valid_campaigns.append(c)
            return valid_campaigns
            
        return list(campaigns)

    @classmethod
    def calculate_discount(cls, product, base_price, campaigns=None):
        """Calculate the best discount available for a product."""
        if campaigns is None:
            campaigns = cls.get_active_campaigns(product)
            
        best_discount = Decimal('0.00')
        best_campaign = None
        
        for c in campaigns:
            if c.auto_pause_at_budget and c.current_spend >= c.budget_limit:
                continue

            discount = Decimal('0.00')
            if c.discount_type == 'percentage':
                discount = base_price * (c.discount_value / Decimal('100.0'))
            elif c.discount_type == 'fixed':
                discount = c.discount_value
                
            if c.max_discount and discount > c.max_discount:
                discount = c.max_discount
                
            if discount > best_discount:
                best_discount = discount
                best_campaign = c
                
        return best_discount, best_campaign

    @classmethod
    def create_campaign_from_ai(cls, config: dict, user=None) -> dict:
        """
        Create a budget-bounded promotional campaign with segment-specific Razorpay tracking.
        """
        name = config.get("name", f"AI Campaign {timezone.now().strftime('%b %d')}")
        campaign_type = config.get("campaign_type", "segment_promotion")
        discount_type = config.get("discount_type", "percentage")
        discount_value = Decimal(str(config.get("discount_value", "10.00")))
        max_discount = Decimal(str(config["max_discount"])) if config.get("max_discount") else None
        budget_limit = Decimal(str(config.get("budget_limit", "50000.00")))
        segments = config.get("segments", ["all_customers"])
        eligible_product_ids = config.get("eligible_product_ids", [])
        
        # Verify merchant limits
        merchant_cfg = MerchantConfig.get_solo()
        if discount_type == "percentage" and discount_value > merchant_cfg.max_discount_percent:
            return {
                "success": False,
                "error": f"Discount {discount_value}% exceeds merchant maximum of {merchant_cfg.max_discount_percent}%",
                "graceful": True
            }

        trace_id = str(uuid.uuid4())

        # Create Campaign
        campaign = Campaign.objects.create(
            name=name,
            campaign_type=campaign_type,
            discount_type=discount_type,
            discount_value=discount_value,
            max_discount=max_discount,
            budget_limit=budget_limit,
            current_spend=Decimal("0.00"),
            auto_pause_at_budget=config.get("auto_pause_at_budget", True),
            segments=segments,
            status="active",
            active=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=int(config.get("duration_days", 7)))
        )

        if eligible_product_ids:
            campaign.eligible_products.set(eligible_product_ids)

        # Create Razorpay tracked links for each customer segment
        segment_links = {}
        for seg in segments:
            try:
                plink = RazorpayService.create_payment_link(
                    amount=0,  # dynamic product amount
                    description=f"{name} ({seg})",
                    notes={
                        "campaign_id": str(campaign.id),
                        "segment": seg,
                        "discount_applied": str(discount_value),
                        "bounded_budget": str(budget_limit),
                        "trace_id": trace_id
                    }
                )
                segment_links[seg] = {
                    "payment_link_id": plink["id"],
                    "url": plink.get("short_url", "")
                }
            except Exception as e:
                logger.warning(f"[Campaign] Could not generate link for segment {seg}: {e}")

        # Audit trail logging
        CommerceAuditService.log_campaign_event(
            action="campaign_created",
            campaign_id=campaign.id,
            outcome="success",
            budget_limit=budget_limit,
            current_spend=Decimal("0.00"),
            trace_id=trace_id,
            explainable=f"Created {campaign_type} '{name}' with {discount_value}{'%' if discount_type=='percentage' else ' INR'} off, capped at ₹{budget_limit:,.2f}"
        )

        return {
            "success": True,
            "campaign_id": campaign.id,
            "name": campaign.name,
            "status": campaign.status,
            "budget_limit": float(budget_limit),
            "discount": f"{discount_value}{'%' if discount_type=='percentage' else ' INR'}",
            "segments": segments,
            "segment_links": segment_links,
            "trace_id": trace_id
        }

    @classmethod
    def record_discount_redemption(cls, campaign_id: int, discount_awarded: Decimal):
        """Record discount spend against the campaign budget and auto-pause if exhausted."""
        try:
            campaign = Campaign.objects.get(id=campaign_id)
            campaign.current_spend += discount_awarded
            
            if campaign.auto_pause_at_budget and campaign.current_spend >= campaign.budget_limit:
                campaign.status = 'paused'
                campaign.active = False
                campaign.save(update_fields=['current_spend', 'status', 'active', 'updated_at'])
                
                CommerceAuditService.log_campaign_event(
                    action="campaign_auto_paused",
                    campaign_id=campaign.id,
                    outcome="paused",
                    budget_limit=campaign.budget_limit,
                    current_spend=campaign.current_spend,
                    explainable=f"Campaign {campaign.name} auto-paused: budget limit of ₹{campaign.budget_limit:,.2f} reached."
                )
            else:
                campaign.save(update_fields=['current_spend', 'updated_at'])
        except Campaign.DoesNotExist:
            pass

    @classmethod
    def auto_pause_campaign(cls, campaign: Campaign, reason: str = "Budget limit reached"):
        """Pause a campaign gracefully and log audit trail."""
        campaign.status = 'paused'
        campaign.active = False
        campaign.save(update_fields=['status', 'active', 'updated_at'])
        CommerceAuditService.log_campaign_event(
            action="campaign_auto_paused",
            campaign_id=campaign.id,
            outcome="paused",
            budget_limit=campaign.budget_limit,
            current_spend=campaign.current_spend,
            explainable=f"Campaign {campaign.name} paused: {reason}"
        )

    @classmethod
    def get_campaign_performance(cls, campaign_id: int) -> dict:
        """Fetch real-time analytics for a specific campaign."""
        try:
            campaign = Campaign.objects.get(id=campaign_id)
            budget = float(campaign.budget_limit)
            spend = float(campaign.current_spend)
            remaining = max(budget - spend, 0.0)
            burn_rate = (spend / budget * 100.0) if budget > 0 else 0.0

            return {
                "campaign_id": campaign.id,
                "name": campaign.name,
                "status": campaign.status,
                "budget_limit": budget,
                "current_spend": spend,
                "remaining_budget": remaining,
                "budget_burn_pct": round(burn_rate, 2),
                "segments": campaign.segments,
                "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
                "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
            }
        except Campaign.DoesNotExist:
            return {"error": "Campaign not found"}


def models_q_start(now):
    from django.db.models import Q
    return Q(start_date__isnull=True) | Q(start_date__lte=now)


def models_q_end(now):
    from django.db.models import Q
    return Q(end_date__isnull=True) | Q(end_date__gte=now)

