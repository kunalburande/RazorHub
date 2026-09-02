#!/usr/bin/env python
"""
RazorHub Database Seeding Script — Phase 1 & 2
Phase 1: Categories & Users (Admin, Seller, Customer)
Phase 2: Seed 64 products from frontend seller data
"""
import os
import sys
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from users.models import User, CustomerProfile
from sellers.models import SellerProfile, Store
from products.models import Product, Category, Brand, ProductImage, Inventory
from crm.models import CustomerRecord, SellerRecord, ActivityLog

# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: Categories & Users
# ═══════════════════════════════════════════════════════════════════════

CATEGORIES = [
    {"name": "Electronics", "slug": "electronics", "description": "Headphones, monitors, keyboards, speakers, power banks", "order": 1},
    {"name": "Fashion", "slug": "fashion", "description": "General fashion items", "order": 2},
    {"name": "Laptops", "slug": "laptops", "description": "MacBook, Dell XPS, Lenovo, HP gaming desktops", "order": 3},
    {"name": "Mobiles", "slug": "mobiles", "description": "Phones, chargers, cases, mobile accessories", "order": 4},
    {"name": "Appliances", "slug": "appliances", "description": "Air fryers, blenders, rice cookers, vacuum cleaners", "order": 5},
    {"name": "Jewellery & Accessories", "slug": "jewellery-accessories", "description": "Watches, sunglasses, bags, wallets, rings, necklaces", "order": 6},
    {"name": "Men's Clothing", "slug": "mens-clothing", "description": "Bomber jackets, blazers, shirts, t-shirts for men", "order": 7},
    {"name": "Women's Clothing", "slug": "womens-clothing", "description": "Dresses, hoodies, athletic wear for women", "order": 8},
    {"name": "Groceries", "slug": "groceries", "description": "Rice, oil, eggs, noodles, bread, milk, atta", "order": 9},
    {"name": "Books", "slug": "books", "description": "Programming, novels, exam prep, art books", "order": 10},
    {"name": "Photography", "slug": "photography", "description": "Cameras, lenses, drones, tripods, flash", "order": 11},
    {"name": "Furniture", "slug": "furniture", "description": "Sofas, chairs, desks, tables, credenzas", "order": 12},
    {"name": "Sneakers", "slug": "sneakers", "description": "High-tops, low-tops, trainers, skate shoes", "order": 13},
    {"name": "Automotive", "slug": "automotive", "description": "Cars, car accessories, dash cams, tire inflators", "order": 14},
    {"name": "Sports & Fitness", "slug": "sports-fitness", "description": "Yoga mats, dumbbells, resistance bands, balls", "order": 15},
    {"name": "Gaming", "slug": "gaming", "description": "Consoles, controllers, VR headsets, gaming chairs", "order": 16},
    {"name": "Stationery", "slug": "stationery", "description": "Pens, notebooks, calculators, markers", "order": 17},
    {"name": "Pets", "slug": "pets", "description": "Dog food, cat food, grooming, toys, bowls", "order": 18},
    {"name": "Audio & Sound", "slug": "audio-sound", "description": "Speakers, headphones, earbuds, soundbars", "order": 19},
    {"name": "Home & Kitchen", "slug": "home-kitchen", "description": "Kitchen storage, LED lights, curtains, bedsheets", "order": 20},
    {"name": "Eco & Sustainable", "slug": "eco-sustainable", "description": "Bamboo products, reusable items, solar, compost", "order": 21},
]

ADMINS = [
    {"first_name": "Priya", "last_name": "Sharma", "email": "priya.sharma@razorhub.com", "username": "priya.sharma", "password": "Razor@Admin01"},
    {"first_name": "Rahul", "last_name": "Verma", "email": "rahul.verma@razorhub.com", "username": "rahul.verma", "password": "Razor@Admin02"},
    {"first_name": "Vikram", "last_name": "Reddy", "email": "vikram.reddy@razorhub.com", "username": "vikram.reddy", "password": "Razor@Admin03"},
]

SELLERS = [
    {"first_name": "Ananya", "last_name": "Gupta", "email": "ananya.gupta@razorhub.com", "username": "ananya.gupta", "password": "Razor@Seller01",
     "business_name": "Ananya Electronics Hub", "store_name": "Ananya Electronics Hub",
     "store_desc": "Your one-stop shop for premium electronics, laptops, and audio gear.",
     "store_logo": "https://ui-avatars.com/api/?name=AEH&background=6366f1&color=fff&size=256"},
    {"first_name": "Amit", "last_name": "Singh", "email": "amit.singh@razorhub.com", "username": "amit.singh", "password": "Razor@Seller02",
     "business_name": "Amit Fashion House", "store_name": "Amit Fashion House",
     "store_desc": "Curated luxury fashion for men and women.",
     "store_logo": "https://ui-avatars.com/api/?name=AFH&background=ec4899&color=fff&size=256"},
    {"first_name": "Kavya", "last_name": "Iyer", "email": "kavya.iyer@razorhub.com", "username": "kavya.iyer", "password": "Razor@Seller03",
     "business_name": "Kavya Photo Studio", "store_name": "Kavya Photo Studio",
     "store_desc": "Professional-grade cameras, lenses, and photography equipment.",
     "store_logo": "https://ui-avatars.com/api/?name=KPS&background=f59e0b&color=fff&size=256"},
    {"first_name": "Isha", "last_name": "Banerjee", "email": "isha.banerjee@razorhub.com", "username": "isha.banerjee", "password": "Razor@Seller04",
     "business_name": "Isha Home & Living", "store_name": "Isha Home & Living",
     "store_desc": "Premium furniture, appliances, and home essentials.",
     "store_logo": "https://ui-avatars.com/api/?name=IHL&background=10b981&color=fff&size=256"},
    {"first_name": "Ramesh", "last_name": "Sinha", "email": "ramesh.sinha@razorhub.com", "username": "ramesh.sinha", "password": "Razor@Seller05",
     "business_name": "Sinha Sports & Sneakers", "store_name": "Sinha Sports & Sneakers",
     "store_desc": "Top sneakers, automotive parts, and sports gear.",
     "store_logo": "https://ui-avatars.com/api/?name=SSS&background=ef4444&color=fff&size=256"},
    {"first_name": "Saanvi", "last_name": "Joshi", "email": "saanvi.joshi@razorhub.com", "username": "saanvi.joshi", "password": "Razor@Seller06",
     "business_name": "Joshi Jewels & Accessories", "store_name": "Joshi Jewels & Accessories",
     "store_desc": "Handcrafted jewellery, luxury watches, and designer accessories.",
     "store_logo": "https://ui-avatars.com/api/?name=JJA&background=8b5cf6&color=fff&size=256"},
    {"first_name": "Deepak", "last_name": "Tiwari", "email": "deepak.tiwari@razorhub.com", "username": "deepak.tiwari", "password": "Razor@Seller07",
     "business_name": "Deepak Grocery & Books", "store_name": "Deepak Grocery & Books",
     "store_desc": "Fresh groceries, bestselling books, and stationery supplies.",
     "store_logo": "https://ui-avatars.com/api/?name=DGB&background=06b6d4&color=fff&size=256"},
]

CUSTOMERS = [
    {"first_name": "Sneha", "last_name": "Patel", "email": "sneha.patel@razorhub.com", "username": "sneha.patel", "password": "Razor@Cust01"},
    {"first_name": "Rohit", "last_name": "Das", "email": "rohit.das@razorhub.com", "username": "rohit.das", "password": "Razor@Cust02"},
    {"first_name": "Neha", "last_name": "Bose", "email": "neha.bose@razorhub.com", "username": "neha.bose", "password": "Razor@Cust03"},
    {"first_name": "Suresh", "last_name": "Chatterjee", "email": "suresh.chatterjee@razorhub.com", "username": "suresh.chatterjee", "password": "Razor@Cust04"},
    {"first_name": "Pooja", "last_name": "Mishra", "email": "pooja.mishra@razorhub.com", "username": "pooja.mishra", "password": "Razor@Cust05"},
    {"first_name": "Vikram", "last_name": "Mehta", "email": "vikram.mehta@razorhub.com", "username": "vikram.mehta", "password": "Razor@Cust06"},
    {"first_name": "Riya", "last_name": "Pandey", "email": "riya.pandey@razorhub.com", "username": "riya.pandey", "password": "Razor@Cust07"},
    {"first_name": "Manoj", "last_name": "Yadav", "email": "manoj.yadav@razorhub.com", "username": "manoj.yadav", "password": "Razor@Cust08"},
    {"first_name": "Ajay", "last_name": "Kulkarni", "email": "ajay.kulkarni@razorhub.com", "username": "ajay.kulkarni", "password": "Razor@Cust09"},
    {"first_name": "Diya", "last_name": "Deshpande", "email": "diya.deshpande@razorhub.com", "username": "diya.deshpande", "password": "Razor@Cust10"},
]

# Category mapping: index.ts category name -> our DB category slug -> seller store index
CATEGORY_TO_STORE = {
    "Electronics": 0, "Clothes": 1, "Photography": 2, "Furniture": 3,
    "Sneakers": 4, "Automotive": 4, "Accessories": 5,
}
CATEGORY_REMAP = {
    "Electronics": "electronics", "Clothes": "mens-clothing", "Photography": "photography",
    "Furniture": "furniture", "Sneakers": "sneakers", "Automotive": "automotive",
    "Accessories": "jewellery-accessories",
}

PRODUCTS_FROM_INDEX = [
    # ============== ELECTRONICS (10) ==============
    {"title": "Sony WH-1000XM5 Noise Canceling Headphones", "description": "Industry-leading noise cancellation with dual processors. Crystal clear hands-free calling with 4 beamforming microphones. Up to 30 hours battery life with quick charging.", "imageURL": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80", "price": "399", "colors": ["#121212", "#C0C0C0", "#13005A"], "stock": 42, "sku": "SKU-ELEC-001", "rating": 4.8, "category": "Electronics"},
    {"title": "Apple MacBook Pro 16-inch (M3 Max)", "description": "Empowered by the M3 Max chip with a 16-core CPU and 40-core GPU. Liquid Retina XDR display with up to 22 hours of battery life.", "imageURL": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=800&q=80", "price": "2499", "colors": ["#121212", "#C0C0C0"], "stock": 18, "sku": "SKU-ELEC-002", "rating": 4.9, "category": "Electronics"},
    {"title": "iPad Pro 12.9-inch M2 Liquid Retina XDR", "description": "Astonishing performance with M2 chip, ProRes video capture, and ultra-fast Wi-Fi 6E.", "imageURL": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=800&q=80", "price": "1099", "colors": ["#121212", "#C0C0C0"], "stock": 31, "sku": "SKU-ELEC-003", "rating": 4.7, "category": "Electronics"},
    {"title": "Samsung Odyssey OLED G9 Curved Gaming Monitor", "description": "49-inch Dual QHD curved gaming monitor with 240Hz refresh rate and 0.03ms response time.", "imageURL": "https://i.pinimg.com/1200x/77/75/74/7775746fe3b619b170785763aaf8738e.jpg", "price": "1599", "colors": ["#121212"], "stock": 0, "sku": "SKU-ELEC-004", "rating": 4.8, "category": "Electronics"},
    {"title": "Logitech MX Master 3S Ergonomic Wireless Mouse", "description": "Quiet Click technology with 8000 DPI track-anywhere sensor. MagSpeed electromagnetic scrolling.", "imageURL": "https://i.pinimg.com/736x/e4/4b/d9/e44bd94fcae7ea3bc142c91514b08cc9.jpg", "price": "320", "colors": ["#121212", "#C0C0C0"], "stock": 65, "sku": "SKU-ELEC-005", "rating": 4.6, "category": "Electronics"},
    {"title": "Keychron Q1 Pro Wireless Mechanical Keyboard", "description": "75% layout QMK/VIA custom wireless mechanical keyboard with full aluminum body.", "imageURL": "https://i.pinimg.com/736x/73/e6/bf/73e6bfe98042ee8e09e8c69f71997b5c.jpg", "price": "420", "colors": ["#121212", "#2563eb", "#6F7174"], "stock": 28, "sku": "SKU-ELEC-006", "rating": 4.7, "category": "Electronics"},
    {"title": "Dell UltraSharp 32 4K USB-C Hub Monitor", "description": "IPS Black panel with 2000:1 contrast ratio, 98% DCI-P3 color gamut, and 90W power delivery.", "imageURL": "https://i.pinimg.com/736x/74/a7/77/74a77702d17af7814ba894537f60d15a.jpg", "price": "899", "colors": ["#C0C0C0", "#0B0C0A"], "stock": 9, "sku": "SKU-ELEC-007", "rating": 4.5, "category": "Electronics"},
    {"title": "Sonos Era 300 Smart Speaker | Spatial Audio", "description": "Revolutionary spatial audio speaker with 6 drivers. Dolby Atmos support, Bluetooth 5.0, WiFi 6.", "imageURL": "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=800&q=80", "price": "449", "colors": ["#121212", "#00383A"], "stock": 22, "sku": "SKU-ELEC-008", "rating": 4.8, "category": "Electronics"},
    {"title": "Anker Prime 20,000mAh 200W Power Bank", "description": "High-capacity portable charger with smart digital display and dual 100W USB-C fast charging outputs.", "imageURL": "https://i.pinimg.com/1200x/be/1b/91/be1b9122836e39d3b963aa5c7b14a230.jpg", "price": "310", "colors": ["#121212"], "stock": 50, "sku": "SKU-ELEC-009", "rating": 4.9, "category": "Electronics"},
    {"title": "Bose QuietComfort Ultra Wireless Earbuds", "description": "Immersive spatial audio with CustomTune sound calibration. World-class active noise cancellation.", "imageURL": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=800&q=80", "price": "349", "colors": ["#121212", "#C0C0C0"], "stock": 35, "sku": "SKU-ELEC-010", "rating": 4.6, "category": "Electronics"},
    # ============== CLOTHES (10) ==============
    {"title": "Premium Leather Bomber Jacket", "description": "Crafted from genuine full-grain lambskin leather with a buttery soft feel.", "imageURL": "https://i.pinimg.com/736x/b5/4a/23/b54a232498cf4827e824cad8e83ae459.jpg", "price": "480", "colors": ["#3C2A21", "#121212", "#820000"], "stock": 24, "sku": "SKU-CLOT-001", "rating": 4.8, "category": "Clothes"},
    {"title": "Tailored Italian Wool Blazer", "description": "Structured single-breasted blazer made from 100% fine Italian virgin wool.", "imageURL": "https://i.pinimg.com/736x/86/da/2e/86da2ee5c5bc3de6447393da0a7d844c.jpg", "price": "390", "colors": ["#121212", "#2563eb"], "stock": 0, "sku": "SKU-CLOT-002", "rating": 4.7, "category": "Clothes"},
    {"title": "Minimalist Organic Cotton Heavyweight Hoodie", "description": "Heavy 450gsm organic French terry cotton hoodie with double-lined hood.", "imageURL": "https://i.pinimg.com/1200x/d4/b0/1c/d4b01c4e7ae28fa2e8720f209024245b.jpg", "price": "95", "colors": ["#C0C0C0", "#121212", "#3C2A21"], "stock": 80, "sku": "SKU-CLOT-003", "rating": 4.6, "category": "Clothes"},
    {"title": "Japanese Selvedge Raw Denim Jeans", "description": "14oz Kurabo mill selvedge denim crafted in Okayama, Japan.", "imageURL": "https://i.pinimg.com/736x/e7/2a/7f/e72a7f8dff94b9b0e40a442448bf4e2a.jpg", "price": "185", "colors": ["#4F6B82", "#323240", "#121212"], "stock": 36, "sku": "SKU-CLOT-004", "rating": 4.8, "category": "Clothes"},
    {"title": "100% Mongolian Cashmere Crewneck Sweater", "description": "Ultra-soft grade-A Mongolian cashmere knitted in a lightweight 12-gauge structure.", "imageURL": "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?auto=format&fit=crop&w=800&q=80", "price": "280", "colors": ["#EEE7ED", "#3C2A21", "#121212"], "stock": 20, "sku": "SKU-CLOT-005", "rating": 4.9, "category": "Clothes"},
    {"title": "Waterproof Technical Trench Coat", "description": "3-layer breathable GORE-TEX fabric with fully taped seams.", "imageURL": "https://i.pinimg.com/736x/e3/f9/da/e3f9da3fb1a5c376146ccf2a70e68eb6.jpg", "price": "340", "colors": ["#121212", "#3C2A21"], "stock": 12, "sku": "SKU-CLOT-006", "rating": 4.5, "category": "Clothes"},
    {"title": "Classic Merino Wool Turtleneck Knitwear", "description": "Extra-fine Australian merino wool offering supreme softness and subtle lustre.", "imageURL": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?auto=format&fit=crop&w=800&q=80", "price": "160", "colors": ["#121212", "#C0C0C0", "#820000"], "stock": 45, "sku": "SKU-CLOT-007", "rating": 4.6, "category": "Clothes"},
    {"title": "Slim-Fit Poplin Dress Shirt", "description": "2-ply 100% Egyptian Giza cotton poplin with spread collar and mother-of-pearl buttons.", "imageURL": "https://i.pinimg.com/736x/60/eb/db/60ebdbbc9433bb04ca293d1e6f04ee62.jpg", "price": "110", "colors": ["#9BBEDA", "#2563eb"], "stock": 55, "sku": "SKU-CLOT-008", "rating": 4.4, "category": "Clothes"},
    {"title": "Over-Sized Vintage Washed Graphic T-Shirt", "description": "Heavyweight 240gsm combed cotton with enzyme wash for vintage faded look.", "imageURL": "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?auto=format&fit=crop&w=800&q=80", "price": "65", "colors": ["#121212", "#C0C0C0"], "stock": 90, "sku": "SKU-CLOT-009", "rating": 4.7, "category": "Clothes"},
    {"title": "Luxury Modest Linen Collection", "description": "Floor-length bias-cut evening gown in 100% mulberry silk satin.", "imageURL": "https://i.pinimg.com/736x/56/71/f7/5671f7769c57070cf7378e957cd6c3de.jpg", "price": "490", "colors": ["#ECE7E3", "#C09068", "#84491F"], "stock": 8, "sku": "SKU-CLOT-010", "rating": 4.9, "category": "Clothes"},
    # ============== PHOTOGRAPHY (8) ==============
    {"title": "Canon EOS R6 Mark II Mirrorless Camera", "description": "Full-frame mirrorless camera with 24.2MP sensor and DIGIC X processor.", "imageURL": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=80", "price": "2499", "colors": ["#121212"], "stock": 10, "sku": "SKU-PHOT-001", "rating": 4.9, "category": "Photography"},
    {"title": "Fujifilm X100V Premium Compact Camera", "description": "Iconic street camera featuring a 26.1MP X-Trans CMOS 4 sensor.", "imageURL": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=800&q=80", "price": "1399", "colors": ["#C0C0C0", "#121212"], "stock": 14, "sku": "SKU-PHOT-002", "rating": 4.8, "category": "Photography"},
    {"title": "Sony FE 24-70mm f/2.8 GM II Lens", "description": "The world's lightest standard zoom f/2.8 lens.", "imageURL": "https://images.unsplash.com/photo-1617005082133-548c4dd27f35?auto=format&fit=crop&w=800&q=80", "price": "2299", "colors": ["#121212"], "stock": 0, "sku": "SKU-PHOT-003", "rating": 4.9, "category": "Photography"},
    {"title": "DJI Mavic 3 Pro Cine Quadcopter Drone", "description": "Triple-camera system featuring Hasselblad 4/3 CMOS sensor.", "imageURL": "https://images.unsplash.com/photo-1527977966376-1c8408f9f108?auto=format&fit=crop&w=800&q=80", "price": "2899", "colors": ["#121212", "#C0C0C0"], "stock": 6, "sku": "SKU-PHOT-004", "rating": 4.8, "category": "Photography"},
    {"title": "Leica M11 Rangefinder Camera Body", "description": "60MP BSI CMOS full-frame sensor with Triple Resolution Technology.", "imageURL": "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=800&q=80", "price": "2950", "colors": ["#121212", "#C0C0C0"], "stock": 4, "sku": "SKU-PHOT-005", "rating": 4.9, "category": "Photography"},
    {"title": "Sigma 85mm f/1.4 DG DN Art Lens for E-Mount", "description": "Ultimate portrait lens delivering breathtaking bokeh.", "imageURL": "https://i.pinimg.com/1200x/c6/b4/1a/c6b41a13c2eaabf7a1dbebaf6bd0e940.jpg", "price": "1199", "colors": ["#121212"], "stock": 18, "sku": "SKU-PHOT-006", "rating": 4.7, "category": "Photography"},
    {"title": "Profoto B10X Plus OCF Flash & Monolight", "description": "500Ws powerful battery-powered studio flash.", "imageURL": "https://images.unsplash.com/photo-1520390138845-fd2d229dd553?auto=format&fit=crop&w=800&q=80", "price": "2295", "colors": ["#121212"], "stock": 7, "sku": "SKU-PHOT-007", "rating": 4.6, "category": "Photography"},
    {"title": "Peak Design Carbon Fiber Travel Tripod", "description": "Ultra-compact carbon fiber tripod that packs down to the diameter of a water bottle.", "imageURL": "https://i.pinimg.com/1200x/01/16/9b/01169b0d7d8827cffc460559bac9bbe5.jpg", "price": "649", "colors": ["#121212"], "stock": 25, "sku": "SKU-PHOT-008", "rating": 4.8, "category": "Photography"},
    # ============== FURNITURE (8) ==============
    {"title": "Scandinavian Modern Linen Sofa", "description": "Minimalist three-seater sofa with solid oak legs and premium linen upholstery.", "imageURL": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=800&q=80", "price": "1299", "colors": ["#84D2C5", "#3C2A21", "#C0C0C0"], "stock": 12, "sku": "SKU-FURN-001", "rating": 4.7, "category": "Furniture"},
    {"title": "Eames Lounge Chair & Ottoman Replica", "description": "Mid-century modern design icon in top-grain aniline leather.", "imageURL": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=800&q=80", "price": "2100", "colors": ["#121212", "#3C2A21", "#EFC849"], "stock": 9, "sku": "SKU-FURN-002", "rating": 4.9, "category": "Furniture"},
    {"title": "Solid Walnut Ergonomic Executive Desk", "description": "Hand-finished solid American walnut standing desk.", "imageURL": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=800&q=80", "price": "1850", "colors": ["#3C2A21", "#D0D0D0"], "stock": 14, "sku": "SKU-FURN-003", "rating": 4.8, "category": "Furniture"},
    {"title": "Handcrafted Live-Edge Oak Dining Table", "description": "10-seat natural live-edge European white oak dining table.", "imageURL": "https://images.unsplash.com/photo-1615066390971-03e4e1c36ddf?auto=format&fit=crop&w=800&q=80", "price": "4500", "colors": ["#3C2A21", "#121212", "#6F7174"], "stock": 0, "sku": "SKU-FURN-004", "rating": 4.9, "category": "Furniture"},
    {"title": "Herman Miller Aeron Ergonomic Chair", "description": "Fully adjustable ergonomic office chair with Pellicle 8Z suspension.", "imageURL": "https://i.pinimg.com/1200x/4d/df/f6/4ddff6507a9b14896a291bd571fb5a76.jpg", "price": "1495", "colors": ["#121212", "#C0C0C0"], "stock": 20, "sku": "SKU-FURN-005", "rating": 4.9, "category": "Furniture"},
    {"title": "Modular Velvet Sectional Sofa | Navy", "description": "5-piece configurable sectional sofa in stain-resistant performance velvet.", "imageURL": "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&w=800&q=80", "price": "3200", "colors": ["#938B8B", "#3C2A21"], "stock": 6, "sku": "SKU-FURN-006", "rating": 4.7, "category": "Furniture"},
    {"title": "Minimalist Floating Teak Credenza", "description": "Sustainably sourced plantation teak sideboard.", "imageURL": "https://images.unsplash.com/photo-1538688525198-9b88f6f53126?auto=format&fit=crop&w=800&q=80", "price": "1650", "colors": ["#3C2A21", "#DCB493"], "stock": 11, "sku": "SKU-FURN-007", "rating": 4.6, "category": "Furniture"},
    {"title": "Architectural Marble Top Coffee Table", "description": "Italian Carrara white marble tabletop supported by geometric black steel tripod legs.", "imageURL": "https://images.unsplash.com/photo-1533779283484-8ad4940aa3a8?auto=format&fit=crop&w=800&q=80", "price": "780", "colors": ["#C0C0C0", "#121212"], "stock": 16, "sku": "SKU-FURN-008", "rating": 4.8, "category": "Furniture"},
    # ============== SNEAKERS (8) ==============
    {"title": "Neon Pulse High-Top Sneakers | Limited Edition", "description": "Futuristic high-top sneakers with bold LED-inspired cyan details.", "imageURL": "https://i.pinimg.com/1200x/69/7e/93/697e93eb1a36e81230adffb95744a273.jpg", "price": "350", "colors": ["#06b6d4", "#121212", "#0138ED"], "stock": 30, "sku": "SKU-SNEA-001", "rating": 4.8, "category": "Sneakers"},
    {"title": "Retro Runner OG Colorway Sneakers", "description": "Classic 1980s silhouette with suede overlays and nylon underlays.", "imageURL": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80", "price": "160", "colors": ["#FF6E31", "#2563eb", "#C00019"], "stock": 45, "sku": "SKU-SNEA-002", "rating": 4.6, "category": "Sneakers"},
    {"title": "Air Tech Basketball Performance Shoes", "description": "Engineered knit upper with multi-directional traction pattern.", "imageURL": "https://i.pinimg.com/1200x/33/d6/58/33d6589831aeabcd9f64d17dccd64c93.jpg", "price": "210", "colors": ["#121212", "#8B8F97", "#06b6d4"], "stock": 0, "sku": "SKU-SNEA-003", "rating": 4.7, "category": "Sneakers"},
    {"title": "Minimalist White Italian Leather Low-Tops", "description": "Handcrafted in Tuscany using butter-soft Nappa leather.", "imageURL": "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=800&q=80", "price": "140", "colors": ["#C0C0C0", "#121212", "#BF7C47"], "stock": 50, "sku": "SKU-SNEA-004", "rating": 4.8, "category": "Sneakers"},
    {"title": "Urban Hiker Vibram Sole Trail Sneakers", "description": "Rugged ripstop fabric with waterproof membrane and Vibram Megagrip outsole.", "imageURL": "https://i.pinimg.com/736x/9b/c9/6c/9bc96c4de100f4c0f5e4d2a5e387b485.jpg", "price": "230", "colors": ["#3C2A21", "#121212", "#10b981"], "stock": 19, "sku": "SKU-SNEA-005", "rating": 4.5, "category": "Sneakers"},
    {"title": "Futuristic Carbon Plate Racing Shoes", "description": "Marathon racing shoe with full-length carbon fiber plate.", "imageURL": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=800&q=80", "price": "290", "colors": ["#f43f5e", "#06b6d4"], "stock": 14, "sku": "SKU-SNEA-006", "rating": 4.9, "category": "Sneakers"},
    {"title": "Classic Canvas Skate Sneakers", "description": "12oz heavy canvas upper with reinforced suede toe cap.", "imageURL": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=800&q=80", "price": "110", "colors": ["#121212", "#C0C0C0", "#820000"], "stock": 60, "sku": "SKU-SNEA-007", "rating": 4.6, "category": "Sneakers"},
    {"title": "Knit Slip-On Lightweight Trainer", "description": "Sock-like 3D flyknit construction with elastic collar and memory foam insole.", "imageURL": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=800&q=80", "price": "135", "colors": ["#121212", "#C0C0C0"], "stock": 40, "sku": "SKU-SNEA-008", "rating": 4.7, "category": "Sneakers"},
    # ============== AUTOMOTIVE (10) ==============
    {"title": "Tesla Model S Plaid Sport Edition", "description": "Tri-motor all-wheel drive with 1,020 horsepower.", "imageURL": "https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=800&q=80", "price": "2990", "colors": ["#121212", "#F7F9F9", "#FF0032"], "stock": 3, "sku": "SKU-AUTO-001", "rating": 4.9, "category": "Automotive"},
    {"title": "Porsche 911 Carrera Custom Coupe", "description": "3.0-liter twin-turbo flat-six engine generating 379 hp.", "imageURL": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=800&q=80", "price": "2850", "colors": ["#121212", "#C0C0C0", "#FF6E31"], "stock": 0, "sku": "SKU-AUTO-002", "rating": 4.9, "category": "Automotive"},
    {"title": "BMW M4 Competition Convertible", "description": "M TwinPower Turbo inline 6-cylinder engine producing 503 hp.", "imageURL": "https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=800&q=80", "price": "2600", "colors": ["#D6DEE0", "#121212"], "stock": 4, "sku": "SKU-AUTO-003", "rating": 4.8, "category": "Automotive"},
    {"title": "Chevrolet Camaro SS 2018 - Blue Sports Coupe", "description": "Bold blue finish with 6.2L LT1 V8 engine pumping 455 hp.", "imageURL": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=800&q=80", "price": "1850", "colors": ["#2563eb", "#FF0032", "#121212"], "stock": 5, "sku": "SKU-AUTO-004", "rating": 4.7, "category": "Automotive"},
    {"title": "Ford Mustang GT V8 Fastback Edition", "description": "Iconic 5.0L Coyote V8 engine with active valve performance exhaust.", "imageURL": "https://images.unsplash.com/photo-1584345604476-8ec5e12e42dd?auto=format&fit=crop&w=800&q=80", "price": "1450", "colors": ["#FF0032", "#121212", "#C0C0C0"], "stock": 6, "sku": "SKU-AUTO-005", "rating": 4.8, "category": "Automotive"},
    {"title": "Audi RS e-tron GT Electric Supercar", "description": "800V architecture delivering up to 637 hp with boost launch control.", "imageURL": "https://images.unsplash.com/photo-1614200187524-dc4b892acf16?auto=format&fit=crop&w=800&q=80", "price": "2950", "colors": ["#121212", "#C34038"], "stock": 2, "sku": "SKU-AUTO-006", "rating": 4.9, "category": "Automotive"},
    {"title": "Mercedes-AMG GT R V8 Biturbo", "description": "Handcrafted AMG 4.0L V8 biturbo engine with 577 hp.", "imageURL": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=800&q=80", "price": "2750", "colors": ["#E5AA4B", "#121212"], "stock": 3, "sku": "SKU-AUTO-007", "rating": 4.9, "category": "Automotive"},
    {"title": "Range Rover Sport SV Carbon Edition", "description": "Twin-turbo V8 mild-hybrid engine with 626 hp.", "imageURL": "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=800&q=80", "price": "2400", "colors": ["#121212", "#3C2A21"], "stock": 4, "sku": "SKU-AUTO-008", "rating": 4.8, "category": "Automotive"},
    {"title": "Alfa Romeo Giulia Quadrifoglio", "description": "2.9L twin-turbo V6 engine developed with Ferrari expertise.", "imageURL": "https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?auto=format&fit=crop&w=800&q=80", "price": "1680", "colors": ["#FF0032", "#121212", "#C34038"], "stock": 7, "sku": "SKU-AUTO-009", "rating": 4.7, "category": "Automotive"},
    {"title": "Subaru WRX STI Rally Spec Coupe", "description": "Symmetrical All-Wheel Drive with 2.5L turbocharged BOXER engine.", "imageURL": "https://images.unsplash.com/photo-1621993202323-f438eec934ff?auto=format&fit=crop&w=800&q=80", "price": "980", "colors": ["#2563eb", "#C0C0C0"], "stock": 11, "sku": "SKU-AUTO-010", "rating": 4.6, "category": "Automotive"},
    # ============== ACCESSORIES (10) ==============
    {"title": "Swiss Automatic Chronograph Mechanical Watch", "description": "Swiss-made automatic movement with 48-hour power reserve.", "imageURL": "https://i.pinimg.com/1200x/8b/49/f6/8b49f6aaca9ffa2e72262fc1f2c2c734.jpg", "price": "1850", "colors": ["#C0C0C0", "#121212", "#3C2A21"], "stock": 16, "sku": "SKU-ACCE-001", "rating": 4.9, "category": "Accessories"},
    {"title": "Designer Polarized Titanium Aviator Sunglasses", "description": "Ultra-lightweight Japanese titanium frame with anti-reflective polarized lenses.", "imageURL": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=800&q=80", "price": "240", "colors": ["#C0C0C0", "#121212", "#E3BD9E"], "stock": 35, "sku": "SKU-ACCE-002", "rating": 4.7, "category": "Accessories"},
    {"title": "Italian Full-Grain Leather Executive Briefcase", "description": "Handcrafted in Florence using vegetable-tanned Tuscan leather.", "imageURL": "https://i.pinimg.com/736x/23/06/c2/2306c2d3c152acde77ce49c8b5fab3b5.jpg", "price": "450", "colors": ["#3C2A21", "#121212"], "stock": 22, "sku": "SKU-ACCE-003", "rating": 4.8, "category": "Accessories"},
    {"title": "Minimalist Titanium Smart Fitness Ring", "description": "Waterproof titanium smart ring tracking sleep stages and heart rate.", "imageURL": "https://i.pinimg.com/736x/2b/64/57/2b645756479750ee80bcac30c543abe0.jpg", "price": "299", "colors": ["#121212", "#C0C0C0"], "stock": 40, "sku": "SKU-ACCE-004", "rating": 4.6, "category": "Accessories"},
    {"title": "Handcrafted RFID Slim Leather Cardholder", "description": "Slim bi-fold cardholder with RFID blocking technology.", "imageURL": "https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=800&q=80", "price": "120", "colors": ["#121212", "#3C2A21", "#820000"], "stock": 75, "sku": "SKU-ACCE-005", "rating": 4.7, "category": "Accessories"},
    {"title": "Luxury Cashmere Patterned Scarf", "description": "Hand-woven 100% Mongolian cashmere scarf with fringed edges.", "imageURL": "https://i.pinimg.com/1200x/15/f9/68/15f968b2f4896eb092ea9f44d30907aa.jpg", "price": "195", "colors": ["#3C2A21", "#C0C0C0", "#121212"], "stock": 28, "sku": "SKU-ACCE-006", "rating": 4.8, "category": "Accessories"},
    {"title": "Vintage Cat Painting | Whispers of the Garden", "description": "Timeless artwork featuring a graceful ginger cat and two playful kittens.", "imageURL": "https://images.unsplash.com/photo-1582562124811-c09040d0a901?auto=format&fit=crop&w=800&q=80", "price": "110", "colors": ["#FF6E31", "#121212"], "stock": 85, "sku": "SKU-ACCE-007", "rating": 4.6, "category": "Accessories"},
    {"title": "Ruby Eclipse Pendant Necklace", "description": "Elegant gold necklace with stunning oval-cut ruby centerpiece.", "imageURL": "https://i.pinimg.com/736x/bd/4f/9a/bd4f9aba7e1fbc00f2f1b421790aabc2.jpg", "price": "320", "colors": ["#C0C0C0", "#8D8379"], "stock": 0, "sku": "SKU-ACCE-008", "rating": 4.9, "category": "Accessories"},
    {"title": "Traveler Leather Passport Wallet & Tech Pouch", "description": "Full-grain Horween leather travel wallet with passport sleeve.", "imageURL": "https://i.pinimg.com/736x/4a/17/28/4a1728134dee7ac6e386e40155ab5dd1.jpg", "price": "175", "colors": ["#3C2A21", "#121212"], "stock": 33, "sku": "SKU-ACCE-009", "rating": 4.7, "category": "Accessories"},
    {"title": "Ceramic Minimalist Desk Organizer", "description": "Matte ceramic desk tray for everyday EDC items.", "imageURL": "https://i.pinimg.com/736x/e1/f3/11/e1f31103501107cbc6c34f234cea4810.jpg", "price": "105", "colors": ["#C0C0C0", "#121212"], "stock": 44, "sku": "SKU-ACCE-010", "rating": 4.8, "category": "Accessories"},
]


def seed_categories():
    print("\n" + "=" * 60)
    print("PHASE 1a: Seeding Categories")
    print("=" * 60)
    created = 0
    for cat_data in CATEGORIES:
        cat, was_created = Category.objects.update_or_create(
            slug=cat_data["slug"],
            defaults={"name": cat_data["name"], "description": cat_data["description"], "order": cat_data["order"]}
        )
        if was_created:
            created += 1
            print(f"  + Created: {cat.name}")
        else:
            print(f"  ~ Updated: {cat.name}")
    print(f"\n  Total categories: {Category.objects.count()}")


def seed_admins():
    print("\n" + "=" * 60)
    print("PHASE 1b: Seeding Admin Users")
    print("=" * 60)
    for admin_data in ADMINS:
        if User.objects.filter(email=admin_data["email"]).exists():
            print(f"  - Skipped (exists): {admin_data['email']}")
            continue
        user = User.objects.create_user(
            username=admin_data["username"], email=admin_data["email"],
            password=admin_data["password"], first_name=admin_data["first_name"],
            last_name=admin_data["last_name"], role=User.ROLE_ADMIN,
            is_staff=True, is_superuser=True,
        )
        try:
            CustomerRecord.objects.get_or_create(user=user)
        except Exception:
            pass
        ActivityLog.objects.create(actor=user, verb="registered", target_type="user", target_id=str(user.id), metadata={"role": "admin", "source": "seed"})
        print(f"  + Created admin: {user.email}")


def seed_sellers():
    print("\n" + "=" * 60)
    print("PHASE 1c: Seeding Seller Users + Stores")
    print("=" * 60)
    stores = []
    for seller_data in SELLERS:
        if User.objects.filter(email=seller_data["email"]).exists():
            print(f"  - Skipped (exists): {seller_data['email']}")
            try:
                user = User.objects.get(email=seller_data["email"])
                store = Store.objects.get(seller__user=user)
                stores.append(store)
            except Exception:
                stores.append(None)
            continue
        user = User.objects.create_user(
            username=seller_data["username"], email=seller_data["email"],
            password=seller_data["password"], first_name=seller_data["first_name"],
            last_name=seller_data["last_name"], role=User.ROLE_SELLER,
        )
        sp = SellerProfile.objects.create(user=user, business_name=seller_data["business_name"], status=SellerProfile.STATUS_VERIFIED)
        store = Store.objects.create(seller=sp, name=seller_data["store_name"], description=seller_data["store_desc"], logo_url=seller_data["store_logo"], is_active=True)
        try:
            SellerRecord.objects.get_or_create(seller=sp, defaults={"status": "active"})
        except Exception:
            pass
        ActivityLog.objects.create(actor=user, verb="registered", target_type="user", target_id=str(user.id), metadata={"role": "seller", "source": "seed"})
        stores.append(store)
        print(f"  + Created seller: {user.email} -> Store: {store.name}")
    print(f"\n  Total stores tracked: {len(stores)}")
    return stores


def seed_customers():
    print("\n" + "=" * 60)
    print("PHASE 1d: Seeding Customer Users")
    print("=" * 60)
    for cust_data in CUSTOMERS:
        if User.objects.filter(email=cust_data["email"]).exists():
            print(f"  - Skipped (exists): {cust_data['email']}")
            continue
        user = User.objects.create_user(
            username=cust_data["username"], email=cust_data["email"],
            password=cust_data["password"], first_name=cust_data["first_name"],
            last_name=cust_data["last_name"], role=User.ROLE_CUSTOMER,
        )
        CustomerProfile.objects.create(user=user, full_name=f"{cust_data['first_name']} {cust_data['last_name']}")
        try:
            CustomerRecord.objects.get_or_create(user=user)
        except Exception:
            pass
        ActivityLog.objects.create(actor=user, verb="registered", target_type="user", target_id=str(user.id), metadata={"role": "customer", "source": "seed"})
        print(f"  + Created customer: {user.email}")


def seed_products(stores):
    print("\n" + "=" * 60)
    print("PHASE 2: Seeding 64 Products from index.ts")
    print("=" * 60)
    cat_lookup = {c.slug: c for c in Category.objects.all()}
    created = 0
    skipped = 0
    for p in PRODUCTS_FROM_INDEX:
        if Product.objects.filter(sku=p["sku"]).exists():
            skipped += 1
            continue
        cat_slug = CATEGORY_REMAP.get(p["category"], "electronics")
        category = cat_lookup.get(cat_slug)
        if not category:
            print(f"  ! Category not found: {cat_slug}")
            skipped += 1
            continue
        store_idx = CATEGORY_TO_STORE.get(p["category"], 0)
        store = stores[store_idx] if store_idx < len(stores) and stores[store_idx] else None
        product = Product(
            name=p["title"], description=p["description"], price=Decimal(p["price"]),
            stock=p["stock"], sku=p["sku"], colors=p["colors"],
            rating=Decimal(str(p["rating"])), category=category, store=store,
            is_active=True, is_featured=(p["rating"] >= 4.8),
            delivery_time_estimate="2-5 business days", base_delivery_fee=Decimal("150.00"),
        )
        product.save()
        ProductImage.objects.create(product=product, image_url=p["imageURL"], alt_text=p["title"], is_primary=True, order=0)
        Inventory.objects.create(product=product, sku=p["sku"], quantity=p["stock"], low_stock_threshold=5)
        created += 1
    print(f"\n  Products: {created} created, {skipped} skipped")


def main():
    print("\n" + "=" * 60)
    print("  RazorHub Database Seeding - Phase 1 & 2")
    print("=" * 60)
    seed_categories()
    seed_admins()
    stores = seed_sellers()
    seed_customers()
    seed_products(stores)
    print("\n" + "=" * 60)
    print("  PHASE 1 & 2 COMPLETE!")
    print("=" * 60)
    print(f"  Categories: {Category.objects.count()}")
    print(f"  Users: {User.objects.count()}")
    print(f"  Stores: {Store.objects.count()}")
    print(f"  Products: {Product.objects.count()}")
    print(f"  Images: {ProductImage.objects.count()}")


if __name__ == "__main__":
    main()
