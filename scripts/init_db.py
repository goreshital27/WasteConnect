import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import Base, get_engine  # noqa: E402
from app.modules.auth.models import User  # noqa: F401, E402
from app.modules.catalog.models import WasteCategory  # noqa: F401, E402
from app.modules.listings.models import Listing  # noqa: F401, E402
from app.modules.offers.models import Offer  # noqa: F401, E402
from app.modules.orders.models import Order, OrderStatusHistory, WeightRecord  # noqa: F401, E402


def init_db() -> None:
    print("Initializing database tables...")
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully!")


if __name__ == "__main__":
    init_db()
