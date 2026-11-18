# WasteConnect

> One's Waste, Another's Resource.

WasteConnect is a marketplace for recyclable waste. Individuals, small local resellers (kabadiwalas), societies, offices, businesses, aggregators and recyclers can list material, post what they want to buy, and trade with each other.

**Status:** planning and early build. Nothing here has been validated with real users yet. Items marked *(assumption)* are untested.

## What it does

- **Dry waste is the main product.** Wet waste (compost, biogas and similar) is a separate module, designed for from the start but built later on the same foundation.
- **Open to everyone, not only businesses.**
  - Individuals sell to local resellers.
  - Resellers sell in bulk to aggregators and recyclers.
  - Societies, offices and businesses sell to resellers, aggregators or recyclers.
- **Pilot location** *(assumption)*: Pune, starting with one neighbourhood and a handful of resellers. Candidate areas to research: Hinjawadi, Wakad, Baner, Pimpri-Chinchwad, Hadapsar, Kharadi.
- **Pickups** are done by the reseller or buyer. The platform does not run logistics in the MVP.
- **Individuals use the platform free.** Revenue model is undecided (likely subscriptions or paid leads, to be decided after the pilot).

## Materials

| | Materials |
|---|---|
| **At launch** | Paper, newspaper, cardboard, common plastics (PET, HDPE), common metals (iron, steel, aluminium, copper), possibly glass |
| **Later** | Textile, rubber, industrial scrap, construction debris |
| **Not supported at first** | Regulated or risky waste (e-waste, batteries, biomedical, hazardous); organic/food waste until the wet module exists |

Categories are data, not code. Each category defines: stream (dry/wet), unit, quality grades, `is_perishable`, `is_recurring_pickup`, `allows_zero_or_negative_price`, `allowed_seller_types`, `allowed_buyer_types`. Wet categories exist but are switched off at launch.

## Account types

| Type | Sells | Buys | Notes |
|---|---|---|---|
| individual | yes | no | free to use; can list immediately |
| reseller | yes | yes | the key user |
| business | yes | yes | |
| society | yes | no | |
| aggregator | yes | yes | |
| recycler | no | yes | |
| processor | no | yes | for the wet module |
| admin | n/a | n/a | platform staff |

Roles belong to the **account**, not the user. Accounts carry `can_sell` and `can_buy` flags, and one user can belong to several accounts. Non-individual sellers need admin verification before listing.

## MVP scope

1. Registration and login (a user can belong to several accounts)
2. Account profile with manual admin verification
3. Waste categories as configuration
4. Listings: photos, quantity, quality, fixed or negotiable price, pickup area
5. Buyer requirements (reverse marketplace)
6. Browse and search by material, area, pincode, quantity, verified-only
7. Simple matching with notifications
8. Offers and counteroffers with history and expiry
9. Orders with a strict status flow and weight records at collection and delivery
10. In-app and email notifications
11. Admin dashboard

### Out of scope for the MVP

Payments and commission, ratings, disputes, live GPS, route optimisation, AI features, mobile apps, regulated waste, and the wet-waste module (designed for, built later).

## Design rules

- **Orders are a state machine:** confirmed, pickup scheduled, collected, delivered, then accepted / partially accepted / rejected, then completed. Cancellation is allowed before collection. Every change is written to a status-history table.
- **Listed, collected, delivered, accepted and processed are separate events.** Never claim waste was recycled just because it was collected.
- **Weights are records**, one at collection and one at delivery, so disputes have evidence.
- **Completed orders are never edited.** Corrections go to an audit log.
- **Permissions are enforced in the backend**, not only in the UI.
- **Offers are separate from orders.** An accepted offer creates the order.
- **Money and weight use `Numeric`**, never float.

## Tech stack

- **Architecture:** modular monolith, backend-first, API-first
- **Backend:** Python, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic
- **Database:** PostgreSQL on Neon (pooled URL for the app, direct URL for migrations, a `dev` branch for development)
- **Auth:** JWT, Argon2 password hashing
- **Frontend:** web application, mobile-friendly (resellers and households will mostly use phones); framework not yet chosen
- **Deliberately not used at first:** Redis, Celery, PostGIS, microservices. Matching is plain SQL on category, area, pincode and quantity.

## Core tables (about 15)

`users`, `accounts`, `account_members`, `account_documents`, `waste_categories`, `listings`, `listing_images`, `requirements`, `offers`, `orders`, `order_status_history`, `weight_records`, `notifications`, `audit_logs`

## Build order

0. Project setup and `AGENTS.md` rules file
1. Backend skeleton and Neon connection
2. Accounts and auth
3. Admin verification
4. Categories as configuration (dry waste seeded, wet waste off)
5. Listings with filters and ownership permissions
6. Buyer requirements
7. Matching and notifications
8. Offers and counteroffers
9. Orders, status flow and weight records
10. Admin dashboard endpoints
11. Frontend (after the UI approach is chosen)

Each step ends with passing tests (including permission tests and order state-machine tests) and a Git commit.

## Known risks

- **Marketplace liquidity** is the main risk: enough real buyers and sellers in one area and material.
- **Informal trade** makes commission easy to bypass.
- **Individual pickups** can cost more than the material is worth, so the reseller does their own pickups.
- **Trust and safety** for home pickups: phone verification, verified resellers, pickup OTP.
- **Rigged scales** are a common household complaint; a visible rate card helps.
- **Existing players** (e.g. Recykal, RecyIndia, ScrapUncle, The Kabadiwala, SWaCH Pune) must be researched with live sources before assuming any gap. Wet waste in Pune already has organisations working on it, so partner-vs-competitor needs deciding.
- **Validation:** talk to 10 to 15 resellers, aggregators, recyclers, societies and hotels before heavy building.
- **Regulation:** verify current Indian rules before building any wet-waste or regulated-waste workflow.

## Open questions

- Hindi/Marathi support: design in from the start, or add after the pilot?
- Pilot partners, and which payment method resellers actually want (cash or UPI)
- Revenue model
- Frontend framework

## Local setup

To be filled in during Step 0 (Windows, Python 3.12+, Git, Neon connection strings in an untracked `.env`).

## Repository notes

- Never commit `.env` or any connection string.
- Rules for AI coding tools live in `AGENTS.md`.
