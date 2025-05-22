"""
Tests for database models in the SmartNinja application.
Simplified tests focusing on model functionality.
"""
import os
import sys
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# pylint: disable=wrong-import-position,invalid-name,redefined-outer-name,attribute-defined-outside-init
from app.core.models import Alert, Analysis, Base, Phone, Price


@pytest.fixture
def db_session():
    """Create a test database session"""
    # Create a temporary database
    temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    temp_db_uri = f"sqlite:///{temp_db_path}"
    # Create test engine
    engine = create_engine(
        temp_db_uri, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        os.close(temp_db_fd)
        os.unlink(temp_db_path)


def test_phone_model(db_session):
    """Test Phone model creation and retrieval"""
    # Create a test phone
    phone = Phone(model="iPhone 15 Pro", brand="Apple", storage="128GB")
    # Add to database
    db_session.add(phone)
    db_session.commit()
    # Query back
    stored_phone = db_session.query(Phone).filter_by(model="iPhone 15 Pro").first()
    # Verify fields
    assert stored_phone is not None
    assert stored_phone.model == "iPhone 15 Pro"
    assert stored_phone.brand == "Apple"
    assert stored_phone.storage == "128GB"
    assert stored_phone.id is not None


def test_price_model(db_session):
    """Test Price model creation and retrieval"""
    # Create a test phone
    phone = Phone(model="iPhone 15 Pro", brand="Apple", storage="128GB")
    # Add to database
    db_session.add(phone)
    db_session.commit()
    # Create a price for the phone
    price = Price(
        phone_id=phone.id, price=999.99, currency="USD", region="US", source="Amazon"
    )
    # Add to database
    db_session.add(price)
    db_session.commit()
    # Query back
    stored_price = db_session.query(Price).filter_by(phone_id=phone.id).first()
    # Verify fields
    assert stored_price is not None
    assert stored_price.price == 999.99
    assert stored_price.currency == "USD"
    assert stored_price.region == "US"
    assert stored_price.source == "Amazon"
    assert stored_price.id is not None


def test_phone_price_relationship(db_session):
    """Test relationship between Phone and Price models"""
    # Create a test phone
    phone = Phone(model="Samsung Galaxy S24 Ultra", brand="Samsung", storage="256GB")
    # Add to database
    db_session.add(phone)
    db_session.commit()
    # Create multiple prices for the phone
    prices = [
        Price(
            phone_id=phone.id,
            price=1199.99,
            currency="USD",
            region="US",
            source="Samsung Store",
        )
        for i in range(3)
    ]
    # Add to database
    db_session.add_all(prices)
    db_session.commit()
    # Query back the phone with its prices
    stored_phone = db_session.query(Phone).filter_by(id=phone.id).first()
    # Verify relationship
    assert stored_phone is not None
    assert len(stored_phone.prices) == 3
    assert all(isinstance(price, Price) for price in stored_phone.prices)
    assert all(price.phone_id == phone.id for price in stored_phone.prices)


def test_alert_model(db_session):
    """Test Alert model creation and retrieval"""
    # Create a test phone first
    phone = Phone(model="Google Pixel 8 Pro", brand="Google", storage="128GB")
    # Add to database
    db_session.add(phone)
    db_session.commit()
    # Create a test alert
    alert = Alert(phone_id=phone.id, threshold=899.99, active=True)
    # Add to database
    db_session.add(alert)
    db_session.commit()
    # Query back
    stored_alert = db_session.query(Alert).filter_by(phone_id=phone.id).first()
    # Verify fields
    assert stored_alert is not None
    assert stored_alert.phone_id == phone.id
    assert stored_alert.threshold == 899.99
    assert stored_alert.active is True
    assert stored_alert.id is not None


def test_analysis_model(db_session):
    """Test Analysis model creation and retrieval"""
    # Create a test phone first
    phone = Phone(model="iPhone 15 Pro", brand="Apple", storage="128GB")
    # Add to database
    db_session.add(phone)
    db_session.commit()
    # Create a test analysis
    analysis = Analysis(
        phone_id=phone.id,
        region="Global",
        insights="Price trending downward globally due to new model announcement.",
    )
    # Add to database
    db_session.add(analysis)
    db_session.commit()
    # Query back
    stored_analysis = db_session.query(Analysis).filter_by(phone_id=phone.id).first()
    # Verify fields
    assert stored_analysis is not None
    assert stored_analysis.phone_id == phone.id
    assert stored_analysis.region == "Global"
    assert "Price trending downward" in stored_analysis.insights
    assert stored_analysis.id is not None


def test_cascade_delete(db_session):
    """Test cascade delete from Phone to Price"""
    # Create a test phone
    phone = Phone(model="iPhone 14", brand="Apple", storage="128GB")
    # Add to database
    db_session.add(phone)
    db_session.commit()
    # Create prices for the phone
    prices = [
        Price(
            phone_id=phone.id,
            price=799.99,
            currency="USD",
            region="US",
            source="Apple Store",
        ),
        Price(
            phone_id=phone.id,
            price=849.99,
            currency="EUR",
            region="EU",
            source="Amazon EU",
        ),
    ]
    # Add to database
    db_session.add_all(prices)
    db_session.commit()
    # Verify prices exist
    price_count = db_session.query(Price).filter_by(phone_id=phone.id).count()
    assert price_count == 2
    # Delete the phone
    db_session.delete(phone)
    db_session.commit()
    # Verify prices were deleted
    price_count = db_session.query(Price).filter_by(phone_id=phone.id).count()
    assert price_count == 0
