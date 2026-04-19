from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "s2p_secret_2026"  # needed for flash messages (alerts)

# Database will be created in the same folder as app.py
DB_PATH = os.path.join(os.path.dirname(__file__), "s2p.db")

def get_db():
    # Opens a connection to the SQLite database
    # row_factory lets us access columns by name like row['vendor_name']
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # This function creates all our tables when the app starts
    # IF NOT EXISTS means it won't break if tables already exist
    conn = get_db()
    c = conn.cursor()

    # TABLE 1: Vendors (our suppliers)
    c.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT NOT NULL,
            phone       TEXT,
            address     TEXT,
            gst_number  TEXT,
            category    TEXT,
            status      TEXT DEFAULT 'Active',
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # TABLE 2: Purchase Requisitions (internal requests to buy something)
    c.execute("""
        CREATE TABLE IF NOT EXISTS requisitions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name       TEXT NOT NULL,
            quantity        INTEGER NOT NULL,
            estimated_cost  REAL NOT NULL,
            department      TEXT NOT NULL,
            requested_by    TEXT NOT NULL,
            reason          TEXT,
            status          TEXT DEFAULT 'Pending',
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    # TABLE 3: Purchase Orders (official order sent to vendor)
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            requisition_id  INTEGER,
            vendor_id       INTEGER NOT NULL,
            item_name       TEXT NOT NULL,
            quantity        INTEGER NOT NULL,
            unit_price      REAL NOT NULL,
            total_amount    REAL NOT NULL,
            delivery_date   TEXT,
            status          TEXT DEFAULT 'Sent',
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    # TABLE 4: Goods Receipts (confirmation that goods arrived)
    c.execute("""
        CREATE TABLE IF NOT EXISTS goods_receipts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id           INTEGER NOT NULL,
            received_qty    INTEGER NOT NULL,
            received_by     TEXT NOT NULL,
            condition_ok    INTEGER DEFAULT 1,
            remarks         TEXT,
            received_at     TEXT DEFAULT (datetime('now'))
        )
    """)

    # TABLE 5: Invoices (bill sent by vendor after delivery)
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id           INTEGER NOT NULL,
            vendor_id       INTEGER NOT NULL,
            invoice_number  TEXT NOT NULL,
            invoice_amount  REAL NOT NULL,
            invoice_date    TEXT NOT NULL,
            due_date        TEXT,
            status          TEXT DEFAULT 'Pending',
            match_status    TEXT DEFAULT 'Unverified',
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    # TABLE 6: Payments (final payment released to vendor)
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id      INTEGER NOT NULL,
            amount_paid     REAL NOT NULL,
            payment_mode    TEXT,
            payment_date    TEXT DEFAULT (datetime('now')),
            reference_no    TEXT
        )
    """)

    conn.commit()   # save all changes to the database file
    conn.close()    # close the connection
    print("Database ready!")


@app.route("/")
def dashboard():
    # Query the DB for counts to show on the dashboard
    conn = get_db()
    stats = {
        "vendors":      conn.execute("SELECT COUNT(*) FROM vendors WHERE status='Active'").fetchone()[0],
        "requisitions": conn.execute("SELECT COUNT(*) FROM requisitions WHERE status='Pending'").fetchone()[0],
        "open_pos":     conn.execute("SELECT COUNT(*) FROM purchase_orders WHERE status='Sent'").fetchone()[0],
        "pending_inv":  conn.execute("SELECT COUNT(*) FROM invoices WHERE status='Pending'").fetchone()[0],
        "total_spend":  conn.execute("SELECT COALESCE(SUM(amount_paid),0) FROM payments").fetchone()[0],
        "matched":      conn.execute("SELECT COUNT(*) FROM invoices WHERE match_status='3-Way Matched'").fetchone()[0],
    }
    conn.close()
    # render_template looks inside the /templates folder for dashboard.html
    return render_template("dashboard.html", stats=stats)
    
@app.route("/vendors")    
def vendors():
    conn = get_db()
    vendors_list = conn.execute("SELECT * FROM vendors ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("vendors.html", vendors=vendors_list)


@app.route("/vendors/add", methods=["GET", "POST"])
def add_vendor():
    # GET = show the form, POST = save the form data
    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO vendors (name, email, phone, address, gst_number, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.form["name"],
            request.form["email"],
            request.form.get("phone", ""),
            request.form.get("address", ""),
            request.form.get("gst_number", ""),
            request.form.get("category", "General"),
        ))
        conn.commit()
        conn.close()
        flash("Vendor registered successfully!", "success")
        return redirect(url_for("vendors"))
    return render_template("vendor_form.html")


@app.route("/vendors/delete/<int:vid>")
def delete_vendor(vid):
    conn = get_db()
    conn.execute("UPDATE vendors SET status='Inactive' WHERE id=?", (vid,))
    conn.commit()
    conn.close()
    flash("Vendor marked as Inactive.", "info")
    return redirect(url_for("vendors"))

@app.route("/requisitions")
def requisitions():
    conn = get_db()
    reqs = conn.execute("SELECT * FROM requisitions ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("requisitions.html", requisitions=reqs)


@app.route("/requisitions/add", methods=["GET", "POST"])
def add_requisition():
    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO requisitions (item_name, quantity, estimated_cost, department, requested_by, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.form["item_name"],
            int(request.form["quantity"]),
            float(request.form["estimated_cost"]),
            request.form["department"],
            request.form["requested_by"],
            request.form.get("reason", ""),
        ))
        conn.commit()
        conn.close()
        flash("Purchase Requisition submitted!", "success")
        return redirect(url_for("requisitions"))
    return render_template("requisition_form.html")


@app.route("/requisitions/approve/<int:rid>")
def approve_requisition(rid):
    conn = get_db()
    conn.execute("UPDATE requisitions SET status='Approved' WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    flash("Requisition Approved!", "success")
    return redirect(url_for("requisitions"))


@app.route("/requisitions/reject/<int:rid>")
def reject_requisition(rid):
    conn = get_db()
    conn.execute("UPDATE requisitions SET status='Rejected' WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    flash("Requisition Rejected.", "warning")
    return redirect(url_for("requisitions"))

@app.route("/purchase-orders")
def purchase_orders():
    conn = get_db()
    pos = conn.execute("""
        SELECT po.*, v.name as vendor_name 
        FROM purchase_orders po
        JOIN vendors v ON po.vendor_id = v.id
        ORDER BY po.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("purchase_orders.html", purchase_orders=pos)


@app.route("/purchase-orders/add", methods=["GET", "POST"])
def add_purchase_order():
    conn = get_db()
    if request.method == "POST":
        qty        = int(request.form["quantity"])
        unit_price = float(request.form["unit_price"])
        total      = qty * unit_price        # auto-calculate total
        conn.execute("""
            INSERT INTO purchase_orders
              (requisition_id, vendor_id, item_name, quantity, unit_price, total_amount, delivery_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("requisition_id") or None,
            int(request.form["vendor_id"]),
            request.form["item_name"],
            qty,
            unit_price,
            total,
            request.form.get("delivery_date", ""),
        ))
        conn.commit()
        conn.close()
        flash("Purchase Order created and sent to vendor!", "success")
        return redirect(url_for("purchase_orders"))

    # Load dropdowns for the form
    vendors_list  = conn.execute("SELECT * FROM vendors WHERE status='Active'").fetchall()
    approved_reqs = conn.execute("SELECT * FROM requisitions WHERE status='Approved'").fetchall()
    conn.close()
    return render_template("po_form.html", vendors=vendors_list, requisitions=approved_reqs)


@app.route("/goods-receipt")
def goods_receipt():
    conn = get_db()
    grs = conn.execute("""
        SELECT gr.*, po.item_name, po.quantity as ordered_qty, v.name as vendor_name
        FROM goods_receipts gr
        JOIN purchase_orders po ON gr.po_id = po.id
        JOIN vendors v ON po.vendor_id = v.id
        ORDER BY gr.received_at DESC
    """).fetchall()
    conn.close()
    return render_template("goods_receipt.html", receipts=grs)


@app.route("/goods-receipt/add", methods=["GET", "POST"])
def add_goods_receipt():
    conn = get_db()
    if request.method == "POST":
        po_id = int(request.form["po_id"])
        conn.execute("""
            INSERT INTO goods_receipts (po_id, received_qty, received_by, condition_ok, remarks)
            VALUES (?, ?, ?, ?, ?)
        """, (
            po_id,
            int(request.form["received_qty"]),
            request.form["received_by"],
            1 if request.form.get("condition_ok") == "on" else 0,
            request.form.get("remarks", ""),
        ))
        # Mark the PO as Delivered
        conn.execute("UPDATE purchase_orders SET status='Delivered' WHERE id=?", (po_id,))
        conn.commit()
        conn.close()
        flash("Goods Receipt recorded!", "success")
        return redirect(url_for("goods_receipt"))

    open_pos = conn.execute("""
        SELECT po.*, v.name as vendor_name FROM purchase_orders po
        JOIN vendors v ON po.vendor_id = v.id
        WHERE po.status IN ('Sent', 'Delivered')
    """).fetchall()
    conn.close()
    return render_template("gr_form.html", purchase_orders=open_pos)


@app.route("/invoices")
def invoices():
    conn = get_db()
    inv_list = conn.execute("""
        SELECT inv.*, v.name as vendor_name, po.item_name, po.total_amount as po_amount
        FROM invoices inv
        JOIN vendors v ON inv.vendor_id = v.id
        JOIN purchase_orders po ON inv.po_id = po.id
        ORDER BY inv.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("invoices.html", invoices=inv_list)


@app.route("/invoices/add", methods=["GET", "POST"])
def add_invoice():
    conn = get_db()
    if request.method == "POST":
        conn.execute("""
            INSERT INTO invoices (po_id, vendor_id, invoice_number, invoice_amount, invoice_date, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            int(request.form["po_id"]),
            int(request.form["vendor_id"]),
            request.form["invoice_number"],
            float(request.form["invoice_amount"]),
            request.form["invoice_date"],
            request.form.get("due_date", ""),
        ))
        conn.commit()
        conn.close()
        flash("Invoice recorded!", "success")
        return redirect(url_for("invoices"))

    delivered_pos = conn.execute("""
        SELECT po.*, v.name as vendor_name FROM purchase_orders po
        JOIN vendors v ON po.vendor_id = v.id
        WHERE po.status = 'Delivered'
    """).fetchall()
    vendors_list = conn.execute("SELECT * FROM vendors WHERE status='Active'").fetchall()
    conn.close()
    return render_template("invoice_form.html", purchase_orders=delivered_pos, vendors=vendors_list)


@app.route("/invoices/match/<int:inv_id>")
def three_way_match(inv_id):
    """
    3-Way Match: Compare PO amount vs GR quantity vs Invoice amount.
    All 3 must align (within 5% tolerance) to approve payment.
    This is the most important SAP S2P concept.
    """
    conn = get_db()
    inv = conn.execute("SELECT * FROM invoices WHERE id=?", (inv_id,)).fetchone()
    po  = conn.execute("SELECT * FROM purchase_orders WHERE id=?", (inv["po_id"],)).fetchone()
    gr  = conn.execute(
        "SELECT * FROM goods_receipts WHERE po_id=? ORDER BY received_at DESC LIMIT 1",
        (inv["po_id"],)
    ).fetchone()

    if not gr:
        flash("No Goods Receipt found for this PO. Cannot match.", "warning")
        conn.close()
        return redirect(url_for("invoices"))

    po_amount  = po["total_amount"]
    inv_amount = inv["invoice_amount"]
    tolerance  = 0.05   # 5% allowed difference

    amount_ok = abs(inv_amount - po_amount) / po_amount <= tolerance
    qty_ok    = gr["received_qty"] >= po["quantity"]
    cond_ok   = bool(gr["condition_ok"])

    if amount_ok and qty_ok and cond_ok:
        match_result = "3-Way Matched"
        inv_status   = "Matched"
        flash("3-Way Match PASSED! Invoice approved for payment.", "success")
    else:
        match_result = "Mismatch"
        inv_status   = "Disputed"
        reasons = []
        if not amount_ok: reasons.append(f"Amount mismatch (PO: ₹{po_amount}, Invoice: ₹{inv_amount})")
        if not qty_ok:    reasons.append(f"Qty short (Ordered: {po['quantity']}, Received: {gr['received_qty']})")
        if not cond_ok:   reasons.append("Goods damaged")
        flash("3-Way Match FAILED: " + " | ".join(reasons), "danger")

    conn.execute(
        "UPDATE invoices SET match_status=?, status=? WHERE id=?",
        (match_result, inv_status, inv_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("invoices"))


@app.route("/payments")
def payments():
    conn = get_db()
    pay_list = conn.execute("""
        SELECT p.*, inv.invoice_number, v.name as vendor_name
        FROM payments p
        JOIN invoices inv ON p.invoice_id = inv.id
        JOIN vendors v ON inv.vendor_id = v.id
        ORDER BY p.payment_date DESC
    """).fetchall()
    conn.close()
    return render_template("payments.html", payments=pay_list)


@app.route("/payments/add/<int:inv_id>", methods=["GET", "POST"])
def add_payment(inv_id):
    conn = get_db()
    inv = conn.execute("""
        SELECT inv.*, v.name as vendor_name FROM invoices inv
        JOIN vendors v ON inv.vendor_id = v.id
        WHERE inv.id=?
    """, (inv_id,)).fetchone()

    if inv["match_status"] != "3-Way Matched":
        flash("Payment blocked: Invoice has not passed 3-Way Matching.", "danger")
        conn.close()
        return redirect(url_for("invoices"))

    if request.method == "POST":
        conn.execute("""
            INSERT INTO payments (invoice_id, amount_paid, payment_mode, reference_no)
            VALUES (?, ?, ?, ?)
        """, (
            inv_id,
            float(request.form["amount_paid"]),
            request.form.get("payment_mode", "Bank Transfer"),
            request.form.get("reference_no", ""),
        ))
        conn.execute("UPDATE invoices SET status='Paid' WHERE id=?", (inv_id,))
        conn.commit()
        conn.close()
        flash("Payment released successfully!", "success")
        return redirect(url_for("payments"))

    conn.close()
    return render_template("payment_form.html", invoice=inv)




    # This runs ONLY when you do: python app.py
    # It creates the DB tables, then starts the web server
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)