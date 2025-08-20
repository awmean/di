from app.database import SessionLocal
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository

# Method 1: Manual session management
db = SessionLocal()
#
# ProductCRUD.create(
#     db=db,
#     name='Диванчег',
#     slug='divancheg',
#     category_id=2,
#     price=10000,
# )
Q
categories = CategoryRepository.get_all(db)
for cat in categories:
    print(cat.id)

products = ProductRepository.get_all(db)
for product in products:
    print(product.name)
