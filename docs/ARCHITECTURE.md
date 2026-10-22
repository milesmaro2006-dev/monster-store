# Application architecture

The app is a Flask application factory with separate storefront, cart, checkout, and admin blueprints. Jinja templates render Arabic-first pages with an English language switch. SQLAlchemy models store products, categories, store settings, delivery areas, orders, item price and brand snapshots, order history, admin users, and audit events.

The customer cart is stored in the signed Flask session. Checkout reads current product prices and inventory on the server, validates availability, writes an order and item snapshots in one database transaction, and decrements stock. The admin portal supports product and category CRUD, stock and order operations, store contact settings, and configurable metro and home delivery rates.

Static assets, including the Three.js viewer and product images, are served from `app/static`. The viewer uses local GLB and image assets, observes visibility, caps pixel ratio, respects reduced motion, and switches to an image when WebGL or model loading fails. Product uploads are written under `app/static/uploads`; private files must remain outside static paths.

SQLite is the default local and deployment database. Existing schemas are changed through Flask-Migrate/Alembic, not `create_all()`. Apply migrations from a backup and keep the WSGI configuration and filesystem paths deployment-specific.
