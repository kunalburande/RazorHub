import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Product, Brand, Category
from django.utils.text import slugify

UPDATES = [
    # ── LUXURY & SPORTS CARS ──────────────────────────────────────────────────
    {
        "id": 376,
        "name": "Subaru WRX STI Rally Spec Coupe",
        "brand": "Subaru",
        "price": Decimal("5200000.00"),
        "discount_price": Decimal("4950000.00"),
        "cost_price": Decimal("4200000.00"),
        "description": "The Subaru WRX STI Rally Spec Coupe is an iconic rally-bred performance sports car featuring Subaru's legendary Symmetrical All-Wheel Drive and a motorsport-tuned 2.5L Turbocharged BOXER engine. Built with championship rally heritage, it delivers razor-sharp handling, active center differential torque vectoring, high-performance Brembo braking, and aggressive aerodynamics for both track day precision and demanding terrain.",
        "specifications": (
            "Brand: Subaru\n"
            "Model: WRX STI Rally Spec Coupe\n"
            "Engine: 2.5-Liter Turbocharged DOHC 16-Valve Boxer-4\n"
            "Horsepower: 310 HP @ 6,000 RPM\n"
            "Torque: 393 Nm @ 4,000 RPM\n"
            "Transmission: Close-Ratio 6-Speed Manual with Short Throw Shifter\n"
            "Drivetrain: Symmetrical All-Wheel Drive with Driver Controlled Center Differential (DCCD)\n"
            "Acceleration (0-100 km/h): 4.9 seconds\n"
            "Top Speed: 255 km/h\n"
            "Braking System: Brembo Performance Brakes (6-Piston Front, 2-Piston Rear Calipers)\n"
            "Suspension: High-Performance Inverted Front Struts & Rear Double Wishbone\n"
            "Wheels: 19-inch Dark Gray BBS Forged Aluminum Alloy\n"
            "Exhaust: High-Flow Quad Stainless Steel Performance Exhaust Tips\n"
            "Interior: Recaro Sport Bucket Seats with Black Ultrasuede and Red Leather Bolsters\n"
            "Warranty: 3-Year / 60,000 km Manufacturer Warranty\n"
            "Country of Origin: Japan"
        ),
    },
    {
        "id": 375,
        "name": "Alfa Romeo Giulia Quadrifoglio",
        "brand": "Alfa Romeo",
        "price": Decimal("9500000.00"),
        "discount_price": Decimal("8990000.00"),
        "cost_price": Decimal("7600000.00"),
        "description": "The Alfa Romeo Giulia Quadrifoglio is a masterclass in Italian automotive passion and engineering, blending racetrack aerodynamics with luxury saloon craftsmanship. Powered by a Ferrari-derived 2.9L 90° Bi-Turbo V6 delivering 505 horsepower, it features near-perfect 50:50 weight distribution, an active carbon-fiber front splitter, carbon ceramic brakes, and the Alfa DNA Pro drive system with Race mode for hair-raising acceleration.",
        "specifications": (
            "Brand: Alfa Romeo\n"
            "Model: Giulia Quadrifoglio\n"
            "Engine: 2.9-Liter 90° V6 Bi-Turbo (Ferrari-derived)\n"
            "Horsepower: 505 HP @ 6,500 RPM\n"
            "Torque: 600 Nm @ 2,500 - 5,000 RPM\n"
            "Transmission: 8-Speed Sport Automatic with Column-Mounted Aluminum Paddle Shifters\n"
            "Drivetrain: Rear-Wheel Drive with Torque Vectoring Rear Differential\n"
            "Acceleration (0-100 km/h): 3.9 seconds\n"
            "Top Speed: 307 km/h\n"
            "Chassis & Aero: Carbon Fiber Hood, Roof, Active Front Aero Splitter, and Driveshaft\n"
            "Braking System: Brembo High-Performance Carbon Ceramic Discs\n"
            "Suspension: Alfa Active Suspension with Dual Wishbone Front and Multi-Link Rear\n"
            "Audio: 14-Speaker 900W Harman Kardon Premium Surround Sound System\n"
            "Wheels: 19-inch 5-Hole Forged Aluminum Alloys with Pirelli P Zero Corsa Tires\n"
            "Warranty: 3-Year / 100,000 km Warranty\n"
            "Country of Origin: Italy"
        ),
    },
    {
        "id": 374,
        "name": "Range Rover Sport SV Carbon Edition",
        "brand": "Land Rover",
        "price": Decimal("28000000.00"),
        "discount_price": Decimal("26500000.00"),
        "cost_price": Decimal("22500000.00"),
        "description": "The Range Rover Sport SV Carbon Edition represents the absolute pinnacle of high-performance luxury SUVs. Driven by a mild-hybrid 4.4-liter Twin-Turbo V8 engine delivering 635 HP, it boasts groundbreaking 23-inch ultra-lightweight carbon fiber wheels, carbon-ceramic brakes with bespoke 8-piston Brembo Octyma calipers, and world-first 6D Dynamics hydraulic interlinked air suspension that virtually eliminates pitch and roll.",
        "specifications": (
            "Brand: Land Rover\n"
            "Model: Range Rover Sport SV Carbon Edition\n"
            "Engine: 4.4-Liter Twin-Turbo MHEV V8 Engine\n"
            "Horsepower: 635 HP\n"
            "Torque: 750 Nm (800 Nm with Dynamic Launch)\n"
            "Transmission: 8-Speed Automatic Transmission with SV Paddle Shifters\n"
            "Drivetrain: Intelligent All-Wheel Drive with All-Terrain Progress Control & Configurable Dynamics\n"
            "Acceleration (0-100 km/h): 3.6 seconds\n"
            "Top Speed: 290 km/h\n"
            "Suspension: 6D Dynamics Semi-Active Hydraulic Interlinked Air Suspension\n"
            "Brakes: Carbon Ceramic Brakes with 8-Piston Brembo Octyma Front Calipers\n"
            "Wheels: 23-inch Ultra-Lightweight Carbon Fiber Wheels (saving 76 kg)\n"
            "Seating: Body and Soul (BASS) Sensory Audio-Tactile Performance Seats\n"
            "Exhaust: Quad Active Carbon-Fiber Tipped Sport Exhaust System\n"
            "Warranty: 5-Year / 150,000 km Comprehensive Warranty\n"
            "Country of Origin: United Kingdom"
        ),
    },
    {
        "id": 373,
        "name": "Mercedes-AMG GT R V8 Biturbo",
        "brand": "Mercedes-Benz",
        "price": Decimal("27100000.00"),
        "discount_price": Decimal("25900000.00"),
        "cost_price": Decimal("22000000.00"),
        "description": "Dubbed 'The Beast of the Green Hell', the Mercedes-AMG GT R is a purebred track weapon honed at the Nürburgring Nordschleife. Featuring a front-mid-mounted handcrafted AMG 4.0L V8 Biturbo engine with dry-sump lubrication, 9-way adjustable motorsport traction control, active rear-axle steering, and extensive carbon fiber aerodynamics, it is one of the most agile and exhilarating supercars ever constructed.",
        "specifications": (
            "Brand: Mercedes-Benz\n"
            "Model: AMG GT R Coupe\n"
            "Engine: Handcrafted 4.0-Liter AMG V8 Biturbo with Dry-Sump Lubrication\n"
            "Horsepower: 577 HP @ 6,250 RPM\n"
            "Torque: 700 Nm @ 1,900 - 5,500 RPM\n"
            "Transmission: AMG SPEEDSHIFT DCT 7-Speed Dual-Clutch Sport Transmission\n"
            "Drivetrain: Rear-Wheel Drive with Electronic Limited-Slip Differential\n"
            "Acceleration (0-100 km/h): 3.6 seconds\n"
            "Top Speed: 318 km/h\n"
            "Aerodynamics: Active Underbody Carbon Profile and Manually Adjustable Rear Wing\n"
            "Steering: AMG Active Rear-Axle Steering\n"
            "Braking System: AMG Carbon Ceramic High-Performance Composite Braking System\n"
            "Traction Control: 9-Stage AMG Motorsport Traction Control\n"
            "Exhaust: Titanium Center Exhaust with Dual Outboard Diffusers\n"
            "Warranty: 3-Year Unlimited Mileage AMG Warranty\n"
            "Country of Origin: Germany"
        ),
    },
    {
        "id": 372,
        "name": "Audi RS e-tron GT Electric Supercar",
        "brand": "Audi",
        "price": Decimal("19500000.00"),
        "discount_price": Decimal("18900000.00"),
        "cost_price": Decimal("16000000.00"),
        "description": "The Audi RS e-tron GT is Audi's flagship all-electric high-performance grand tourer. Driven by dual permanently excited synchronous electric motors producing up to 637 horsepower in boost launch mode, it features 800-volt high-speed charging architecture, electric quattro all-wheel drive, three-chamber adaptive air suspension, and an ultra-low drag coefficient of just 0.24 for blistering acceleration with grand touring comfort.",
        "specifications": (
            "Brand: Audi\n"
            "Model: RS e-tron GT\n"
            "Powertrain: Dual Synchronous Electric Motors (Front and Rear Axles)\n"
            "Peak Power: 637 HP (with Launch Control Boost) / 590 HP Continuous\n"
            "Torque: 830 Nm Instant Torque\n"
            "Transmission: 2-Speed Automatic on Rear Axle, Single-Speed on Front Axle\n"
            "Drivetrain: Electric quattro Permanent All-Wheel Drive with Controlled Rear Differential Lock\n"
            "Acceleration (0-100 km/h): 3.3 seconds\n"
            "Top Speed: 250 km/h (Electronically Limited)\n"
            "Battery Capacity: 93.4 kWh Lithium-Ion (800V Architecture)\n"
            "Fast Charging: 270 kW DC Ultra-Fast Charging (5% to 80% in 22.5 minutes)\n"
            "Driving Range: 472 km (WLTP Test Cycle)\n"
            "Suspension: 3-Chamber Adaptive Air Suspension with Electronic Damper Control\n"
            "Audio: Bang & Olufsen 3D Premium Sound System (16 Speakers, 710W)\n"
            "Warranty: 8-Year / 160,000 km High-Voltage Battery Warranty\n"
            "Country of Origin: Germany"
        ),
    },
    {
        "id": 371,
        "name": "Ford Mustang GT V8 Fastback Edition",
        "brand": "Ford",
        "price": Decimal("7500000.00"),
        "discount_price": Decimal("7150000.00"),
        "cost_price": Decimal("6000000.00"),
        "description": "The Ford Mustang GT V8 Fastback is the definitive American muscle car icon. Centered around the revered 5.0L Coyote naturally aspirated V8 engine that revs freely to 7,500 RPM while delivering an unmistakable rumble, it features selectable drive modes, an active valve performance quad exhaust, Brembo 6-piston front brakes, and an electronic line-lock track feature designed for drag-strip performance.",
        "specifications": (
            "Brand: Ford\n"
            "Model: Mustang GT Fastback\n"
            "Engine: 5.0-Liter Ti-VCT Coyote Naturally Aspirated V8\n"
            "Horsepower: 450 HP @ 7,000 RPM\n"
            "Torque: 529 Nm @ 4,600 RPM\n"
            "Transmission: 10-Speed SelectShift Automatic with Paddle Shifters\n"
            "Drivetrain: Rear-Wheel Drive with Torsen 3.55 Limited-Slip Rear Axle\n"
            "Acceleration (0-100 km/h): 4.3 seconds\n"
            "Top Speed: 250 km/h\n"
            "Exhaust: Active Valve Performance Dual Exhaust with Quad 3.5-inch Chrome Tips\n"
            "Braking System: Brembo 6-Piston Front Calipers with 380mm Vented Rotors\n"
            "Suspension: MagneRide Damping System (calibrates 1,000 times per second)\n"
            "Track Features: Electronic Line-Lock, Launch Control, and Acceleration Timers\n"
            "Cockpit: 12-inch All-Digital Instrument Cluster with SYNC 3\n"
            "Warranty: 3-Year / 100,000 km Standard Warranty\n"
            "Country of Origin: United States"
        ),
    },
    {
        "id": 370,
        "name": "Chevrolet Camaro SS 2018 - Blue Sports Coupe",
        "brand": "Chevrolet",
        "price": Decimal("6500000.00"),
        "discount_price": Decimal("6190000.00"),
        "cost_price": Decimal("5200000.00"),
        "description": "The Chevrolet Camaro SS Blue Sports Coupe combines muscular exterior design with razor-sharp sports car agility. Under the sculpted aluminum hood lies a thunderous 6.2-liter LT1 Small Block V8 engine paired with an 8-speed paddle-shift transmission. Built on the lightweight Alpha platform, it features Magnetic Ride Control suspension, Brembo 4-wheel performance brakes, and driver mode selector for optimal response on track or street.",
        "specifications": (
            "Brand: Chevrolet\n"
            "Model: Camaro SS Coupe\n"
            "Engine: 6.2-Liter LT1 Direct Injection Naturally Aspirated V8\n"
            "Horsepower: 455 HP @ 6,000 RPM\n"
            "Torque: 617 Nm @ 4,400 RPM\n"
            "Transmission: 8-Speed Paddle-Shift Automatic Transmission\n"
            "Drivetrain: Rear-Wheel Drive with Mechanical Limited-Slip Differential\n"
            "Acceleration (0-100 km/h): 4.0 seconds\n"
            "Top Speed: 265 km/h\n"
            "Suspension: Magnetic Ride Control Active Suspension System\n"
            "Braking System: Brembo 4-Piston Calipers with Performance Vented Rotors\n"
            "Cooling: Extra-Capacity Engine Cooling, Auxiliary Radiators, and Differential Cooler\n"
            "Exhaust: Dual-Mode Performance Quad Exhaust with Sound Management Valves\n"
            "Display: Head-Up Display (HUD) with G-Meter, Tachometer, and Speed\n"
            "Warranty: 3-Year / 60,000 km Limited Warranty\n"
            "Country of Origin: United States"
        ),
    },
    {
        "id": 369,
        "name": "BMW M4 Competition Convertible",
        "brand": "BMW",
        "price": Decimal("15300000.00"),
        "discount_price": Decimal("14700000.00"),
        "cost_price": Decimal("12400000.00"),
        "description": "The BMW M4 Competition Convertible combines the untamed track capability of BMW M with open-top motoring thrills. Driven by a 3.0-liter BMW M TwinPower Turbo inline 6-cylinder engine producing 503 HP and 650 Nm of torque, it couples with an 8-speed M Steptronic transmission and rear-biased M xDrive all-wheel drive. The innovative panel bow soft top folds away gracefully in just 18 seconds up to 50 km/h.",
        "specifications": (
            "Brand: BMW\n"
            "Model: M4 Competition Convertible M xDrive\n"
            "Engine: 3.0-Liter BMW M TwinPower Turbo Inline-6 (S58)\n"
            "Horsepower: 503 HP @ 6,250 RPM\n"
            "Torque: 650 Nm @ 2,750 - 5,500 RPM\n"
            "Transmission: 8-Speed M Steptronic with Drivelogic and Paddle Shifters\n"
            "Drivetrain: M xDrive Intelligent AWD with Selectable 4WD, 4WD Sport, and 2WD Modes\n"
            "Acceleration (0-100 km/h): 3.7 seconds\n"
            "Top Speed: 280 km/h (with M Driver's Package)\n"
            "Roof: Lightweight Panel Bow Soft-Top (Opens/Closes in 18s up to 50 km/h)\n"
            "Brakes: M Compound Brakes with 6-Piston Fixed Front Calipers\n"
            "Chassis: Adaptive M Suspension with Electronically Controlled Dampers\n"
            "Infotainment: BMW Curved Display (12.3-inch cluster + 14.9-inch screen) with OS 8.5\n"
            "Warranty: 3-Year / 200,000 km BMW Service Inclusive\n"
            "Country of Origin: Germany"
        ),
    },
    {
        "id": 368,
        "name": "Porsche 911 Carrera Custom Coupe",
        "brand": "Porsche",
        "price": Decimal("20000000.00"),
        "discount_price": Decimal("19200000.00"),
        "cost_price": Decimal("16200000.00"),
        "description": "The Porsche 911 Carrera is the timeless benchmark of sports car perfection. Engineered with rear-engine purity, it is powered by a responsive 3.0-liter twin-turbocharged boxer-6 engine mated to Porsche's lightning-fast 8-speed PDK transmission. Featuring Porsche Active Suspension Management (PASM), Porsche Torque Vectoring Plus (PTV+), and an iconic silhouette, it delivers an unmatched driver-machine connection.",
        "specifications": (
            "Brand: Porsche\n"
            "Model: 911 Carrera Coupe\n"
            "Engine: 3.0-Liter Twin-Turbocharged Flat-6 Boxer Engine\n"
            "Horsepower: 385 HP @ 6,500 RPM\n"
            "Torque: 450 Nm @ 1,950 - 5,000 RPM\n"
            "Transmission: 8-Speed Porsche Doppelkupplung (PDK) Dual-Clutch Transmission\n"
            "Drivetrain: Rear-Wheel Drive with Porsche Torque Vectoring Plus (PTV+)\n"
            "Acceleration (0-100 km/h): 4.0 seconds (with Sport Chrono Package)\n"
            "Top Speed: 293 km/h\n"
            "Suspension: Porsche Active Suspension Management (PASM) with 10mm Lowered Stance\n"
            "Braking System: 4-Piston Monobloc Fixed Front & Rear Calipers with 330mm Discs\n"
            "Exhaust: Twin Single-Tube Tailpipes in Brushed Stainless Steel with Sport Mode\n"
            "Interior: 2+2 Leather Sport Seats with Embossed Porsche Crests\n"
            "Warranty: 4-Year / 100,000 km Porsche Approved Warranty\n"
            "Country of Origin: Germany"
        ),
    },
    {
        "id": 367,
        "name": "Tesla Model S Plaid Sport Edition",
        "brand": "Tesla",
        "price": Decimal("15000000.00"),
        "discount_price": Decimal("14400000.00"),
        "cost_price": Decimal("12200000.00"),
        "description": "The Tesla Model S Plaid is the quickest accelerating production car in existence. Engineered with a revolutionary tri-motor all-wheel-drive powertrain utilizing carbon-sleeved rotors, it outputs 1,020 peak horsepower to launch from 0 to 100 km/h in an unbelievable 2.1 seconds. Featuring a 17-inch cinematic center display with console-quality gaming, adaptive air suspension, and estimated 600 km range, it redefines the frontier of electric performance.",
        "specifications": (
            "Brand: Tesla\n"
            "Model: Model S Plaid\n"
            "Powertrain: Tri-Motor All-Wheel Drive with Carbon-Sleeved Rotors\n"
            "Peak Power: 1,020 HP\n"
            "Torque: 1,420 Nm Instant Torque\n"
            "Acceleration (0-100 km/h): 2.1 seconds\n"
            "Quarter Mile: 9.23 seconds @ 250 km/h\n"
            "Top Speed: 322 km/h (with Plaid Track Package)\n"
            "Battery & Range: 100 kWh Battery Pack, Estimated 600 km EPA Range\n"
            "Charging Speed: Up to 250 kW Supercharging (adds up to 322 km in 15 minutes)\n"
            "Suspension: Adaptive Air Suspension with Auto-Leveling and GPS Height Memory\n"
            "Interior Display: 17-inch Tiltable Cinematic OLED Display (2200 x 1300 resolution, 10 TFLOPs gaming)\n"
            "Audio System: 22-Speaker 960-Watt Premium Audio with Active Road Noise Cancellation\n"
            "Warranty: 8-Year / 240,000 km Powertrain & Battery Warranty\n"
            "Country of Origin: United States"
        ),
    },

    # ── HIGH-TECH PRODUCTS, TABLETS, LAPTOPS & PHONES ────────────────────────
    {
        "id": 710,
        "name": "Xiaomi Pad 7 Pro",
        "brand": "Xiaomi",
        "price": Decimal("28990.00"),
        "discount_price": Decimal("26999.00"),
        "cost_price": Decimal("22000.00"),
        "description": "The Xiaomi Pad 7 Pro is a flagship Android tablet powered by the 4nm Qualcomm Snapdragon 8s Gen 3 processor. It features an ultra-sharp 11.2-inch 3.2K (3200 x 2136) 144Hz display with 800 nits brightness, an expansive 8850mAh battery with 67W HyperCharge, quad stereo speakers with Dolby Atmos, and Xiaomi HyperOS 2 for desktop-grade productivity and split-screen multitasking.",
        "specifications": (
            "Brand: Xiaomi\n"
            "Model: Pad 7 Pro\n"
            "Display: 11.2-inch 3.2K IPS LCD, 3200 x 2136 pixels, 144Hz Refresh Rate, 800 nits peak\n"
            "Processor: Qualcomm Snapdragon 8s Gen 3 (4nm Octa-Core up to 3.0 GHz)\n"
            "RAM & Storage: 8GB LPDDR5X RAM, 256GB UFS 4.0 High-Speed Internal Storage\n"
            "Rear Camera: 50 MP Main Sensor with 4K Video Recording & PDAF\n"
            "Front Camera: 32 MP Ultra-Wide Selfie Camera with FocusFrame Tracking\n"
            "Battery: 8,850 mAh Large Capacity Battery\n"
            "Charging: 67W Turbo Charge (USB-C 3.2 Gen 1)\n"
            "Operating System: Xiaomi HyperOS 2 based on Android 15\n"
            "Audio: Quad Stereo Speakers with Dolby Atmos & Hi-Res Wireless Audio\n"
            "Connectivity: Wi-Fi 7 (802.11be), Bluetooth 5.4, USB Type-C 3.2 Gen 1\n"
            "Build & Weight: All-Aluminum Unibody, 500g Lightweight Design\n"
            "Warranty: 1 Year Manufacturer Warranty\n"
            "Country of Origin: India / China"
        ),
    },
    {
        "id": 324,
        "name": "Apple MacBook Pro 16-inch (M3 Max)",
        "brand": "Apple",
        "price": Decimal("349900.00"),
        "discount_price": Decimal("329900.00"),
        "cost_price": Decimal("280000.00"),
        "description": "The 16-inch MacBook Pro with M3 Max takes performance and efficiency to extreme levels. Built for demanding workflows like 3D rendering, machine learning modeling, and 8K video color grading, it features a 16-core CPU, 40-core GPU, 36GB unified memory, and a Liquid Retina XDR display with 1600 nits peak HDR brightness and 120Hz ProMotion.",
        "specifications": (
            "Brand: Apple\n"
            "Model: MacBook Pro 16-inch (M3 Max)\n"
            "Display: 16.2-inch Liquid Retina XDR Display, 3456 x 2234 resolution, 120Hz ProMotion, 1600 nits peak HDR\n"
            "Processor: Apple M3 Max (16-Core CPU with 12 performance and 4 efficiency cores)\n"
            "Graphics: 40-Core GPU with Hardware-Accelerated Ray Tracing and Mesh Shading\n"
            "Memory: 36GB Unified Memory (300GB/s memory bandwidth)\n"
            "Storage: 1TB High-Speed NVMe SSD\n"
            "Battery Life: Up to 22 hours video playback, 100Wh battery with 140W USB-C Power Adapter\n"
            "Ports: 3x Thunderbolt 4 (USB-C), HDMI port, SDXC card slot, headphone jack, MagSafe 3\n"
            "Audio: Six-Speaker Sound System with Force-Cancelling Woofers and Spatial Audio\n"
            "Camera: 1080p FaceTime HD Camera with Advanced Image Signal Processor\n"
            "Operating System: macOS Sequoia\n"
            "Warranty: 1 Year Apple Limited Warranty\n"
            "Country of Origin: China / Vietnam"
        ),
    },
    {
        "id": 325,
        "name": "iPad Pro 12.9-inch M2 Liquid Retina XDR",
        "brand": "Apple",
        "price": Decimal("112900.00"),
        "discount_price": Decimal("104900.00"),
        "cost_price": Decimal("90000.00"),
        "description": "The 12.9-inch iPad Pro delivers unmatched performance with the Apple M2 chip. Its breathtaking Liquid Retina XDR display uses mini-LED backlight technology for 1,000,000:1 contrast and 1600 nits peak HDR brightness. With Apple Pencil hover detection, ProRes video capture, and desktop-class Stage Manager multitasking, it is the ultimate creative powerhouse.",
        "specifications": (
            "Brand: Apple\n"
            "Model: iPad Pro 12.9-inch (6th Gen)\n"
            "Display: 12.9-inch Mini-LED Liquid Retina XDR, 2732 x 2048 at 264 ppi, 120Hz ProMotion, True Tone\n"
            "Processor: Apple M2 Chip (8-Core CPU, 10-Core GPU, 16-Core Neural Engine)\n"
            "Memory & Storage: 8GB RAM, 256GB High-Speed Storage\n"
            "Cameras: 12MP Wide + 10MP Ultra Wide rear with LiDAR Scanner; 12MP TrueDepth Front with Center Stage\n"
            "Video: 4K video recording at up to 60 fps, ProRes video recording up to 4K at 30 fps\n"
            "Pencil Support: Apple Pencil (2nd Gen) with Hover Technology\n"
            "Connectivity: Wi-Fi 6E, Bluetooth 5.3, Thunderbolt / USB 4 Port\n"
            "Authentication: Face ID via TrueDepth Camera\n"
            "Operating System: iPadOS\n"
            "Warranty: 1 Year Apple Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 545,
        "name": "Iphone 16 Pro Max",
        "brand": "Apple",
        "price": Decimal("144900.00"),
        "discount_price": Decimal("139900.00"),
        "cost_price": Decimal("115000.00"),
        "description": "The iPhone 16 Pro Max features a gorgeous Grade 5 Titanium design with the thinnest borders on any Apple product. Powered by the A18 Pro chip, it brings Apple Intelligence, an innovative Camera Control capacitive button, a versatile 48MP Fusion camera system with 5x telephoto optical zoom, and 4K 120 fps Dolby Vision video recording.",
        "specifications": (
            "Brand: Apple\n"
            "Model: iPhone 16 Pro Max\n"
            "Display: 6.9-inch Super Retina XDR OLED, 2868 x 1320 pixels, ProMotion 120Hz, Always-On, 2000 nits peak\n"
            "Processor: A18 Pro Chip (6-Core CPU, 6-Core GPU with Hardware Ray Tracing, 16-Core Neural Engine)\n"
            "Storage: 256GB NVMe Internal Storage\n"
            "Rear Camera: 48MP Fusion (24mm, f/1.78) + 48MP Ultra Wide (13mm, f/2.2) + 12MP 5x Telephoto (120mm, f/2.8)\n"
            "Front Camera: 12MP TrueDepth Front Camera with Autofocus\n"
            "Video Recording: 4K Dolby Vision video recording at 24, 25, 30, 60, 100, or 120 fps\n"
            "Camera Control: Capacitive force-sensitive button for immediate capture and zoom control\n"
            "Battery: Up to 33 hours video playback; Fast Qi2 & MagSafe wireless charging up to 25W\n"
            "Build & Durability: Grade 5 Titanium frame, Ceramic Shield front, IP68 water resistance\n"
            "Operating System: iOS 18 with Apple Intelligence\n"
            "Warranty: 1 Year Apple Warranty\n"
            "Country of Origin: India / China"
        ),
    },
    {
        "id": 544,
        "name": "Iphone 16 Cover",
        "brand": "Apple",
        "price": Decimal("1499.00"),
        "discount_price": Decimal("1299.00"),
        "cost_price": Decimal("600.00"),
        "description": "Designed by Apple to complement and protect iPhone 16, this premium silicone case with MagSafe has a silky, soft-touch exterior that feels great in your hand. On the inside, there's a soft microfiber lining for even more protection. Equipped with conductive sapphire crystal for seamless Camera Control interaction and perfectly aligned magnets for faster wireless charging.",
        "specifications": (
            "Brand: Apple\n"
            "Product: iPhone 16 Silicone Case with MagSafe\n"
            "Material: Liquid Silicone Exterior, Microfiber Interior Lining\n"
            "Compatibility: iPhone 16\n"
            "MagSafe: Built-in N52 Neodymium Magnetic Ring for fast 15W wireless charging\n"
            "Camera Control: Conductive sapphire crystal overlay for uninterrupted fingertip gestures\n"
            "Drop Protection: Shock-absorbing perimeter buffer tested against 2-meter drops\n"
            "Warranty: 1 Year Limited Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 631,
        "name": "Samsung Galaxy S25 Ultra",
        "brand": "Samsung",
        "price": Decimal("129999.00"),
        "discount_price": Decimal("124999.00"),
        "cost_price": Decimal("105000.00"),
        "description": "The Samsung Galaxy S25 Ultra is the crown jewel of Android flagships. Powered by the bespoke Snapdragon 8 Elite for Galaxy 3nm processor, it boasts a flat 6.8-inch Dynamic AMOLED 2X display with anti-reflective Corning Gorilla Armor glass, an aerospace-grade titanium frame, an integrated S Pen stylus, and a quad-camera system led by an industry-leading 200MP sensor with Galaxy AI photo editing.",
        "specifications": (
            "Brand: Samsung\n"
            "Model: Galaxy S25 Ultra\n"
            "Display: 6.8-inch Dynamic AMOLED 2X, 3120 x 1440 (QHD+), 1-120Hz Adaptive Refresh, 2600 nits peak\n"
            "Processor: Qualcomm Snapdragon 8 Elite for Galaxy (3nm Octa-Core)\n"
            "RAM & Storage: 12GB LPDDR5X RAM, 256GB UFS 4.0 Storage\n"
            "Rear Cameras: 200MP Main (OIS) + 50MP 5x Periscope Telephoto (OIS) + 50MP Ultra Wide + 10MP 3x Telephoto\n"
            "Front Camera: 12MP Dual Pixel AF Selfie Camera\n"
            "Stylus: Built-in S Pen with Bluetooth Air Actions\n"
            "Battery & Charging: 5,000 mAh Battery with 45W Fast Wired & 15W Fast Wireless Charging\n"
            "Build & Durability: Titanium Frame, IP68 Water and Dust Resistance\n"
            "Operating System: Android 15 with One UI 7 & Galaxy AI (7 Years OS Updates)\n"
            "Warranty: 1 Year Comprehensive Manufacturer Warranty\n"
            "Country of Origin: India / South Korea"
        ),
    },
    {
        "id": 569,
        "name": "Macbook Air M3",
        "brand": "Apple",
        "price": Decimal("104900.00"),
        "discount_price": Decimal("96900.00"),
        "cost_price": Decimal("82000.00"),
        "description": "The 13-inch MacBook Air with M3 chip is an impossibly thin and ultra-portable laptop that sails through work and play. Powered by Apple's next-generation 3nm M3 chip, it offers up to 18 hours of battery life, support for up to two external displays with the laptop lid closed, Wi-Fi 6E, MagSafe 3 charging, and a stunning 13.6-inch Liquid Retina display.",
        "specifications": (
            "Brand: Apple\n"
            "Model: MacBook Air 13-inch (M3)\n"
            "Display: 13.6-inch Liquid Retina Display, 2560 x 1664 resolution, 500 nits brightness, True Tone\n"
            "Processor: Apple M3 Chip (8-Core CPU, 8-Core/10-Core GPU, 16-Core Neural Engine)\n"
            "Memory & Storage: 16GB Unified Memory, 256GB High-Speed SSD\n"
            "Battery: Up to 18 hours battery life, 52.6Wh lithium-polymer battery with 30W USB-C adapter\n"
            "External Displays: Supports up to two external displays (with laptop lid closed)\n"
            "Ports: MagSafe 3 charging port, 2x Thunderbolt / USB 4 ports, 3.5mm headphone jack\n"
            "Camera & Audio: 1080p FaceTime HD camera, four-speaker sound system with Spatial Audio\n"
            "Wireless: Wi-Fi 6E (802.11ax), Bluetooth 5.3\n"
            "Weight: 1.24 kg lightweight all-aluminum enclosure\n"
            "Warranty: 1 Year Apple Limited Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 600,
        "name": "Playstation 5 Digital Edition",
        "brand": "Sony",
        "price": Decimal("44990.00"),
        "discount_price": Decimal("41990.00"),
        "cost_price": Decimal("36000.00"),
        "description": "Experience lightning-fast loading with an ultra-high-speed SSD, deeper immersion with support for haptic feedback, adaptive triggers, and 3D Audio, and an all-new generation of incredible PlayStation games with the PS5 Digital Edition. Compact Slim design with 1TB built-in storage for all your favorite digital downloads.",
        "specifications": (
            "Brand: Sony\n"
            "Model: PlayStation 5 Digital Edition (Slim)\n"
            "CPU: Custom 8-Core AMD Zen 2 CPU up to 3.5 GHz\n"
            "GPU: Custom AMD RDNA 2 GPU with 10.3 TFLOPs and Hardware Ray Tracing\n"
            "Memory: 16GB GDDR6 RAM (448 GB/s Bandwidth)\n"
            "Storage: 1TB Custom PCIe Gen 4 NVMe SSD (5.5 GB/s Raw Read Speed)\n"
            "Video Output: 4K 120Hz TVs, 8K TVs, VRR (Variable Refresh Rate) supported via HDMI 2.1\n"
            "Audio: Tempest 3D AudioTech engine\n"
            "Controller: DualSense Wireless Controller included with Haptic Feedback and Dynamic Triggers\n"
            "Connectivity: Wi-Fi 6, Bluetooth 5.1, Gigabit Ethernet, 2x USB-C ports\n"
            "Warranty: 1 Year Sony India Domestic Warranty\n"
            "Country of Origin: Japan / China"
        ),
    },
    {
        "id": 709,
        "name": "Xbox Series S",
        "brand": "Microsoft",
        "price": Decimal("34990.00"),
        "discount_price": Decimal("31990.00"),
        "cost_price": Decimal("27000.00"),
        "description": "Go all-digital and enjoy next-gen performance in the smallest Xbox ever. Powered by Xbox Velocity Architecture, featuring a custom 512GB NVMe SSD and custom AMD Zen 2/RDNA 2 processor, Xbox Series S delivers seamless gameplay up to 120 FPS, lightning-fast load times, Quick Resume, and access to hundreds of blockbuster titles with Xbox Game Pass.",
        "specifications": (
            "Brand: Microsoft\n"
            "Model: Xbox Series S\n"
            "CPU: Custom 8-Core AMD Zen 2 CPU @ 3.6 GHz\n"
            "GPU: Custom AMD RDNA 2 GPU with 4 TFLOPs\n"
            "Memory: 10GB GDDR6 RAM\n"
            "Storage: 512GB Custom NVMe SSD with Xbox Velocity Architecture\n"
            "Target Resolution: 1440p gaming up to 120 FPS; 4K streaming and upscaling\n"
            "Ray Tracing: Hardware-Accelerated DirectX Ray Tracing\n"
            "Special Features: Quick Resume between multiple games, Backward Compatibility across 4 Xbox generations\n"
            "Audio: Dolby Atmos, DTS:X, and Windows Sonic 3D Spatial Sound\n"
            "Controller: Xbox Wireless Controller with Textured Grip and Share Button\n"
            "Warranty: 1 Year Microsoft Limited Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 708,
        "name": "Xbox Series Controller",
        "brand": "Microsoft",
        "price": Decimal("5390.00"),
        "discount_price": Decimal("4990.00"),
        "cost_price": Decimal("3800.00"),
        "description": "Experience the modernized design of the Xbox Wireless Controller, featuring sculpted surfaces and refined geometry for enhanced comfort during gameplay. Stay on target with textured grip on the triggers, bumpers, and back case, and capture and share gameplay effortlessly with a dedicated Share button. Seamlessly pair with Xbox consoles, PC, Android, and iOS.",
        "specifications": (
            "Brand: Microsoft\n"
            "Product: Xbox Wireless Controller\n"
            "Compatibility: Xbox Series X, Xbox Series S, Xbox One, Windows 10/11, Android, iOS\n"
            "Connectivity: Xbox Wireless, Bluetooth Low Energy, USB-C Wired\n"
            "Ergonomics: Hybrid D-Pad, Textured Grip on Triggers, Bumpers, and Back Case\n"
            "Share Button: Dedicated one-touch button to capture and share screenshots and recordings\n"
            "Audio: 3.5mm Stereo Headset Audio Jack\n"
            "Battery: Up to 40 hours of battery life with standard AA batteries or rechargeable pack\n"
            "Warranty: 90 Days Microsoft Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 326,
        "name": "Samsung Odyssey OLED G9 Curved Gaming Monitor",
        "brand": "Samsung",
        "price": Decimal("149999.00"),
        "discount_price": Decimal("139999.00"),
        "cost_price": Decimal("115000.00"),
        "description": "The Samsung Odyssey OLED G9 is a gargantuan 49-inch curved gaming monitor featuring Dual QHD (5120 x 1440) resolution, a blisteringly fast 240Hz refresh rate, and an instantaneous 0.03ms response time. Powered by the Neo Quantum Processor Pro, its OLED panel delivers inky blacks, vibrant HDR True Black 400 contrast, and AMD FreeSync Premium Pro for tears-free gaming.",
        "specifications": (
            "Brand: Samsung\n"
            "Model: Odyssey OLED G9 (G95SC)\n"
            "Screen Size & Curvature: 49-inch 32:9 Super Ultrawide with 1800R Curvature\n"
            "Resolution: Dual QHD (5120 x 1440 pixels)\n"
            "Panel Type: QD-OLED (Quantum Dot OLED)\n"
            "Refresh Rate: 240Hz\n"
            "Response Time: 0.03ms (GtG)\n"
            "HDR Rating: VESA DisplayHDR True Black 400\n"
            "Sync Technology: AMD FreeSync Premium Pro & G-Sync Compatible\n"
            "Smart Features: Samsung Gaming Hub, built-in streaming apps with Wi-Fi & Bluetooth\n"
            "Connectivity: DisplayPort 1.4, HDMI 2.1, Micro HDMI 2.1, USB Hub\n"
            "Lighting: CoreSync & Core Lighting+ rear ambient RGB rings\n"
            "Speakers: Built-in 5W Stereo Speakers\n"
            "Warranty: 3-Year Samsung On-Site Warranty\n"
            "Country of Origin: Vietnam"
        ),
    },
    {
        "id": 343,
        "name": "Canon EOS R6 Mark II Mirrorless Camera",
        "brand": "Canon",
        "price": Decimal("215995.00"),
        "discount_price": Decimal("199990.00"),
        "cost_price": Decimal("170000.00"),
        "description": "The Canon EOS R6 Mark II is an all-around hybrid mirrorless camera delivering breakthrough speed and video capabilities. Equipped with a 24.2MP full-frame CMOS sensor and DIGIC X image processor, it records uncropped 4K 60p 10-bit video oversampled from 6K and shoots continuous bursts up to 40 fps with full AF/AE tracking. Its in-body image stabilizer (IBIS) delivers up to 8 stops of shake correction.",
        "specifications": (
            "Brand: Canon\n"
            "Model: EOS R6 Mark II Body\n"
            "Sensor: 24.2 MP Full-Frame CMOS Sensor\n"
            "Image Processor: DIGIC X Processor\n"
            "Autofocus: Dual Pixel CMOS AF II with Deep Learning Subject Detection (People, Animals, Vehicles, Aircraft)\n"
            "Continuous Shooting: Up to 40 fps with electronic shutter, 12 fps with mechanical shutter\n"
            "Image Stabilization: In-Body 5-Axis Sensor-Shift IS (up to 8 stops with compatible RF lenses)\n"
            "Video: 4K 60p 10-bit Canon Log 3 (oversampled from 6K); 6K RAW external recording via HDMI\n"
            "Viewfinder: 0.5-inch 3.69M-dot OLED Electronic Viewfinder (120 fps refresh)\n"
            "Screen: 3.0-inch 1.62M-dot Vari-Angle Touchscreen LCD\n"
            "Storage: Dual SD/SDHC/SDXC UHS-II Memory Card Slots\n"
            "Connectivity: Wi-Fi 2.4/5GHz, Bluetooth 5.0, USB-C 3.2 Gen 2, Full-Size HDMI\n"
            "Warranty: 2-Year Canon India Warranty\n"
            "Country of Origin: Japan"
        ),
    },
    {
        "id": 345,
        "name": "Sony FE 24-70mm f/2.8 GM II Lens",
        "brand": "Sony",
        "price": Decimal("199990.00"),
        "discount_price": Decimal("189990.00"),
        "cost_price": Decimal("160000.00"),
        "description": "The Sony FE 24-70mm f/2.8 GM II is the world's lightest and smallest constant F2.8 standard zoom lens. Redesigned with four XD (Extreme Dynamic) Linear Motors, it delivers blazingly fast autofocus, minimal focus breathing, and sublime G Master corner-to-corner sharpness across the entire focal range.",
        "specifications": (
            "Brand: Sony\n"
            "Model: FE 24-70mm F2.8 GM II (SEL2470GM2)\n"
            "Mount: Sony E-Mount (Full-Frame Format)\n"
            "Focal Length: 24-70mm (Angle of view: 84° - 34°)\n"
            "Maximum Aperture: Constant f/2.8\n"
            "Aperture Blades: 11-Blade Circular Aperture for Creamy Bokeh\n"
            "Optical Elements: 20 Elements in 15 Groups (2 XA, 3 Aspherical, 2 ED, 2 Super ED)\n"
            "Coating: Nano AR Coating II to Suppress Flare and Ghosting\n"
            "AF Motor: 4 XD Linear Motors for 4x Faster AF Tracking\n"
            "Controls: Aperture Ring with Click/De-Click Switch, Iris Lock, 2 Focus Hold Buttons\n"
            "Weather Sealing: Dust and Moisture Resistant Construction, Fluorine Front Coating\n"
            "Filter Size: 82mm\n"
            "Weight: 695g (22% lighter than previous generation)\n"
            "Warranty: 2-Year Sony India Warranty\n"
            "Country of Origin: Japan"
        ),
    },
    {
        "id": 332,
        "name": "Bose QuietComfort Ultra Wireless Earbuds",
        "brand": "Bose",
        "price": Decimal("24990.00"),
        "discount_price": Decimal("22990.00"),
        "cost_price": Decimal("18000.00"),
        "description": "Bose QuietComfort Ultra Earbuds deliver groundbreaking spatialized audio and world-class noise cancellation. Using proprietary CustomTune sound calibration technology, they analyze the unique shape of your ears to tailor both the active noise reduction and sound signature specifically for you.",
        "specifications": (
            "Brand: Bose\n"
            "Model: QuietComfort Ultra Earbuds\n"
            "Noise Cancellation: World-Class Active Noise Cancelling with Aware Mode and ActiveSense\n"
            "Spatial Audio: Bose Immersive Audio with Still and Motion Tracking Modes\n"
            "Sound Calibration: CustomTune Technology personalized to individual ear canal shape\n"
            "Battery Life: Up to 6 hours on a single charge (up to 24 hours total with charging case)\n"
            "Quick Charge: 20-minute quick charge yields up to 2 hours of playback\n"
            "Microphones: 4 Noise-Rejecting Microphones in each earbud for crystal-clear calls\n"
            "Water Resistance: IPX4 Sweat and Weather Resistant\n"
            "Connectivity: Bluetooth 5.3 with aptX Adaptive and Multipoint Pairing\n"
            "Controls: Touch-Sensitive Capacitive Volume Slider and Multifunction Taps\n"
            "Warranty: 1 Year Bose Official Warranty\n"
            "Country of Origin: China / Vietnam"
        ),
    },
    {
        "id": 663,
        "name": "Sony Wh 1000xm6",
        "brand": "Sony",
        "price": Decimal("29990.00"),
        "discount_price": Decimal("26990.00"),
        "cost_price": Decimal("22000.00"),
        "description": "The Sony WH-1000XM Series sets the global benchmark for wireless noise cancelling headphones. Equipped with dual noise cancelling processors, eight microphones, and an Auto NC Optimizer, it eliminates ambient sound like never before. With 30 hours of battery life and Hi-Res Audio Wireless via LDAC, it offers peerless acoustic clarity.",
        "specifications": (
            "Brand: Sony\n"
            "Model: WH-1000XM Series Wireless Noise Cancelling\n"
            "Processors: Integrated Processor V1 + HD Noise Cancelling Processor QN1\n"
            "Microphones: 8 Microphones with Auto NC Optimizer for Real-Time Noise Suppression\n"
            "Driver Unit: Precision-Engineered 30mm Driver with Carbon Fiber Composite Dome\n"
            "Audio Codecs: LDAC, AAC, SBC (Hi-Res Audio Wireless & DSEE Extreme Audio Upscaling)\n"
            "Battery Life: Up to 30 hours with ANC enabled; 40 hours with ANC off\n"
            "Quick Charging: 3-minute charge provides up to 3 hours of playback\n"
            "Smart Features: Speak-to-Chat, Quick Attention Mode, Multipoint Bluetooth Connection\n"
            "Call Quality: 4 Beamforming Microphones with AI Noise Reduction Algorithm\n"
            "Warranty: 1 Year Sony India Warranty\n"
            "Country of Origin: Malaysia / China"
        ),
    },
    {
        "id": 327,
        "name": "Logitech MX Master 3S Ergonomic Wireless Mouse",
        "brand": "Logitech",
        "price": Decimal("9995.00"),
        "discount_price": Decimal("8995.00"),
        "cost_price": Decimal("7000.00"),
        "description": "The Logitech MX Master 3S is an ergonomic masterpiece engineered for coders, creators, and power users. Featuring an 8000 DPI Darkfield sensor that tracks anywhere—even on glass—Quiet Click switches with 90% less click noise, and the iconic MagSpeed electromagnetic scroll wheel capable of scrolling 1,000 lines per second.",
        "specifications": (
            "Brand: Logitech\n"
            "Model: MX Master 3S\n"
            "Sensor: Darkfield High Precision 8000 DPI Sensor (tracks on glass >= 4mm thickness)\n"
            "Scroll Wheel: MagSpeed Electromagnetic Smart-Shift Wheel (1,000 lines/sec)\n"
            "Thumb Controls: Horizontal Thumb Scroll Wheel, Gesture Button, Forward/Back Buttons\n"
            "Acoustics: Quiet Click Technology (90% noise reduction compared to Master 3)\n"
            "Connectivity: Bluetooth Low Energy & Logi Bolt USB Receiver (up to 3 devices with Easy-Switch)\n"
            "Battery Life: 500 mAh Li-Po battery lasts up to 70 days on a full charge; 1-min charge gives 3 hours\n"
            "Ergonomics: Sculpted palm support engineered for wrist neutrality\n"
            "Software: Logi Options+ Customizable Profiles per Application\n"
            "Warranty: 1 Year Logitech Limited Hardware Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 567,
        "name": "Logitech Mx Mechanical",
        "brand": "Logitech",
        "price": Decimal("16995.00"),
        "discount_price": Decimal("15495.00"),
        "cost_price": Decimal("12000.00"),
        "description": "The Logitech MX Mechanical Wireless Keyboard offers low-profile mechanical typing with extraordinary tactile feedback. Featuring smart backlighting that automatically illuminates when your hands approach, dual-connectivity via Bluetooth or Logi Bolt receiver, and seamless multi-device switching across Windows and macOS.",
        "specifications": (
            "Brand: Logitech\n"
            "Model: MX Mechanical Full-Size Wireless Keyboard\n"
            "Key Switches: Low-Profile Tactile Quiet Mechanical Switches\n"
            "Backlighting: Smart Ambient Sensing White Backlighting with 6 Lighting Effects\n"
            "Connectivity: Bluetooth Low Energy & Logi Bolt USB Receiver (Easy-Switch for 3 devices)\n"
            "Multi-OS: Dual Key Layout optimized for Windows, macOS, Linux, ChromeOS, iOS, Android\n"
            "Battery Life: Up to 15 days on full charge with backlighting, or up to 10 months with backlighting off\n"
            "Chassis: Top plate crafted from low-carbon aluminum for structural rigidity\n"
            "Charging: USB-C Quick Rechargeable\n"
            "Warranty: 1 Year Logitech Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 629,
        "name": "Samsung 49 Inch Chg90 144hz Curved Gaming Monitor Lc49hg90dmnxza Super Ultrawide Screen Qled",
        "brand": "Samsung",
        "price": Decimal("99990.00"),
        "discount_price": Decimal("89990.00"),
        "cost_price": Decimal("75000.00"),
        "description": "The Samsung CHG90 is a groundbreaking 49-inch super ultrawide 32:9 curved gaming monitor equivalent to two 27-inch 16:9 monitors side-by-side. Featuring Quantum Dot (QLED) technology delivering 125% sRGB color space, a fast 144Hz refresh rate, 1ms response time, and AMD FreeSync 2 HDR.",
        "specifications": (
            "Brand: Samsung\n"
            "Model: CHG90 (LC49HG90DMNXZA)\n"
            "Display Size: 49-inch 32:9 Super Ultrawide with 1800R Curvature\n"
            "Resolution: 3840 x 1080 (DFHD)\n"
            "Panel Technology: QLED VA Panel (125% sRGB, 95% DCI-P3)\n"
            "Refresh Rate: 144Hz (Switchable to 120Hz/60Hz)\n"
            "Response Time: 1ms (MPRT)\n"
            "HDR: High Dynamic Range (HDR) Support\n"
            "Adaptive Sync: AMD Radeon FreeSync 2 HDR Technology\n"
            "Ports: 2x HDMI 2.0, DisplayPort 1.2, Mini DisplayPort, USB 3.0 Hub, Audio In/Out\n"
            "Ergonomics: Height Adjustable Stand, Tilt & Swivel\n"
            "Warranty: 3-Year Samsung On-Site Warranty\n"
            "Country of Origin: Vietnam"
        ),
    },
    {
        "id": 632,
        "name": "Samsung T7 Shield SSD 2tb",
        "brand": "Samsung",
        "price": Decimal("17499.00"),
        "discount_price": Decimal("15999.00"),
        "cost_price": Decimal("12500.00"),
        "description": "The Samsung T7 Shield Portable SSD 2TB is designed to endure. Featuring an IP65 rating for water and dust resistance and a high-tech rubberized exterior capable of withstanding up to a 3-meter drop, it delivers blazing transfer speeds up to 1,050 MB/s via USB 3.2 Gen 2.",
        "specifications": (
            "Brand: Samsung\n"
            "Model: T7 Shield Portable SSD 2TB\n"
            "Capacity: 2 Terabytes (2000 GB)\n"
            "Interface: USB 3.2 Gen 2 (10 Gbps) Type-C\n"
            "Sequential Read Speed: Up to 1,050 MB/s\n"
            "Sequential Write Speed: Up to 1,000 MB/s\n"
            "Durability: IP65 Water and Dust Resistant, Drop-Resistant up to 3 meters\n"
            "Security: Optional AES 256-Bit Hardware Encryption with Password Protection\n"
            "Thermal Protection: Dynamic Thermal Guard controls heat to maintain fast speeds\n"
            "Compatibility: Windows, macOS, Android, iPadOS, Smart TVs, and Gaming Consoles\n"
            "In The Box: USB Type-C to C cable, USB Type-C to A cable\n"
            "Warranty: 3-Year Samsung Limited Warranty\n"
            "Country of Origin: South Korea"
        ),
    },
    {
        "id": 435,
        "name": "Canon Eos R50 Camera",
        "brand": "Canon",
        "price": Decimal("58995.00"),
        "discount_price": Decimal("54995.00"),
        "cost_price": Decimal("46000.00"),
        "description": "The Canon EOS R50 is an ultra-compact mirrorless camera made for creators and vloggers. Boasting a 24.2MP APS-C sensor paired with Canon's DIGIC X processor, it records gorgeous 4K 30p video oversampled from 6K, continuous bursts up to 15 fps, and features Dual Pixel CMOS AF II with smart subject tracking.",
        "specifications": (
            "Brand: Canon\n"
            "Model: EOS R50 Body\n"
            "Sensor: 24.2 MP APS-C CMOS Sensor\n"
            "Processor: DIGIC X Image Processor\n"
            "Video: Uncropped 6K-Oversampled 4K 30p, Full HD 120p Slow Motion\n"
            "Autofocus: Dual Pixel CMOS AF II with Human, Animal, and Vehicle Subject Detection\n"
            "Burst Rate: Up to 15 fps electronic shutter, 12 fps electronic front curtain\n"
            "Screen: 3.0-inch 1.62M-dot Vari-Angle Touchscreen LCD\n"
            "Viewfinder: 0.39-inch 2.36M-dot OLED Electronic Viewfinder\n"
            "Vlogging Features: Close-Up Demos Mode, Movie for Close-up View, Vertical Video Support\n"
            "Weight: 375g Lightweight and Pocketable Body\n"
            "Warranty: 2-Year Canon India Warranty\n"
            "Country of Origin: Japan"
        ),
    },
    {
        "id": 434,
        "name": "Canon Eos R50",
        "brand": "Canon",
        "price": Decimal("58995.00"),
        "discount_price": Decimal("54995.00"),
        "cost_price": Decimal("46000.00"),
        "description": "The Canon EOS R50 is an ultra-compact mirrorless camera made for creators and vloggers. Boasting a 24.2MP APS-C sensor paired with Canon's DIGIC X processor, it records gorgeous 4K 30p video oversampled from 6K, continuous bursts up to 15 fps, and features Dual Pixel CMOS AF II with smart subject tracking.",
        "specifications": (
            "Brand: Canon\n"
            "Model: EOS R50 Body\n"
            "Sensor: 24.2 MP APS-C CMOS Sensor\n"
            "Processor: DIGIC X Image Processor\n"
            "Video: Uncropped 6K-Oversampled 4K 30p, Full HD 120p Slow Motion\n"
            "Autofocus: Dual Pixel CMOS AF II with Human, Animal, and Vehicle Subject Detection\n"
            "Burst Rate: Up to 15 fps electronic shutter, 12 fps electronic front curtain\n"
            "Screen: 3.0-inch 1.62M-dot Vari-Angle Touchscreen LCD\n"
            "Viewfinder: 0.39-inch 2.36M-dot OLED Electronic Viewfinder\n"
            "Weight: 375g Lightweight Body\n"
            "Warranty: 2-Year Canon India Warranty\n"
            "Country of Origin: Japan"
        ),
    },
    {
        "id": 702,
        "name": "Webcam HD",
        "brand": "Generic",
        "price": Decimal("1899.00"),
        "discount_price": Decimal("1499.00"),
        "cost_price": Decimal("900.00"),
        "description": "Crystal-clear 1080p Full HD USB webcam designed for video conferencing, live streaming, and remote education. Features an omnidirectional noise-reducing microphone, automatic light correction, and a 360-degree rotating mounting clip.",
        "specifications": (
            "Resolution: 1080p Full HD @ 30 FPS\n"
            "Microphone: Built-in Noise-Reduction Mic\n"
            "Lens: Premium Multi-Layer Glass Lens with 90° Field of View\n"
            "Connectivity: USB 2.0 Plug & Play (no driver required)\n"
            "Compatibility: Windows 11/10/8/7, macOS, Linux, Android\n"
            "Mount: Universal Tripod-Ready Clip for Laptops and Monitors\n"
            "Warranty: 1 Year Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 700,
        "name": "Wd 2tb Elements Portable External Hard Drive USB 30",
        "brand": "Western Digital",
        "price": Decimal("6199.00"),
        "discount_price": Decimal("5799.00"),
        "cost_price": Decimal("4600.00"),
        "description": "WD Elements portable hard drive offers reliable, high-capacity storage on the go, fast data transfer rates with USB 3.0, and universal connectivity with USB 3.0 and USB 2.0 devices.",
        "specifications": (
            "Brand: Western Digital\n"
            "Model: WD Elements Portable 2TB\n"
            "Capacity: 2 Terabytes\n"
            "Interface: USB 3.0 (compatible with USB 2.0)\n"
            "Form Factor: 2.5-inch Portable Hard Drive\n"
            "Transfer Rate: Up to 5 Gbps\n"
            "Operating System: Formatted NTFS for Windows 10/11; reformatable for macOS\n"
            "Warranty: 2-Year Limited Manufacturer Warranty\n"
            "Country of Origin: Malaysia / Thailand"
        ),
    },
    {
        "id": 699,
        "name": "Wd 2tb Elements Portable External Hard Drive USB",
        "brand": "Western Digital",
        "price": Decimal("6199.00"),
        "discount_price": Decimal("5799.00"),
        "cost_price": Decimal("4600.00"),
        "description": "WD Elements portable hard drive offers reliable, high-capacity storage on the go, fast data transfer rates with USB 3.0, and universal connectivity with USB 3.0 and USB 2.0 devices.",
        "specifications": (
            "Brand: Western Digital\n"
            "Model: WD Elements Portable 2TB\n"
            "Capacity: 2 Terabytes\n"
            "Interface: USB 3.0 (compatible with USB 2.0)\n"
            "Form Factor: 2.5-inch Portable Hard Drive\n"
            "Transfer Rate: Up to 5 Gbps\n"
            "Operating System: Formatted NTFS for Windows 10/11; reformatable for macOS\n"
            "Warranty: 2-Year Limited Manufacturer Warranty\n"
            "Country of Origin: Malaysia / Thailand"
        ),
    },
    {
        "id": 701,
        "name": "Wd 4tb Gaming Drive Works With Playstation 4 Portable External Hard Drive",
        "brand": "Western Digital",
        "price": Decimal("11499.00"),
        "discount_price": Decimal("10499.00"),
        "cost_price": Decimal("8500.00"),
        "description": "Expand your console gaming capacity with the official WD 4TB Gaming Drive. Store up to 100+ full-sized game titles without deleting your existing library, with fast USB 3.0 connectivity and plug-and-play installation.",
        "specifications": (
            "Brand: Western Digital\n"
            "Model: WD Gaming Drive 4TB\n"
            "Capacity: 4 Terabytes\n"
            "Compatibility: PlayStation 4, PlayStation 5 (PS4 games storage), Xbox One, PC\n"
            "Interface: USB 3.0\n"
            "Setup: Plug-and-Play Quick Console Setup\n"
            "Warranty: 3-Year Limited Warranty\n"
            "Country of Origin: Malaysia"
        ),
    },
    {
        "id": 711,
        "name": "Xiaomi Smart Air Purifier",
        "brand": "Xiaomi",
        "price": Decimal("9999.00"),
        "discount_price": Decimal("8999.00"),
        "cost_price": Decimal("7000.00"),
        "description": "Breathe pure, fresh air with the Xiaomi Smart Air Purifier. Featuring a 3-in-1 true HEPA filter capturing 99.97% of particles down to 0.3 microns, real-time OLED air quality display, 360-degree filtration, and seamless voice control via Xiaomi Home app, Alexa, and Google Assistant.",
        "specifications": (
            "Brand: Xiaomi\n"
            "Model: Smart Air Purifier 4 Series\n"
            "CADR (Clean Air Delivery Rate): Up to 400 m³/h\n"
            "Effective Coverage Area: Up to 516 sq. ft. (48 m²)\n"
            "Filtration: 3-in-1 High Efficiency Filter + Activated Carbon Layer\n"
            "Noise Level: Ultra-Quiet 32.1 dB(A) Night Mode\n"
            "Display: Crisp OLED Touch Display with Air Quality Indicator Ring\n"
            "Smart Connectivity: Wi-Fi 2.4 GHz, Mi Home App, Google Assistant, Amazon Alexa\n"
            "Power Consumption: 30W High-Efficiency Low Energy Motor\n"
            "Warranty: 1 Year Warranty\n"
            "Country of Origin: India / China"
        ),
    },
    {
        "id": 712,
        "name": "Xiaomi Smart Band",
        "brand": "Xiaomi",
        "price": Decimal("2499.00"),
        "discount_price": Decimal("2299.00"),
        "cost_price": Decimal("1600.00"),
        "description": "Step up your fitness with the Xiaomi Smart Band. Featuring a vibrant 1.62-inch AMOLED high-resolution display with 60Hz refresh rate, 150+ fitness sports modes, continuous heart rate and SpO2 tracking, sleep analysis, and up to 16 days of battery life.",
        "specifications": (
            "Brand: Xiaomi\n"
            "Model: Smart Band 8\n"
            "Display: 1.62-inch AMOLED Display, 192 x 490 pixels, 60Hz, 600 nits peak\n"
            "Sensors: High-Precision 6-Axis Sensor, PPG Heart Rate & SpO2 Sensor\n"
            "Sports Modes: 150+ Professional Workout & Sports Modes\n"
            "Health Tracking: 24/7 Heart Rate, All-Day Blood Oxygen, Sleep & Stress Monitoring\n"
            "Water Resistance: 5 ATM (Up to 50 meters water resistance)\n"
            "Battery: 190 mAh Lithium-Ion Battery (Up to 16 days typical use)\n"
            "Charging: Magnetic Fast Charging (approx. 1 hour full charge)\n"
            "Compatibility: Android 6.0+ or iOS 12.0+ via Mi Fitness App\n"
            "Warranty: 1 Year Manufacturer Warranty\n"
            "Country of Origin: India / China"
        ),
    },
    {
        "id": 506,
        "name": "Essence Mascara Lash Princess",
        "brand": "Generic Brand",
        "price": Decimal("399.00"),
        "discount_price": Decimal("349.00"),
        "cost_price": Decimal("180.00"),
        "description": "Essence Lash Princess False Lash Effect Mascara delivers dramatic volume and sculpted length without clumps or flaking. Features a conic shape fiber brush that coats each individual lash for a stunning false lash effect that lasts all day.",
        "specifications": (
            "Brand: Essence\n"
            "Product: Lash Princess False Lash Effect Mascara\n"
            "Volume: 12 ml\n"
            "Finish: Dramatic False Lash Length & Volume\n"
            "Brush Type: Conical Shaped Precision Fiber Wand\n"
            "Features: Cruelty-Free, Paraben-Free, Long-Lasting Wear\n"
            "Country of Origin: Italy / Germany"
        ),
    },
    {
        "id": 707,
        "name": "Wooden Bathroom Sink With Mirror",
        "brand": "Generic",
        "price": Decimal("14999.00"),
        "discount_price": Decimal("13499.00"),
        "cost_price": Decimal("9500.00"),
        "description": "Handcrafted solid teak wood bathroom vanity combo featuring a premium ceramic undermount vessel sink, matching framed mirror, moisture-resistant protective matte finish, and spacious soft-closing cabinet doors.",
        "specifications": (
            "Material: Solid Natural Teak Wood & High-Gloss Vitreous Ceramic Basin\n"
            "Includes: Vanity Cabinet Unit, Ceramic Basin, Matching Wooden Frame Mirror\n"
            "Dimensions Vanity: 32\" H x 30\" W x 20\" D\n"
            "Dimensions Mirror: 30\" H x 24\" W\n"
            "Finish: Water-Resistant Multi-Coat Polyurethane Seal\n"
            "Hardware: Brushed Stainless Steel Soft-Closing Hinges\n"
            "Warranty: 2 Years Structural Warranty\n"
            "Country of Origin: India"
        ),
    },

    # ── AUTOMOTIVE ACCESSORIES (Fixing inflated prices) ────────────────────────
    {
        "id": 422,
        "name": "Bike Phone Holder",
        "brand": "Generic",
        "price": Decimal("799.00"),
        "discount_price": Decimal("649.00"),
        "cost_price": Decimal("300.00"),
        "description": "Universal 360-degree rotation motorcycle and bicycle phone mount. Crafted with heavy-duty aluminum alloy brackets and shock-absorbing silicone pads to keep smartphones securely clamped over rough terrain.",
        "specifications": (
            "Material: High-Grade CNC Aluminum Alloy & Shockproof Silicone\n"
            "Compatibility: 4.7-inch to 7.0-inch Smartphones (iPhone, Samsung, OnePlus, Xiaomi)\n"
            "Handlebar Diameter: Fits 22mm - 32mm handlebars\n"
            "Rotation: 360-Degree Ball Joint for Portrait and Landscape Viewing\n"
            "Warranty: 6 Months Replacement Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 561,
        "name": "LED Bike Light Set",
        "brand": "Generic",
        "price": Decimal("1299.00"),
        "discount_price": Decimal("999.00"),
        "cost_price": Decimal("450.00"),
        "description": "Super-bright rechargeable bicycle headlight and taillight set. Equipped with ultra-luminous Cree T6 LEDs delivering up to 1000 lumens, multiple lighting modes, USB-C rechargeable batteries, and IPX6 waterproof protection.",
        "specifications": (
            "Brightness: 1000 Lumens (Headlight), 120 Lumens (Taillight)\n"
            "Battery: 2600 mAh USB-C Rechargeable Lithium Battery\n"
            "Runtime: Up to 8 hours on medium mode\n"
            "Modes: High, Medium, Low, Strobe, SOS Flash\n"
            "Waterproof Rating: IPX6 Weatherproof\n"
            "Mounting: Tool-Free Quick Release Silicone Straps\n"
            "Warranty: 1 Year Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 687,
        "name": "Tyre Inflator",
        "brand": "Generic",
        "price": Decimal("2499.00"),
        "discount_price": Decimal("2199.00"),
        "cost_price": Decimal("1300.00"),
        "description": "Portable 12V DC digital tire inflator with auto shut-off and digital pressure gauge. Inflates a standard car tire from 0 to 35 PSI in under 4 minutes with emergency LED work light and multiple nozzle attachments.",
        "specifications": (
            "Power Input: 12V DC Cigarette Lighter Socket (10A)\n"
            "Maximum Pressure: 150 PSI\n"
            "Inflation Speed: 35 Liters/min\n"
            "Auto Shut-off: Automatically stops when preset target PSI is reached\n"
            "Cord Length: 3-Meter Heavy-Duty Power Cord + 60cm Air Hose\n"
            "Lighting: Built-in High-Visibility LED Emergency Flashlight\n"
            "Warranty: 1 Year Warranty\n"
            "Country of Origin: India / China"
        ),
    },
    {
        "id": 438,
        "name": "Car Tire Inflator",
        "brand": "Generic",
        "price": Decimal("2799.00"),
        "discount_price": Decimal("2399.00"),
        "cost_price": Decimal("1400.00"),
        "description": "Compact cordless rechargeable air compressor and tire inflator with 6000mAh battery. Delivers rapid inflation for cars, bikes, sports balls, and scooters with digital LCD display and preset pressure settings.",
        "specifications": (
            "Battery: 6000 mAh Rechargeable Lithium-Ion Battery\n"
            "Pressure Range: 0 - 150 PSI (0 - 10.3 Bar)\n"
            "Display: Backlit Digital LCD Pressure Display\n"
            "Charging: USB-C Fast Charging + 12V DC Vehicle Adapter\n"
            "Accessories: 4 Adapters (Presta valve, ball needle, swimming ring nozzle)\n"
            "Warranty: 1 Year Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 538,
        "name": "Helmet Visor",
        "brand": "Generic",
        "price": Decimal("899.00"),
        "discount_price": Decimal("749.00"),
        "cost_price": Decimal("350.00"),
        "description": "Anti-scratch, UV400 protective helmet replacement face shield visor. Made of high-strength optical grade polycarbonate with anti-fog coating for crystal-clear night and day visibility.",
        "specifications": (
            "Material: Optical Grade Polycarbonate\n"
            "Protection: UV400 Sun Protection & Anti-Scratch Hard Coating\n"
            "Visibility: High-Transparency Clear / Smoke Tint options\n"
            "Compatibility: Universal 3-snap / ratchet helmet mounts\n"
            "Warranty: 6 Months Warranty\n"
            "Country of Origin: India"
        ),
    },
    {
        "id": 482,
        "name": "Dash Cam",
        "brand": "Generic",
        "price": Decimal("4999.00"),
        "discount_price": Decimal("4299.00"),
        "cost_price": Decimal("2600.00"),
        "description": "Full HD 1080p vehicle dashboard camera featuring 170-degree wide-angle lens, night vision sensor, G-sensor emergency collision lock, loop recording, and 24-hour parking surveillance mode.",
        "specifications": (
            "Resolution: 1080p Full HD @ 30 FPS with Sony STARVIS Night Vision Sensor\n"
            "Field of View: 170-Degree Ultra Wide Angle\n"
            "Display: 3.0-inch IPS Display Screen\n"
            "Sensors: Built-in G-Sensor Collision Lock & Motion Detection\n"
            "Storage: Supports MicroSD Cards up to 128GB (Class 10+)\n"
            "Power: 12V/24V Car Charger with Supercapacitor for heat resistance\n"
            "Warranty: 1 Year Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 439,
        "name": "Car Vacuum",
        "brand": "Generic",
        "price": Decimal("1899.00"),
        "discount_price": Decimal("1599.00"),
        "cost_price": Decimal("900.00"),
        "description": "High-power 120W portable handheld car vacuum cleaner with 8000Pa cyclonic suction. Comes with washable HEPA filter, crevice tool, brush attachment, and flexible extension hose for deep interior cleaning.",
        "specifications": (
            "Suction Power: 8000 Pa High-Power Suction (120W Motor)\n"
            "Filter: Washable & Reusable Stainless Steel + HEPA Filter\n"
            "Power: 12V DC Vehicle Cigarette Lighter Plug with 4.5m Cord\n"
            "Dust Cup: 500 ml Transparent Quick-Release Dust Canister\n"
            "Accessories: Crevice Tool, Dusting Brush, Extension Hose, Carry Bag\n"
            "Warranty: 1 Year Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 421,
        "name": "Bike Mirror Set",
        "brand": "Generic",
        "price": Decimal("599.00"),
        "discount_price": Decimal("499.00"),
        "cost_price": Decimal("220.00"),
        "description": "Pair of 360-degree adjustable HD convex rearview handlebar mirrors for bicycles and electric scooters. Made of shatterproof acrylic glass and sturdy ABS casing for wide-angle rearview vision.",
        "specifications": (
            "Lens: HD Convex Acrylic Mirror (Wide-Angle View)\n"
            "Handlebar Diameter: Fits 17.4mm - 22mm handlebar ends\n"
            "Adjustment: 360° Rotatable Base & 180° Foldable Arm\n"
            "Quantity: Pair (Left and Right Mirrors)\n"
            "Warranty: 6 Months Warranty\n"
            "Country of Origin: China"
        ),
    },
    {
        "id": 420,
        "name": "Bike Lock",
        "brand": "Generic",
        "price": Decimal("899.00"),
        "discount_price": Decimal("749.00"),
        "cost_price": Decimal("350.00"),
        "description": "High-security 5-digit resettable combination bicycle cable lock. Features a 12mm braided steel cable encased in a protective weather-resistant PVC coating with quick-mount frame bracket.",
        "specifications": (
            "Cable Thickness: 12mm Braided Hardened Steel\n"
            "Length: 1.2 Meters (4 Feet)\n"
            "Lock Mechanism: 5-Digit Resettable Combination (100,000 possible codes)\n"
            "Coating: Scratch-Resistant Weatherproof Vinyl PVC\n"
            "Mount: Easy-Mount Bike Frame Bracket Included\n"
            "Warranty: 1 Year Warranty\n"
            "Country of Origin: China"
        ),
    },
]

def run():
    updated_count = 0
    for item in UPDATES:
        p_id = item["id"]
        try:
            prod = Product.objects.get(id=p_id)
        except Product.DoesNotExist:
            print(f"Product ID {p_id} not found, skipping.")
            continue

        brand_name = item.get("brand")
        if brand_name:
            brand_obj, _ = Brand.objects.get_or_create(
                name=brand_name,
                defaults={"slug": slugify(brand_name)}
            )
            prod.brand = brand_obj

        prod.name = item["name"]
        prod.price = item["price"]
        prod.discount_price = item.get("discount_price")
        prod.cost_price = item.get("cost_price")
        prod.description = item["description"]
        prod.specifications = item["specifications"]

        prod.save()
        updated_count += 1
        print(f"[OK] Updated [{prod.id}] {prod.name}: Rs.{prod.price:,.2f} | Brand: {prod.brand.name if prod.brand else 'None'}")

    print(f"\nSuccessfully updated {updated_count} products with real market prices, detailed specifications, and brand links!")

if __name__ == "__main__":
    run()
