"""
Database Schemas for Extensions Essence by Abisola

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name (e.g., Product -> "product").
"""
from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import List, Optional
from datetime import datetime

# Core domain models
class ProductImage(BaseModel):
    url: HttpUrl
    alt: Optional[str] = None

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in selected currency")
    category: str = Field(..., description="Category: crochet, extensions, accessories, hair-care, installation")
    subcategory: Optional[str] = Field(None, description="Optional subcategory/texture/length")
    images: List[ProductImage] = Field(default_factory=list, description="Product image gallery")
    in_stock: bool = Field(True, description="Stock availability")
    featured: bool = Field(False, description="Whether to show on homepage slider")
    tags: List[str] = Field(default_factory=list)

class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(1, ge=1)

class OrderCustomer(BaseModel):
    name: str
    email: EmailStr
    phone: str

class OrderAddress(BaseModel):
    line1: str
    line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "NG"

class Order(BaseModel):
    items: List[CartItem]
    amount: float = Field(..., ge=0)
    currency: str = Field("NGN", description="Order currency")
    payment_provider: str = Field(..., description="stripe | paystack")
    payment_id: Optional[str] = None
    status: str = Field("pending", description="pending | paid | failed | fulfilled")
    customer: OrderCustomer
    address: OrderAddress
    delivery_option: str = Field("standard")
    created_at: Optional[datetime] = None

class Booking(BaseModel):
    name: str
    phone: str
    service: str = Field(..., description="crochet | braids | wig-install | other")
    preferred_date: Optional[str] = None
    notes: Optional[str] = None

class FAQ(BaseModel):
    question: str
    answer: str

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    message: str
