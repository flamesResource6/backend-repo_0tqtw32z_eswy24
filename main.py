import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order, Booking, FAQ, ContactMessage

app = FastAPI(title="Extensions Essence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class ObjectIdStr(str):
    pass

def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


def _doc_with_id(doc):
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/")
def read_root():
    return {"message": "Extensions Essence API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, "name", None) or "Unknown"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# Public schemas endpoint (useful for admin tooling)
@app.get("/schema")
def get_schema():
    return {
        "collections": [
            "product", "order", "booking", "faq", "contactmessage"
        ]
    }


# Products
@app.get("/products")
def list_products(category: Optional[str] = None, featured: Optional[bool] = None):
    q = {}
    if category:
        q["category"] = category
    if featured is not None:
        q["featured"] = featured
    items = get_documents("product", q)
    return [_doc_with_id(i) for i in items]


@app.get("/products/{product_id}")
def get_product(product_id: str):
    doc = db["product"].find_one({"_id": _oid(product_id)})
    if not doc:
        raise HTTPException(404, "Product not found")
    return _doc_with_id(doc)


@app.post("/products")
def create_product(product: Product):
    new_id = create_document("product", product)
    return {"id": new_id}


@app.put("/products/{product_id}")
def update_product(product_id: str, product: Product):
    data = product.model_dump()
    res = db["product"].update_one({"_id": _oid(product_id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(404, "Product not found")
    return {"id": product_id, "updated": True}


@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    res = db["product"].delete_one({"_id": _oid(product_id)})
    if res.deleted_count == 0:
        raise HTTPException(404, "Product not found")
    return {"deleted": True}


# Payments (Stripe / Paystack)
class CreateStripeIntent(BaseModel):
    amount: int
    currency: str = "NGN"


@app.post("/payments/stripe-intent")
def create_stripe_intent(payload: CreateStripeIntent):
    import math
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        # Mock response if key not set
        return {"clientSecret": "mock_client_secret", "mock": True}
    try:
        import stripe  # type: ignore
    except Exception:
        raise HTTPException(500, "Stripe package not installed on server")

    stripe.api_key = stripe_key
    # Convert amount in major to minor (e.g. 1000.50 -> 100050)
    amount_minor = int(math.floor(payload.amount)) * 100
    intent = stripe.PaymentIntent.create(
        amount=amount_minor,
        currency=payload.currency.lower(),
        automatic_payment_methods={"enabled": True},
    )
    return {"clientSecret": intent.client_secret}


class CreatePaystackInit(BaseModel):
    email: str
    amount: int
    currency: str = "NGN"


@app.post("/payments/paystack-init")
def create_paystack_transaction(payload: CreatePaystackInit):
    key = os.getenv("PAYSTACK_SECRET_KEY")
    if not key:
        # Mock response
        return {"authorization_url": "https://paystack.mock/checkout", "reference": "mock_ref", "mock": True}

    import requests
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {
        "email": payload.email,
        "amount": payload.amount * 100,  # kobo
        "currency": payload.currency,
    }
    r = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers, timeout=20)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    j = r.json()
    return {"authorization_url": j["data"]["authorization_url"], "reference": j["data"]["reference"]}


# Orders
@app.post("/orders")
def create_order(order: Order):
    new_id = create_document("order", order)
    return {"id": new_id}


@app.get("/orders")
def list_orders(limit: int = 50):
    docs = get_documents("order", {}, limit)
    return [_doc_with_id(d) for d in docs]


# Bookings
@app.post("/bookings")
def create_booking(booking: Booking):
    new_id = create_document("booking", booking)
    return {"id": new_id}


# FAQs
@app.get("/faqs")
def list_faqs():
    docs = get_documents("faq")
    return [_doc_with_id(d) for d in docs]


@app.post("/faqs")
def create_faq(faq: FAQ):
    new_id = create_document("faq", faq)
    return {"id": new_id}


# Contact messages
@app.post("/contact")
def contact(msg: ContactMessage):
    new_id = create_document("contactmessage", msg)
    return {"id": new_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
