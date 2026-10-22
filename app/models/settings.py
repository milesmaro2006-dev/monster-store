# StoreSettings + DeliveryArea models
from datetime import datetime
from app.extensions import db


class StoreSettings(db.Model):
    __tablename__ = "store_settings"

    id = db.Column(db.Integer, primary_key=True)
    default_delivery_fee = db.Column(db.Numeric(10, 2), nullable=False, default=30)
    metro_pickup_fee = db.Column(
        db.Numeric(10, 2), nullable=False, default=60, server_default="60.00"
    )
    home_delivery_fee = db.Column(
        db.Numeric(10, 2), nullable=False, default=95, server_default="95.00"
    )
    free_delivery_threshold = db.Column(db.Numeric(10, 2), nullable=True)
    store_phone = db.Column(db.String(20), nullable=True)
    store_whatsapp = db.Column(db.String(20), nullable=True)
    store_email = db.Column(db.String(120), nullable=True)
    store_address = db.Column(db.String(255), nullable=True)
    # Current storefront settings. Legacy store_* fields remain for compatibility.
    contact_phone = db.Column(db.String(20), nullable=True)
    contact_whatsapp = db.Column(db.String(20), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    facebook_url = db.Column(db.String(500), nullable=True)
    instagram_url = db.Column(db.String(500), nullable=True)
    tiktok_url = db.Column(db.String(500), nullable=True)
    instapay_address = db.Column(db.String(120), nullable=True)
    instapay_name = db.Column(db.String(120), nullable=True)
    payment_instructions = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls) -> "StoreSettings":
        obj = db.session.get(cls, 1)
        if not obj:
            obj = cls(id=1)
            db.session.add(obj)
            db.session.commit()
        return obj


class DeliveryArea(db.Model):
    __tablename__ = "delivery_areas"

    id = db.Column(db.Integer, primary_key=True)
    governorate = db.Column(db.String(60), nullable=False, index=True)
    area = db.Column(db.String(120), nullable=False)
    fee = db.Column(db.Numeric(10, 2), nullable=False, default=30)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<DeliveryArea {self.governorate}/{self.area} {self.fee}>"
