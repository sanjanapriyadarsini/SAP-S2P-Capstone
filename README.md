# SAP S2P Process Management System
### Capstone Project | SAP Source-to-Pay Course | 2026

---

## 👤 Student Details
| Field | Value |
|---|---|
| **Name** | Sanjana Priyadarsini |
| **Roll Number** | 23052184 |
| **Institute** | KIIT UNIVERSITY |
| **Batch/Program** | SAP S2P |
| **Date** | April 2026 |

---

## 📌 What is S2P?
**Source-to-Pay (S2P)** is a complete procurement process used in SAP that covers every step from identifying a need to paying the vendor:
Vendor Registration → Purchase Requisition → Purchase Order → Goods Receipt → Invoice Processing → 3-Way Matching → Payment

---

## 🚀 Features
| Module | Description |
|---|---|
| **Vendor Management** | Register and manage suppliers with GST details |
| **Purchase Requisition** | Submit internal requests with Approve/Reject workflow |
| **Purchase Order** | Convert approved PRs into official POs with auto total calculation |
| **Goods Receipt** | Record delivery with quantity and condition check |
| **Invoice Processing** | Log vendor invoices linked to POs |
| **3-Way Matching** | Auto-verify PO ↔ GR ↔ Invoice (core SAP concept) |
| **Payment Release** | Release payment only after 3-way match passes |
| **Dashboard** | Real-time KPI overview of entire pipeline |

---

## 🛠️ Tech Stack
| Layer | Technology |
|---|---|
| Backend | Python 3, Flask 3.0 |
| Database | SQLite |
| Frontend | HTML5, CSS3, Jinja2 |
| Version Control | Git, GitHub |
| IDE | VS Code |

---

## ⚙️ How to Run

### 1. Clone the repo
```bash
git clone https://github.com/sanjanapriyadarsini/SAP-S2P-Capstone.git
cd SAP-S2P-Capstone
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open browser
http://127.0.0.1:5000

Database is auto-created on first run. No extra setup needed.

---

## 📁 Project Structure
S2P_Project/
├── app.py                  ← All Flask routes + SQLite logic
├── requirements.txt        ← Dependencies
├── README.md               ← This file
├── templates/              ← HTML pages
│   ├── base.html           ← Sidebar layout
│   ├── dashboard.html      ← KPI dashboard
│   ├── vendors.html
│   ├── vendor_form.html
│   ├── requisitions.html
│   ├── requisition_form.html
│   ├── purchase_orders.html
│   ├── po_form.html
│   ├── goods_receipt.html
│   ├── gr_form.html
│   ├── invoices.html
│   ├── invoice_form.html
│   ├── payments.html
│   └── payment_form.html
└── static/
├── css/style.css       ← Stylesheet
└── js/main.js          ← Flash message script

---

## 🔑 Key Concept: 3-Way Matching
The most critical SAP S2P feature. Before payment is released, the system checks:

| Check | What it verifies |
|---|---|
| ✅ PO Amount | What was agreed to pay |
| ✅ GR Quantity | What was actually received |
| ✅ Invoice Amount | What vendor is charging (must be within 5% of PO) |

If all three match → Invoice approved → Payment released.
If any mismatch → Invoice marked **Disputed** → Payment **blocked**.