# Security notes

- Admin routes require Flask-Login authentication and an administrator role. Passwords use Werkzeug hashing, password changes are required for provisioned first-login accounts, and sensitive admin actions are audited.
- Flask-WTF protects state-changing forms with CSRF. Login, checkout, and global request rate limits are configured; production requires a shared rate-limit backend and strong environment-provided `SECRET_KEY`.
- Product prices, stock, shipping fees, quantities, and totals are read or recalculated on the server. Orders keep purchase-time product name, brand, unit price, quantity, and line total.
- Product uploads are restricted to accepted image types and size limits and saved with generated names. Static delivery denies database, environment, executable, and non-image upload files.
- WhatsApp order links use the configured and validated Egyptian number. The app does not store card details or claim gateway verification.
- Production still requires owner-controlled environment secrets, HTTPS, a configured shared limiter backend, a rotated admin password, restricted filesystem permissions, and private backups. Card payments, InstaPay proof review, and automated WhatsApp messaging are not implemented as connected integrations.
