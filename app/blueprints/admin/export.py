# CSV export
import csv
import io
from flask import Response, request
from app.blueprints.admin import admin_bp
from app.blueprints.admin.decorators import admin_required
from app.models.order import Order
from app.models.order import ORDER_STATUS_LABELS_AR


@admin_bp.route("/export/orders.csv")
@admin_required
def export_orders_csv():
    status = request.args.get("status") or ""
    query = Order.query
    if status:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Reference", "Date", "Customer", "Phone", "Governorate",
        "Area", "Address", "Status", "Subtotal", "Delivery", "Total",
    ])
    for o in orders:
        writer.writerow([
            o.reference,
            o.created_at.strftime("%Y-%m-%d %H:%M"),
            o.customer_name,
            o.phone,
            o.governorate,
            o.area,
            o.address.replace("\n", " "),
            ORDER_STATUS_LABELS_AR.get(o.status, o.status),
            o.subtotal,
            o.delivery_fee,
            o.total,
        ])

    output.seek(0)
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=orders.csv"},
    )
