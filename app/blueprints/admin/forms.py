# Admin forms
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, TextAreaField, SelectField,
    DecimalField, IntegerField, BooleanField,
)
from wtforms.validators import (
    DataRequired, InputRequired, Length, Optional, NumberRange, Email, URL, Regexp,
)


class LoginForm(FlaskForm):
    username = StringField("اسم المستخدم", validators=[DataRequired(), Length(max=60)])
    password = PasswordField("كلمة المرور", validators=[DataRequired(), Length(min=1)])


class ProductForm(FlaskForm):
    name = StringField("الاسم (عربي)", validators=[DataRequired(), Length(max=150)])
    name_en = StringField("الاسم (إنجليزي)", validators=[Optional(), Length(max=150)])
    brand = StringField("العلامة التجارية", validators=[Optional(), Length(max=100)])
    flavor = StringField("النكهة (عربي)", validators=[Optional(), Length(max=80)])
    flavor_en = StringField("النكهة (إنجليزي)", validators=[Optional(), Length(max=80)])
    volume = StringField("الحجم / الوزن", validators=[Optional(), Length(max=50)])
    origin_country = StringField("بلد المنشأ", validators=[Optional(), Length(max=100)])
    calories = StringField("السعرات الحرارية", validators=[Optional(), Length(max=50)])
    serving_advice = StringField(
        "طريقة التقديم", validators=[Optional(), Length(max=100)],
        default="يُقدّم مثلجاً",
    )
    description = TextAreaField("الوصف (عربي)", validators=[Optional(), Length(max=2000)])
    description_en = TextAreaField("الوصف (إنجليزي)", validators=[Optional(), Length(max=2000)])
    price = DecimalField("السعر (EGP)", validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField("المخزون", validators=[DataRequired(), NumberRange(min=0)])
    low_stock_threshold = IntegerField(
        "حد المخزون المنخفض", validators=[Optional(), NumberRange(min=0)]
    )
    category_id = SelectField("الفئة", coerce=int, validators=[Optional()])
    is_active = BooleanField("مُفعّل", default=True)
    is_featured = BooleanField("مميز", default=False)
    is_zero_sugar = BooleanField("خالي من السكر (Zero Sugar)", default=False)


class ProductQuickUpdateForm(FlaskForm):
    price = DecimalField(
        "السعر (EGP)", validators=[InputRequired(), NumberRange(min=0)]
    )
    stock = IntegerField(
        "المخزون", validators=[InputRequired(), NumberRange(min=0)]
    )


class CategoryForm(FlaskForm):
    name = StringField("الاسم (عربي)", validators=[DataRequired(), Length(max=80)])
    name_en = StringField("الاسم (إنجليزي)", validators=[Optional(), Length(max=80)])
    is_active = BooleanField("مُفعّل", default=True)


class SettingsForm(FlaskForm):
    metro_pickup_fee = DecimalField(
        "رسوم استلام المترو (EGP)", validators=[DataRequired(), NumberRange(min=0)]
    )
    home_delivery_fee = DecimalField(
        "رسوم التوصيل للمنزل (EGP)", validators=[DataRequired(), NumberRange(min=0)]
    )
    default_delivery_fee = DecimalField(
        "رسوم التوصيل الافتراضية", validators=[DataRequired(), NumberRange(min=0)]
    )
    free_delivery_threshold = DecimalField(
        "توصيل مجاني بعد (اختياري)", validators=[Optional(), NumberRange(min=0)]
    )
    contact_phone = StringField("هاتف المتجر", validators=[Optional(), Length(max=20), Regexp(r"^[0-9+()\s.-]{6,20}$", message="أدخل رقم هاتف صحيحاً.")])
    contact_whatsapp = StringField("رقم واتساب بصيغة دولية", validators=[Optional(), Length(max=20), Regexp(r"^[0-9+()\s.-]{6,20}$", message="أدخل رقم واتساب صحيحاً.")])
    contact_email = StringField("البريد الإلكتروني", validators=[Optional(), Email(), Length(max=120)])
    store_address = StringField("العنوان", validators=[Optional(), Length(max=255)])
    facebook_url = StringField("رابط فيسبوك", validators=[Optional(), URL(), Length(max=500)])
    instagram_url = StringField("رابط إنستجرام", validators=[Optional(), URL(), Length(max=500)])
    tiktok_url = StringField("رابط تيك توك", validators=[Optional(), URL(), Length(max=500)])
    instapay_address = StringField("عنوان إنستاباي / IPA", validators=[Optional(), Length(max=120)])
    instapay_name = StringField("اسم صاحب الحساب", validators=[Optional(), Length(max=120)])
    payment_instructions = TextAreaField("تعليمات الدفع للعميل", validators=[Optional(), Length(max=2000)])


class DeliveryAreaForm(FlaskForm):
    governorate = StringField("المحافظة", validators=[DataRequired(), Length(max=60)])
    area = StringField("المنطقة", validators=[DataRequired(), Length(max=120)])
    fee = DecimalField("الرسوم", validators=[DataRequired(), NumberRange(min=0)])
    is_active = BooleanField("مُفعّل", default=True)


class OrderStatusForm(FlaskForm):
    status = SelectField(
        "الحالة",
        choices=[
            ("pending", "قيد الانتظار"),
            ("confirmed", "تم التأكيد"),
            ("shipped", "تم الشحن"),
            ("delivered", "تم التوصيل"),
            ("cancelled", "ملغي"),
        ],
        validators=[DataRequired()],
    )
    note = StringField("ملاحظة", validators=[Optional(), Length(max=255)])


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "كلمة المرور الحالية", validators=[DataRequired(), Length(max=128)]
    )
    new_password = PasswordField(
        "كلمة المرور الجديدة", validators=[DataRequired(), Length(min=12, max=128)]
    )
    confirm_password = PasswordField(
        "تأكيد كلمة المرور", validators=[DataRequired(), Length(max=128)]
    )


class AdminAccountForm(FlaskForm):
    username = StringField(
        "اسم المستخدم", validators=[DataRequired(), Length(min=3, max=60)]
    )
    current_password = PasswordField(
        "كلمة المرور الحالية", validators=[DataRequired(), Length(max=128)]
    )
    new_password = PasswordField(
        "كلمة المرور الجديدة (اختياري لتغييرها)",
        validators=[Optional(), Length(min=12, max=128)],
    )
    confirm_password = PasswordField(
        "تأكيد كلمة المرور الجديدة", validators=[Optional(), Length(max=128)]
    )
