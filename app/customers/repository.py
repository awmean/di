from typing import Optional, Literal

from sqlalchemy.orm import Session

from app.customers.models import Customer


class CustomersRepository:
    @staticmethod
    def create(
            db: Session,
            name: str,
            action_type: Literal['cta', 'coop', 'first-time'],
            phone: Optional[str] = None,
            email: Optional[str] = None,
            city: Optional[str] = None,
            company_name: Optional[str] = None,
            website: Optional[str] = None
    ) -> Customer:
        customer = Customer(
            name=name,
            phone=phone,
            email=email,
            city=city,
            company_name=company_name,
            website=website,
            action_type=action_type
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        return customer
