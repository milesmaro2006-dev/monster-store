# IMPORT DISTRICT deployment

## Local run

From `D:\backend\monster-store` in PowerShell:

```powershell
.\venv\Scripts\python.exe -m flask --app run.py db upgrade
.\venv\Scripts\python.exe run.py
```

The development server listens on port 5000. Do not expose it publicly.

## PythonAnywhere release checklist

1. Back up the SQLite database and uploaded media. Keep backups outside `app/static`.
2. Pull the reviewed code in the configured checkout and install `requirements.txt` in the PythonAnywhere virtualenv.
3. Set production environment variables outside the repository: `FLASK_ENV=production`, a unique `SECRET_KEY`, `DATABASE_URL` or `SQLITE_DATABASE_PATH`, `SESSION_COOKIE_SECURE=true`, `RATELIMIT_STORAGE_URI`, `PUBLIC_BASE_URL`, and the intended `COD_ENABLED` value.
4. Check the WSGI file uses the correct checkout and virtualenv and imports `create_app("production")`. Keep debug mode disabled.
5. Run `flask --app run.py db upgrade`. This release adds nullable product brand and order name/brand snapshot fields plus editable metro and home delivery fees; existing product, stock, order, and admin rows are preserved.
6. Confirm SQLite and upload paths are writable by the web app. Product images are served from `app/static/uploads`; database backups and payment evidence must remain private.
7. Configure store contact information, including WhatsApp, and delivery details in the admin portal. InstaPay remains manual. Card payments require a gateway integration and merchant credentials and are not live.
8. Reload the web app. Smoke-check `/`, `/products`, `/cart`, `/checkout/`, admin login, `/health`, image loading, and 3D fallback behavior.
9. If startup or migration fails, restore the database backup and prior code revision, restore the prior WSGI configuration if it changed, and reload.

## Configuration limits

Production configuration requires a strong secret key and a shared rate-limit backend. Checkout remains disabled unless `COD_ENABLED=true`; set it only when the owner confirms this payment option. The app uses SQLite by default and does not include card-gateway or WhatsApp Business API credentials or integrations.
