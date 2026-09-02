from django.core.management.base import BaseCommand
from intelligence.services.product_relationships import ProductRelationshipService
from intelligence.services.revenue_opportunity import RevenueOpportunityService
from intelligence.services.inventory_intelligence import InventoryIntelligenceService

class Command(BaseCommand):
    help = 'Generates intelligence insights and relationships.'

    def handle(self, *args, **options):
        self.stdout.write("Generating frequently bought together relationships...")
        ProductRelationshipService.generate_frequently_bought_together()
        
        self.stdout.write("Analyzing inventory intelligence...")
        InventoryIntelligenceService.analyze_inventory()
        
        self.stdout.write("Analyzing revenue opportunities...")
        RevenueOpportunityService.analyze_all_products()
        
        self.stdout.write(self.style.SUCCESS("Successfully generated intelligence insights."))
