from typing import Optional, Literal

from pydantic import BaseModel, EmailStr


class CustomerBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    city: Optional[str] = None
    company_name: Optional[str] = None
    website: Optional[str] = None
    action_type: Literal['cta', 'coop', 'first-time']


class CustomerCreate(CustomerBase):
    pass
