# IMPORT DISTRICT release checklist

## Implemented

- Rebranded customer and admin templates, page titles, favicon, and hero copy as IMPORT DISTRICT.
- Updated the shared dark graphite and muted lime design tokens and removed invalid empty Cairo font declarations in favor of system Arabic-capable fonts.
- Kept the existing Three.js product viewer, local models, image fallback, reduced-motion handling, visibility pause, resize behavior, and pixel-ratio caps.
- Added optional product brand entry, display, search, filtering, and English name and brand snapshots on new order items. Existing order item snapshots are backfilled when the associated product still exists.
- Added catalog brand and price filters and sales-ranked sorting based on completed order data.
- Added a homepage best-seller collection that appears only when qualifying sales data exists.
- Replaced hardcoded WhatsApp destinations with the configured store number and hide WhatsApp actions when no valid number is configured.
- Added admin-editable metro pickup and home delivery rates, retaining the existing 60 EGP and 95 EGP defaults.
- Added explicit database migrations for product/order brand fields and shipping rates.
- Added PythonAnywhere release, backup/rollback, architecture, and security notes.

## Verification performed

- Baseline before edits: `60 passed`.
- Current suite: `63 passed` using `.\venv\Scripts\python.exe -m pytest -q`.
- Applied migrations to a disposable copy of the existing database and verified revision `20261020_05`, all 6 products and 3 orders preserved, new columns present, and existing known Monster products backfilled as `Monster Energy`.
- Applied migrations to the local database after creating `instance/monster-pre-import-district-20261020-025247.db`; verified product and order counts remained 6 and 3.
- Changed Python modules and migrations pass the targeted flake8 check.

## Remaining work before production readiness

- The 3D models are still beverage-can models. The bundled loader identifies itself as matching Three.js r136, but a browser render was not verified in this release: browser access is disabled in this Work environment. Recheck desktop/mobile rendering and fallback behavior before claiming the 3D display works.
- Product management supports a single brand string and primary image. Multiple galleries, variants, SKU/barcode, product specifications, comparison prices, optional per-product models, and full brand administration are not implemented.
- InstaPay is a payment preference only. The application has no proof upload/review lifecycle or payment status ledger. Card gateway integration is not implemented.
- COD availability remains gated by `COD_ENABLED`. The owner must confirm actual payment methods and configure the production environment.
- Delivery rates are editable; broader geographic eligibility, courier integration, and order-specific tracking are not implemented.
- The local suite is not a PythonAnywhere deployment or a browser-based responsive/accessibility audit. Confirm production Python/runtime support, WSGI paths, environment variables, HTTPS, uploads, backups, and smoke checks on the host.
- Do not call the app production-ready until the items above that are required by the business are completed and verified.
