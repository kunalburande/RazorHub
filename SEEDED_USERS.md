# Seeded Test Users — RazorHub Marketplace

> [!NOTE]
> All seeded users below **automatically bypass OTP verification** during login.
> Regular users registering via the public signup flow still go through standard email verification.

---

## 🛡️ Admins (Superuser / Staff)

| Name | Email | Username | Password | Role |
|---|---|---|---|---|
| Priya Sharma | `priya.sharma@razorhub.com` | `priya.sharma` | `Razor@Admin01` | Admin / Staff |
| Rahul Verma | `rahul.verma@razorhub.com` | `rahul.verma` | `Razor@Admin02` | Admin / Staff |
| Vikram Reddy | `vikram.reddy@razorhub.com` | `vikram.reddy` | `Razor@Admin03` | Admin / Staff |
| System Admin | `admin@razorhub.in` | `admin@razorhub.in` | `RazorHub@Admin2024` | Admin / Staff |

---

## 🏪 Sellers & Stores

> **Seller Registration / Login Code:** `mafia` (or `demo`)

| Name | Email | Username | Password | Store Name | Category Focus |
|---|---|---|---|---|---|
| Ananya Gupta | `ananya.gupta@razorhub.com` | `ananya.gupta` | `Razor@Seller01` | Ananya Electronics Hub | Electronics, Laptops, Audio, Gaming |
| Amit Singh | `amit.singh@razorhub.com` | `amit.singh` | `Razor@Seller02` | Amit Fashion House | Fashion, Men's & Women's Clothing |
| Kavya Iyer | `kavya.iyer@razorhub.com` | `kavya.iyer` | `Razor@Seller03` | Kavya Photo Studio | Photography & Studio Equipment |
| Isha Banerjee | `isha.banerjee@razorhub.com` | `isha.banerjee` | `Razor@Seller04` | Isha Home & Living | Furniture, Appliances, Home & Kitchen, Pets |
| Ramesh Sinha | `ramesh.sinha@razorhub.com` | `ramesh.sinha` | `Razor@Seller05` | Sinha Sports & Sneakers | Sneakers, Sports & Fitness, Automotive |
| Saanvi Joshi | `saanvi.joshi@razorhub.com` | `saanvi.joshi` | `Razor@Seller06` | Joshi Jewels & Accessories | Jewellery, Watches, Accessories |
| Deepak Tiwari | `deepak.tiwari@razorhub.com` | `deepak.tiwari` | `Razor@Seller07` | Deepak Grocery & Books | Groceries, Books, Stationery |
| TechVista Seller | `seller@techvista.in` | `seller@techvista.in` | `Seller@2024` | TechVista Electronics | Consumer Electronics |
| StyleCraft Seller | `seller@stylecraft.in` | `seller@stylecraft.in` | `Seller@2024` | StyleCraft Fashion | Apparel & Accessories |
| HomeEssentials | `seller@homeessentials.in` | `seller@homeessentials.in` | `Seller@2024` | HomeEssentials India | Home & Living |
| GlamourBox Seller | `seller@glamourbox.in` | `seller@glamourbox.in` | `Seller@2024` | GlamourBox | Beauty & Care |
| Saanvi Store | `seller.saanvi0@store.in` | `seller.saanvi0` | `Seller@2024` | Pillai Enterprises | General Retail |

---

## 👥 Customer Accounts

| Name | Email | Username | Password |
|---|---|---|---|
| Sneha Patel | `sneha.patel@razorhub.com` | `sneha.patel` | `Razor@Cust01` |
| Rohit Das | `rohit.das@razorhub.com` | `rohit.das` | `Razor@Cust02` |
| Neha Bose | `neha.bose@razorhub.com` | `neha.bose` | `Razor@Cust03` |
| Suresh Chatterjee | `suresh.chatterjee@razorhub.com` | `suresh.chatterjee` | `Razor@Cust04` |
| Pooja Mishra | `pooja.mishra@razorhub.com` | `pooja.mishra` | `Razor@Cust05` |
| Vikram Mehta | `vikram.mehta@razorhub.com` | `vikram.mehta` | `Razor@Cust06` |
| Riya Pandey | `riya.pandey@razorhub.com` | `riya.pandey` | `Razor@Cust07` |
| Manoj Yadav | `manoj.yadav@razorhub.com` | `manoj.yadav` | `Razor@Cust08` |
| Ajay Kulkarni | `ajay.kulkarni@razorhub.com` | `ajay.kulkarni` | `Razor@Cust09` |
| Diya Deshpande | `diya.deshpande@razorhub.com` | `diya.deshpande` | `Razor@Cust10` |
| Aarav Singh | `aarav.singh@customer.in` | `aarav.singh@customer.in` | `Customer@2024` |
| Diya Mehta | `diya.mehta@customer.in` | `diya.mehta@customer.in` | `Customer@2024` |
| Vihaan Kumar | `vihaan.kumar@customer.in` | `vihaan.kumar@customer.in` | `Customer@2024` |
| Ananya Gupta | `ananya.gupta@customer.in` | `ananya.gupta@customer.in` | `Customer@2024` |
| Reyansh Iyer | `reyansh.iyer@customer.in` | `reyansh.iyer@customer.in` | `Customer@2024` |
| Isha Patel | `isha.patel@customer.in` | `isha.patel@customer.in` | `Customer@2024` |
| Kabir Das | `kabir.das@customer.in` | `kabir.das@customer.in` | `Customer@2024` |
| Myra Joshi | `myra.joshi@customer.in` | `myra.joshi@customer.in` | `Customer@2024` |
| Aryan Nair | `aryan.nair@customer.in` | `aryan.nair@customer.in` | `Customer@2024` |
| Saanvi Rao | `saanvi.rao@customer.in` | `saanvi.rao@customer.in` | `Customer@2024` |

---

## 🔑 Key Features
- **OTP Bypass**: All users listed above bypass OTP on `/api/token/` login and receive JWT tokens directly.
- **Role Redirection**: Admins go to `/admin`, Sellers go to `/seller`, Customers go to `/dashboard`.
- **Database**: Production NeonDB PostgreSQL.
