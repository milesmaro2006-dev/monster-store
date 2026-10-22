# Validated delivery and payment preferences for customer checkout.
from flask import session
from flask_wtf import FlaskForm
from wtforms import (
    HiddenField,
    RadioField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.utils.validators import is_valid_egypt_phone


EGYPT_GOVERNORATES = [
    ("القاهرة", "Cairo"), ("الجيزة", "Giza"), ("الإسكندرية", "Alexandria"),
    ("الدقهلية", "Dakahlia"), ("الشرقية", "Sharqia"),
    ("القليوبية", "Qalyubia"), ("المنوفية", "Monufia"),
    ("الغربية", "Gharbia"), ("كفر الشيخ", "Kafr El Sheikh"),
    ("دمياط", "Damietta"), ("بورسعيد", "Port Said"),
    ("الإسماعيلية", "Ismailia"), ("السويس", "Suez"),
    ("شمال سيناء", "North Sinai"), ("جنوب سيناء", "South Sinai"),
    ("البحيرة", "Beheira"), ("الفيوم", "Faiyum"),
    ("بني سويف", "Beni Suef"), ("المنيا", "Minya"),
    ("أسيوط", "Assiut"), ("سوهاج", "Sohag"), ("قنا", "Qena"),
    ("الأقصر", "Luxor"), ("أسوان", "Aswan"),
    ("البحر الأحمر", "Red Sea"), ("الوادي الجديد", "New Valley"),
    ("مطروح", "Matrouh"),
]


def _phone_validator(form, field):
    if not is_valid_egypt_phone(field.data):
        message = (
            "Enter a valid Egyptian mobile number (for example 01012345678)."
            if session.get("lang") == "en"
            else "من فضلك أدخل رقم موبايل مصري صحيح (مثال: 01012345678)."
        )
        raise ValidationError(message)


class CheckoutForm(FlaskForm):
    customer_name = StringField(validators=[DataRequired(), Length(min=3, max=120)])
    phone = StringField(validators=[DataRequired(), _phone_validator, Length(max=20)])
    delivery_method = RadioField(
        choices=[("metro_pickup", "Metro pickup"), ("home_delivery", "Home delivery")],
        validators=[DataRequired()],
    )
    station_name = StringField(validators=[Optional(), Length(max=120)])
    governorate = SelectField(choices=[], validators=[Optional()])
    area = StringField(validators=[Optional(), Length(max=120)])
    street_address = StringField(validators=[Optional(), Length(max=250)])
    building = StringField(validators=[Optional(), Length(max=80)])
    apartment = StringField(validators=[Optional(), Length(max=40)])
    payment_method = RadioField(
        choices=[
            ("cod", "Cash on delivery"),
            ("instapay", "InstaPay / Smart Wallet"),
            ("visa_link", "Bank card · secure WhatsApp payment link"),
            ("vodafone_cash", "Legacy Vodafone Cash payment"),
        ],
        validators=[DataRequired()],
    )
    notes = TextAreaField(validators=[Optional(), Length(max=500)])
    checkout_token = HiddenField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        english = session.get("lang") == "en"
        self.governorate.choices = [
            (arabic, english_name if english else arabic)
            for arabic, english_name in EGYPT_GOVERNORATES
        ]
        if english:
            self.delivery_method.choices = [
                ("metro_pickup", "Metro station pickup"),
                ("home_delivery", "Home delivery"),
            ]
            self.payment_method.choices = [
                ("cod", "Cash on delivery (cash)"),
                ("instapay", "InstaPay / Smart Wallet"),
                ("visa_link", "Bank card (secure WhatsApp payment link)"),
                ("vodafone_cash", "Vodafone Cash"),
            ]
        else:
            self.delivery_method.choices = [
                ("metro_pickup", "استلام من محطة مترو"),
                ("home_delivery", "توصيل لباب المنزل"),
            ]
            self.payment_method.choices = [
                ("cod", "الدفع عند الاستلام (كاش)"),
                ("instapay", "تحويل إنستاباي / محفظة ذكية (InstaPay / Smart Wallet)"),
                ("visa_link", "بطاقة بنكية (رابط دفع سريع عبر واتساب)"),
                ("vodafone_cash", "فودافون كاش"),
            ]
        labels = {
            "customer_name": ("Full name", "الاسم بالكامل"),
            "phone": ("Phone / WhatsApp number", "رقم الهاتف / واتساب"),
            "delivery_method": ("Delivery method", "طريقة التوصيل"),
            "station_name": ("Preferred metro station", "اسم محطة المترو المفضلة"),
            "governorate": ("Governorate", "المحافظة"),
            "area": ("Area / district", "المنطقة / الحي"),
            "street_address": ("Detailed street address", "عنوان الشارع بالتفصيل"),
            "building": ("Building number / name", "رقم / اسم المبنى"),
            "apartment": ("Apartment number", "رقم الشقة"),
            "payment_method": ("Preferred payment method", "طريقة الدفع المفضلة"),
            "notes": ("Additional notes (optional)", "ملاحظات إضافية (اختياري)"),
        }
        for field_name, (en_label, ar_label) in labels.items():
            getattr(self, field_name).label.text = en_label if english else ar_label
        required_message = "This field is required." if english else "هذا الحقل مطلوب."
        for field in (
            self.customer_name,
            self.phone,
            self.delivery_method,
            self.payment_method,
        ):
            for validator in field.validators:
                if isinstance(validator, DataRequired):
                    validator.message = required_message

    def validate(self, extra_validators=None):
        valid = super().validate(extra_validators=extra_validators)
        english = session.get("lang") == "en"
        required = [
            (
                self.station_name,
                "Choose a metro station." if english else "اسم محطة المترو مطلوب.",
            ),
        ] if self.delivery_method.data == "metro_pickup" else [
            (self.governorate, "Choose a governorate." if english else "المحافظة مطلوبة."),
            (self.area, "Enter your area." if english else "المنطقة مطلوبة."),
            (
                self.street_address,
                "Enter your street address." if english else "عنوان الشارع مطلوب.",
            ),
            (self.building, "Enter your building details." if english else "بيانات المبنى مطلوبة."),
            (self.apartment, "Enter your apartment number." if english else "رقم الشقة مطلوب."),
        ]
        for field, error in required:
            if not (field.data or "").strip():
                field.errors.append(error)
                valid = False
        return valid
