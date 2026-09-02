import os
import django
import urllib.request
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from products.models import Product, ProductImage

# Mapping keywords to realistic image URLs
IMAGE_MAP = {
    # Mobiles
    'iphone': 'https://fdn2.gsmarena.com/vv/pics/apple/apple-iphone-15-pro-max-1.jpg',
    'samsung galaxy s24': 'https://fdn2.gsmarena.com/vv/pics/samsung/samsung-galaxy-s24-ultra-5g-sm-s928-1.jpg',
    'samsung galaxy z fold': 'https://fdn2.gsmarena.com/vv/pics/samsung/samsung-galaxy-z-fold5-5g-1.jpg',
    'samsung galaxy z flip': 'https://fdn2.gsmarena.com/vv/pics/samsung/samsung-galaxy-z-flip5-5g-1.jpg',
    'samsung galaxy s23': 'https://fdn2.gsmarena.com/vv/pics/samsung/samsung-galaxy-s23-fe-1.jpg',
    'samsung galaxy a55': 'https://fdn2.gsmarena.com/vv/pics/samsung/samsung-galaxy-a55-5g-1.jpg',
    'oneplus 12': 'https://fdn2.gsmarena.com/vv/pics/oneplus/oneplus-12-1.jpg',
    'pixel 8': 'https://fdn2.gsmarena.com/vv/pics/google/google-pixel-8-pro-1.jpg',
    'pixel 7': 'https://fdn2.gsmarena.com/vv/pics/google/google-pixel-7a-1.jpg',
    'xiaomi 14': 'https://fdn2.gsmarena.com/vv/pics/xiaomi/xiaomi-14-ultra-1.jpg',
    'motorola edge': 'https://fdn2.gsmarena.com/vv/pics/motorola/motorola-edge-50-pro-1.jpg',
    'nothing phone': 'https://fdn2.gsmarena.com/vv/pics/nothing/nothing-phone2a-1.jpg',
    'vivo x100': 'https://fdn2.gsmarena.com/vv/pics/vivo/vivo-x100-pro-1.jpg',
    'vivo v30': 'https://fdn2.gsmarena.com/vv/pics/vivo/vivo-v30-pro-1.jpg',
    'oppo find': 'https://fdn2.gsmarena.com/vv/pics/oppo/oppo-find-x7-1.jpg',
    'oppo reno': 'https://fdn2.gsmarena.com/vv/pics/oppo/oppo-reno11-1.jpg',
    'realme 12': 'https://fdn2.gsmarena.com/vv/pics/realme/realme-12-pro-plus-1.jpg',
    'poco x6': 'https://fdn2.gsmarena.com/vv/pics/xiaomi/xiaomi-poco-x6-pro-1.jpg',
    'iqoo 12': 'https://fdn2.gsmarena.com/vv/pics/vivo/vivo-iqoo-12-1.jpg',
    'ipad pro': 'https://fdn2.gsmarena.com/vv/pics/apple/apple-ipad-pro-13-2024-1.jpg',
    'ipad air': 'https://fdn2.gsmarena.com/vv/pics/apple/apple-ipad-air-13-2024-1.jpg',
    'galaxy tab': 'https://fdn2.gsmarena.com/vv/pics/samsung/samsung-galaxy-tab-s9-ultra-1.jpg',
    'oneplus pad': 'https://fdn2.gsmarena.com/vv/pics/oneplus/oneplus-pad-1.jpg',
    'lenovo tab': 'https://fdn2.gsmarena.com/vv/pics/lenovo/lenovo-tab-p12-1.jpg',
    'smartphone': 'https://cdn.dummyjson.com/product-images/1/thumbnail.jpg',
    'phone': 'https://cdn.dummyjson.com/product-images/2/thumbnail.jpg',
    
    # Laptops & Computing
    'macbook pro': 'https://store.storeimages.cdn-apple.com/4668/as-images.apple.com/is/mbp14-spacegray-select-202310?wid=904&hei=840&fmt=jpeg&qlt=90&.v=1697230830200',
    'macbook air': 'https://store.storeimages.cdn-apple.com/4668/as-images.apple.com/is/mba13-midnight-select-202402?wid=904&hei=840&fmt=jpeg&qlt=90&.v=1708367688034',
    'dell xps': 'https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-client-products/notebooks/xps-notebooks/xps-15-9530/media-gallery/touch/silver/notebook-xps-15-9530-t-silver-gallery-1.psd?fmt=png-alpha&pscan=auto&scl=1&hei=402&wid=556&qlt=100,1&resMode=sharp2&size=556,402&chrss=full',
    'asus rog': 'https://dlcdnwebimgs.asus.com/gain/497A91DE-4B28-4BA6-A4C8-580798C5DFEE/w1000/h732',
    'legion': 'https://p1-ofp.static.pub/fes/cms/2023/02/10/jf8wrtw02v8x3j14ptx7okp7r3z28g639017.png',
    'hp omen': 'https://in-media.apjonlinecdn.com/catalog/product/cache/b3b166914d87ce343d4dc5ec5117b502/c/0/c08482483.png',
    'predator': 'https://images-cdn.ubuy.co.in/634e32047ed6f3692d477b83-acer-predator-helios-300-ph315-54-760s.jpg',
    'msi stealth': 'https://asset.msi.com/resize/image/global/product/product_167272826955a5b5832a8138402db0d2105e45a274.png62405b38c58fe0f07fcef2367d8a9ba1/1024.png',
    'razer blade': 'https://assets2.razerzone.com/images/pnx.assets/e8a3a0bc7f21287957e8ec16f2c3dbf9/razer-blade-15-2023-laptop-500x500.png',
    'alienware': 'https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-client-products/notebooks/alienware-notebooks/alienware-m16-amd/media-gallery/notebook-alienware-m16-amd-gallery-1.psd?fmt=pjpg&pscan=auto&scl=1&hei=402&wid=613&qlt=100,1&resMode=sharp2&size=613,402&chrss=full',
    'inspiron': 'https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-client-products/notebooks/inspiron-15-3520/media-gallery/in3520-cnb-00000ff090-sl.psd?fmt=pjpg&pscan=auto&scl=1&wid=3399&hei=2247&qlt=100,1&resMode=sharp2&size=3399,2247&chrss=full',
    'zenbook': 'https://dlcdnwebimgs.asus.com/gain/9C7370AF-4C5C-4DF0-BA6D-C16B8859A41C/w1000/h732',
    'playstation 5': 'https://gmedia.playstation.com/is/image/SIEPDC/ps5-product-thumbnail-01-en-14sep21?$facebook$',
    'xbox series': 'https://compass-ssl.xbox.com/assets/b9/0a/b90ad58f-9950-44a7-87fa-1ee8f0b6a90e.jpg?n=XSX_Page-Hero-0_768x792.jpg',
    'nintendo switch': 'https://assets.nintendo.com/image/upload/f_auto/q_auto/dpr_1.5/c_scale,w_400/ncom/en_US/switch/site-design-update/hardware/switch/ndc-tv-console-mob',
    'steam deck': 'https://cdn.akamai.steamstatic.com/steamdeck/images/steamdeck_hero_device.png',
    'laptop': 'https://cdn.dummyjson.com/product-images/6/thumbnail.png',
    
    # Appliances
    'split ac': 'https://www.lg.com/in/images/air-conditioners/md07584100/gallery/RS-Q19ENZE-Air-Conditioners-Front-View-MZ-01.jpg',
    'refrigerator': 'https://images.samsung.com/is/image/samsung/p6pim/in/rt28c3053s8-hl/gallery/in-rt3000k-452377-rt28c3053s8-hl-535359287?$650_519_PNG$',
    'washing machine': 'https://www.lg.com/in/images/washing-machines/md07540203/gallery/FHM1208SDM-Washing-Machines-Front-View-MZ-01.jpg',
    'led tv': 'https://m.media-amazon.com/images/I/81Rx+hS9QzL._SL1500_.jpg',
    'air fryer': 'https://m.media-amazon.com/images/I/61N+QWUPUOL._SL1500_.jpg',
    'vacuum cleaner': 'https://m.media-amazon.com/images/I/61b7LhWnJqL._SL1500_.jpg',
    'dishwasher': 'https://m.media-amazon.com/images/I/71Z0G6X8yNL._SL1500_.jpg',
    'microwave': 'https://m.media-amazon.com/images/I/71wL+RkZt0L._SL1500_.jpg',
    'mixer grinder': 'https://m.media-amazon.com/images/I/71uBq03+k4L._SL1500_.jpg',
    'water purifier': 'https://m.media-amazon.com/images/I/51H+QoB7U2L._SL1000_.jpg',
    'water heater': 'https://m.media-amazon.com/images/I/61aK0bL9gWL._SL1500_.jpg',
    'chimney': 'https://m.media-amazon.com/images/I/61WfQ7i-2XL._SL1500_.jpg',
    
    # Fashion
    'air force 1': 'https://static.nike.com/a/images/t_PDP_1728_v1/f_auto,q_auto:eco/b7d9211c-26e7-431a-ac24-b0540fb3c00f/air-force-1-07-shoes-WrLlWX.png',
    'ultraboost': 'https://assets.adidas.com/images/h_840,f_auto,q_auto,fl_lossy,c_fill,g_auto/c5b058c426314f2ea0e6aef600cc1b97_9366/Ultraboost_Light_Shoes_Black_HQ6351_01_standard.jpg',
    'puma suede': 'https://images.puma.com/image/upload/f_auto,q_auto,b_rgb:fafafa,w_2000,h_2000/global/374915/01/sv01/fnd/IND/fmt/png/Suede-Classic-XXI-Sneakers',
    'levis': 'https://lsco.scene7.com/is/image/lsco/045115160-front-pdp?fmt=jpeg&qlt=70,1&op_sharpen=0&resMode=sharp2&op_usm=0.8,1,10,0&fit=crop,0&wid=450&hei=600',
    'zara': 'https://static.zara.net/photos///2023/I/0/2/p/0722/350/250/2/w/850/0722350250_1_1_1.jpg?ts=1693406322987',
    'h&m': 'https://lp2.hm.com/hmgoepprod?set=quality%5B79%5D%2Csource%5B%2F88%2F4f%2F884fbc96cb4d51abf19bb4f981503db3d242ef99.jpg%5D%2Corigin%5Bdam%5D%2Ccategory%5Bmen_hoodies_sweatshirts_hoodies%5D%2Ctype%5BDESCRIPTIVESTILLLIFE%5D%2Cres%5Bm%5D%2Chmver%5B2%5D&call=url[file:/product/main]',
    'air max 90': 'https://static.nike.com/a/images/t_PDP_1728_v1/f_auto,q_auto:eco/e9d41315-99d7-463d-82d2-28df5cd85871/air-max-90-shoes-kRsBW3.png',
    'stan smith': 'https://assets.adidas.com/images/h_840,f_auto,q_auto,fl_lossy,c_fill,g_auto/6146cbf932d44fc1a477ac8f00fd764a_9366/Stan_Smith_Shoes_White_FX5500_01_standard.jpg',
    't-shirt': 'https://cdn.dummyjson.com/product-images/51/thumbnail.jpg',
    'shoes': 'https://cdn.dummyjson.com/product-images/56/thumbnail.jpg',
    'jacket': 'https://cdn.dummyjson.com/product-images/54/thumbnail.jpg',
    
    # Groceries
    'salt': 'https://m.media-amazon.com/images/I/61M6r-cR2-L._SL1000_.jpg',
    'atta': 'https://m.media-amazon.com/images/I/81xU-Yw2jUL._SL1500_.jpg',
    'rice': 'https://m.media-amazon.com/images/I/71Yf1EIt1-L._SL1500_.jpg',
    'oil': 'https://m.media-amazon.com/images/I/51w7rO9QnTL._SL1000_.jpg',
    'butter': 'https://m.media-amazon.com/images/I/61bZJ9K9R9L._SL1500_.jpg',
    'coffee': 'https://m.media-amazon.com/images/I/71rA4+CgW6L._SL1500_.jpg',
    'tea': 'https://m.media-amazon.com/images/I/61Vd1-o79mL._SL1000_.jpg',
    'maggi': 'https://m.media-amazon.com/images/I/81xZ9P02ZTL._SL1500_.jpg',
    'dairy milk': 'https://m.media-amazon.com/images/I/611Z23tO8VL._SL1500_.jpg',
    'cookies': 'https://m.media-amazon.com/images/I/81V2fD30JqL._SL1500_.jpg',
    'parle-g': 'https://m.media-amazon.com/images/I/61y8n0n9xGL._SL1500_.jpg',
    'bhujia': 'https://m.media-amazon.com/images/I/71r2+XWjHHL._SL1500_.jpg',
    'lays': 'https://m.media-amazon.com/images/I/71X8k4gB8qL._SL1500_.jpg',
    'kurkure': 'https://m.media-amazon.com/images/I/71S3+2e-S3L._SL1500_.jpg',
    'juice': 'https://m.media-amazon.com/images/I/71E3YQ8jM0L._SL1500_.jpg',
    'coca-cola': 'https://m.media-amazon.com/images/I/51v8nyxSOYL._SL1500_.jpg',
    'milk': 'https://m.media-amazon.com/images/I/61S4h8+zpwL._SL1500_.jpg',
    'dal': 'https://m.media-amazon.com/images/I/81K4g9g2YBL._SL1500_.jpg',
    'masala': 'https://m.media-amazon.com/images/I/81+2V5q21lL._SL1500_.jpg',
    'ketchup': 'https://m.media-amazon.com/images/I/71P4qB7wVIL._SL1500_.jpg',
    'jam': 'https://m.media-amazon.com/images/I/71N1+0+a+vL._SL1500_.jpg',
    'honey': 'https://m.media-amazon.com/images/I/61p-3mC26kL._SL1500_.jpg',
    'surf excel': 'https://m.media-amazon.com/images/I/61P9zZ8P-yL._SL1500_.jpg',
    'vim': 'https://m.media-amazon.com/images/I/61s0O1tqKjL._SL1500_.jpg',
    'lizol': 'https://m.media-amazon.com/images/I/61o3N6b-Q9L._SL1500_.jpg',
    'colgate': 'https://m.media-amazon.com/images/I/61-g-0vNqGL._SL1500_.jpg',
    'dettol': 'https://m.media-amazon.com/images/I/51b7+7W2v-L._SL1500_.jpg',
    
    # Flash Deals & General
    'smart watch': 'https://m.media-amazon.com/images/I/61ZjlBOvn-L._SL1500_.jpg',
    'bluetooth tws': 'https://m.media-amazon.com/images/I/61Vd1-o79mL._SL1000_.jpg',
    'airdopes': 'https://m.media-amazon.com/images/I/516vC+1eA9L._SL1500_.jpg',
    'power bank': 'https://m.media-amazon.com/images/I/71lVwl3q-kL._SL1500_.jpg',
    'pendrive': 'https://m.media-amazon.com/images/I/61Uxg-NWUqL._SL1500_.jpg',
    'flash drive': 'https://m.media-amazon.com/images/I/61Uxg-NWUqL._SL1500_.jpg',
    'mouse': 'https://m.media-amazon.com/images/I/5144bV3RbwL._SL1500_.jpg',
    'router': 'https://m.media-amazon.com/images/I/51R2a9p-vNL._SL1000_.jpg',
    'hdmi cable': 'https://m.media-amazon.com/images/I/61O2h2-1JkL._SL1500_.jpg',
    'keyboard': 'https://m.media-amazon.com/images/I/61vYVwH1x-L._SL1500_.jpg',
    'gamepad': 'https://m.media-amazon.com/images/I/611Z23tO8VL._SL1500_.jpg',
    'headphones': 'https://m.media-amazon.com/images/I/61kWB+uzR2L._SL1500_.jpg',
    'earphones': 'https://m.media-amazon.com/images/I/61O0rXhopTLL._SL1500_.jpg',
    'tempered glass': 'https://m.media-amazon.com/images/I/61Q6Z3P9a+L._SL1500_.jpg',
    'charger': 'https://m.media-amazon.com/images/I/51I3UjD-Q1L._SL1500_.jpg',
    'batteries': 'https://m.media-amazon.com/images/I/71Y+z4u-jGL._SL1500_.jpg',
    'fragrance': 'https://m.media-amazon.com/images/I/61V1h+E4z3L._SL1500_.jpg',
    'chopper': 'https://m.media-amazon.com/images/I/51zJ8U+Uu6L._SL1500_.jpg',
    'flask': 'https://m.media-amazon.com/images/I/611+LpX8PqL._SL1500_.jpg',
    'pen': 'https://m.media-amazon.com/images/I/61gPqT-5q1L._SL1500_.jpg',
    'notebook': 'https://m.media-amazon.com/images/I/81p-e3d82hL._SL1500_.jpg',
    'face wash': 'https://m.media-amazon.com/images/I/51tU5B12fKL._SL1000_.jpg',
    'razor': 'https://m.media-amazon.com/images/I/71y+K5XGg9L._SL1500_.jpg',
    'condoms': 'https://m.media-amazon.com/images/I/71H-Zf0P8sL._SL1500_.jpg',
    'room spray': 'https://m.media-amazon.com/images/I/61O0rXhopTLL._SL1500_.jpg',
    'mosquito': 'https://m.media-amazon.com/images/I/61U0o+kR0pL._SL1500_.jpg'
}

def main():
    print("Fixing image URLs...")
    products = Product.objects.all()
    updated_count = 0
    
    for product in products:
        name_lower = product.name.lower()
        matched_url = None
        
        for keyword, url in IMAGE_MAP.items():
            if keyword in name_lower:
                matched_url = url
                break
                
        if not matched_url:
            cat_slug = product.category.slug
            if cat_slug == 'mobiles':
                matched_url = IMAGE_MAP['smartphone']
            elif cat_slug == 'gaming':
                matched_url = IMAGE_MAP['laptop']
            elif cat_slug == 'appliances':
                matched_url = IMAGE_MAP['refrigerator']
            elif cat_slug == 'fashion':
                matched_url = IMAGE_MAP['t-shirt']
            elif cat_slug == 'groceries':
                matched_url = IMAGE_MAP['salt']
            else:
                matched_url = 'https://m.media-amazon.com/images/I/71lVwl3q-kL._SL1500_.jpg'
                
        if matched_url:
            image = ProductImage.objects.filter(product=product).first()
            if image and image.image_url != matched_url:
                image.image_url = matched_url
                image.save()
                updated_count += 1
                
    print(f"Updated {updated_count} product images with realistic links!")

if __name__ == "__main__":
    main()
