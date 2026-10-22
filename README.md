# IMPORT DISTRICT

Arabic-first Flask storefront for an independent Egyptian retailer of imported drinks, snacks, and confectionery. IMPORT DISTRICT is not an official store for any manufacturer. Local development uses Flask, Jinja, SQLite, and the existing application modules.

## Requirements

- Python 3.10 or later (the current virtual environment uses Python 3.14)
- pip
- Windows PowerShell or a POSIX shell

## Install and run locally

### Windows PowerShell

```powershell
cd D:\backend\monster-store
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

If `.env` already exists, keep it and edit only the values you mean to change. Set `SECRET_KEY` to a long random value for any shared or deployed environment. The application reads `.env` from the project root.

### Linux / macOS

```sh
cd /path/to/monster-store
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
```

If `.env` already exists, do not overwrite it. Configure a strong random `SECRET_KEY` before exposing the app beyond your local machine.

### Initialize and start

```sh
flask --app run.py init-db
python run.py
```

Open `http://127.0.0.1:5000`. `python run.py` binds to localhost only and enables debug behavior in development. This is a local development server, not a public deployment. The default SQLite database is `instance/monster.db`; back it up before deployment or migration work.

For local UI experimentation only, `flask --app run.py seed` adds sample categories and products with example prices and stock. Review and replace every sample value before taking real orders. The command is disabled in production. It is safe to run repeatedly in development.

## Environment configuration

See [.env.example](.env.example). Important settings:

- `SECRET_KEY`: required to be explicitly set to a strong value in production.
- `FLASK_ENV`: use `development` locally and `production` for production configuration.
- `DATABASE_URL`: optional SQLAlchemy URL. Without it, SQLite at `instance/monster.db` is used.
- `SESSION_COOKIE_SECURE`: enable only behind HTTPS; production configuration enables secure cookies.
- `ADMIN_URL_PREFIX`: protected dashboard path; defaults to `/portal-spidey` and is checked for unsafe or reserved paths.
- `STORE_TIMEZONE`: timezone for daily dashboard metrics; defaults to `Africa/Cairo`.
- `RATELIMIT_STORAGE_URI`: production must use a shared store such as Redis; `memory://` is for local development only.
- `PUBLIC_BASE_URL`: optional canonical URL after the real public domain is configured.
- `MAX_CART_QTY`: maximum quantity of one product per cart line.
- `COD_ENABLED`: defaults to `false`. Set to `true` only after confirming that the owner supports cash on delivery; checkout remains unavailable until then. Online payment is not implemented.

Never commit `.env`, customer data, or admin credentials. Do not copy credentials into this README.

## Products, stock, and orders

1. Apply schema changes to an existing database with `flask --app run.py db upgrade`.
2. Create the initial admin with `flask --app run.py admin create-user --username Spidey`. The command securely prompts for the password twice, stores only a Werkzeug password hash, and refuses to change an existing account. Initial accounts must change their password on first login.
3. Sign in at `/portal-spidey/login` (or the configured `ADMIN_URL_PREFIX` plus `/login`). Unauthenticated and non-admin access receives a 404.
4. Add products under **المنتجات**, setting the real Arabic/English names, brand, price in EGP, available stock, image, and optional category. Brand names and categories are data, so adding a brand does not require a code change. Edit products to update price or stock; archive products that should leave the catalog.
5. Review customer details and move orders through the allowed status workflow under **الطلبات**. Orders are persisted in SQLite and the application deducts stock when checkout succeeds. Cancelling an order restores its stock once.

To reset an existing admin password explicitly, run `flask --app run.py admin reset-password --username Spidey`. The command asks for a temporary password without echoing it and forces another change at next login. Do not put credentials in shell arguments, source files, or `.env`.

After the owner confirms cash on delivery is available, set `COD_ENABLED=true` in `.env` and restart the app. Until then, the checkout page explains that payment options must be confirmed and does not accept orders. When enabled, orders are saved as pending and the seller confirms the delivery arrangement with the customer. There is no online payment integration or automated email/WhatsApp notification.

## Tests and checks

Install development tools and run the suite:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest
```

Tests use an in-memory database. They do not need or modify the local `instance/monster.db`. Run the application health endpoint at `/health` to check its database connection.

## Assets and troubleshooting

- The hero carousel reads `app/static/img/hero/can-1.png` through `can-6.png` when present. Product cards use the image path saved for each product and fall back to `app/static/img/placeholder.svg` if it is missing.
- If an image does not appear, check its exact filename and case under `app/static`, then confirm the saved product image path is relative to that directory (for example `uploads/example.webp`). The browser network panel should show a successful `/static/...` request.
- The checked-in Cairo font files are empty, so the site uses the system font fallback. No remote font service is required.
- If port 5000 is busy, stop the other local server or change the port in `run.py` for local development.
- If the database is missing tables, run `flask --app run.py init-db`. Use migrations for changes to an existing database; `init-db` creates tables but does not alter existing schemas.
- If startup fails, activate the virtual environment, reinstall `requirements.txt`, and inspect the traceback and `logs/app.log`. Keep secret values and customer data out of shared logs.

## Before public deployment

The app has not been deployed by this project setup. For the existing PythonAnywhere deployment, configure the WSGI file to point at this checkout and its virtual environment, set production environment variables outside source control, install `requirements.txt`, back up the database, and apply `flask --app run.py db upgrade` before reloading the web app. Confirm static and uploaded-media paths, HTTPS, secure cookies, a strong `SECRET_KEY`, shared rate-limit storage, and owner-managed admin credentials. Do not use Flask's development server on a public network.

Set real product prices and stock, delivery zones and fees, confirm payment options (and enable `COD_ENABLED` only if COD is supported), and configure contact details before accepting orders. The current checkout intentionally does not claim fixed delivery availability or times. Review the guides in `docs/` for architecture, security, backups, and deployment notes.
