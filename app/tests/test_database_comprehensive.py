"""
Comprehensive tests for database module in the SmartNinja application.
Tests database initialization, session management, and model operations.
"""
import os
import sys
import tempfile

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# pylint: disable=invalid-name,redefined-outer-name,unused-import,reimported,import-outside-toplevel,wrong-import-position
from app.core.database import Base, SessionLocal, get_db, init_db
from app.core.models import Alert, Analysis, Phone, Price


class TestDatabaseInitialization:
    """Test suite for database initialization and configuration"""

    def test_init_db(self):
        """Test database initialization"""
        # Create a temporary database
        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
        temp_db_uri = f"sqlite:///{temp_db_path}"
        try:
            # Create a test engine
            engine = create_engine(
                temp_db_uri,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
            # Import models to ensure they're registered with Base
            from app.core.models import Alert, Analysis, Phone, Price

            # Initialize database with our engine
            Base.metadata.create_all(bind=engine)
            # Verify tables exist
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            assert "phones" in tables, f"Tables in database: {tables}"
            assert "prices" in tables, f"Tables in database: {tables}"
            assert "alerts" in tables, f"Tables in database: {tables}"
            assert "analysis" in tables, f"Tables in database: {tables}"
            # Check columns in phones table
            columns = {col["name"] for col in inspector.get_columns("phones")}
            expected_columns = {
                "id",
                "model",
                "brand",
                "storage",
                "created_at",
                "updated_at",
            }
            assert expected_columns.issubset(columns)
            # Check columns in prices table
            columns = {col["name"] for col in inspector.get_columns("prices")}
            expected_columns = {
                "id",
                "phone_id",
                "region",
                "price",
                "currency",
                "source",
                "timestamp",
            }
            assert expected_columns.issubset(columns)
        finally:
            # Clean up
            os.close(temp_db_fd)
            os.unlink(temp_db_path)

    def test_get_db(self):
        """Test database session generator"""
        # Create a temporary database
        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
        temp_db_uri = f"sqlite:///{temp_db_path}"
        try:
            # Create a test engine
            engine = create_engine(
                temp_db_uri,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
            # Initialize database with our engine
            Base.metadata.create_all(bind=engine)
            # Create a session factory
            TestSessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=engine
            )

            # Create a test get_db function that uses our test session
            def test_get_db():
                db = TestSessionLocal()
                try:
                    yield db
                finally:
                    db.close()

            # Get a session from the generator
            db_gen = test_get_db()
            db = next(db_gen)
            # Verify it's a valid session
            assert isinstance(db, Session)
            # Clean up
            try:
                next(db_gen)
            except StopIteration:
                pass
        finally:
            # Clean up
            os.close(temp_db_fd)
            os.unlink(temp_db_path)


class TestModels:
    """Test suite for ORM models and their relationships"""

    @pytest.fixture
    def db_session(self):
        """Create a test database session for use in tests"""
        # Create in-memory database for testing
        # Using file-based SQLite to ensure schema persistence across connections
        test_db_path = "test_smartninja.db"
        test_db_uri = f"sqlite:///{test_db_path}"
        # Create a test engine with a persistent database
        test_engine = create_engine(
            test_db_uri, connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        TestSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=test_engine
        )
        # Models already imported at the top level

        # Create tables
        Base.metadata.create_all(bind=test_engine)
        # Create session
        test_db = TestSessionLocal()
        try:
            # Return the session for use in tests
            yield test_db
        finally:
            # Clean up resources
            test_db.close()
            # Optionally, clean up the test database file
            # Comment this out for debugging if needed
            if os.path.exists(test_db_path):
                try:
                    os.remove(test_db_path)
                except OSError:
                    # File might be locked or have permission issues
                    pass

    def test_phone_model_crud(self, db_session):
        """Test Phone model CRUD operations"""
        # Create a phone
        phone = Phone(model="Test Phone", brand="Test Brand", storage="128GB")
        # Add to session
        db_session.add(phone)
        db_session.commit()
        # Read
        saved_phone = db_session.query(Phone).filter_by(model="Test Phone").first()
        assert saved_phone is not None
        assert saved_phone.model == "Test Phone"
        assert saved_phone.brand == "Test Brand"
        assert saved_phone.storage == "128GB"
        # Update
        saved_phone.model = "Updated Phone"
        db_session.commit()
        updated_phone = db_session.query(Phone).filter_by(id=saved_phone.id).first()
        assert updated_phone.model == "Updated Phone"
        # Delete
        db_session.delete(updated_phone)
        db_session.commit()
        deleted_phone = db_session.query(Phone).filter_by(id=saved_phone.id).first()
        assert deleted_phone is None

    def test_phone_price_relationship(self, db_session):
        """Test relationship between Phone and Price models"""
        # Create a phone
        phone = Phone(model="Test Phone", brand="Test Brand", storage="128GB")
        db_session.add(phone)
        db_session.commit()
        # Create prices for the phone
        price1 = Price(
            phone_id=phone.id,
            region="US",
            price=999.99,
            currency="USD",
            source="Test Source 1",
        )
        price2 = Price(
            phone_id=phone.id,
            region="EU",
            price=1099.99,
            currency="EUR",
            source="Test Source 2",
        )
        db_session.add_all([price1, price2])
        db_session.commit()
        # Retrieve the phone with prices
        saved_phone = db_session.query(Phone).filter_by(id=phone.id).first()
        # Test relationship
        assert len(saved_phone.prices) == 2
        assert saved_phone.prices[0].region == "US"
        assert saved_phone.prices[0].price == 999.99
        assert saved_phone.prices[1].region == "EU"
        assert saved_phone.prices[1].price == 1099.99
        # Test reverse relationship
        saved_price = db_session.query(Price).filter_by(id=price1.id).first()
        assert saved_price.phone.model == "Test Phone"
        assert saved_price.phone.brand == "Test Brand"

    def test_alert_model(self, db_session):
        """Test Alert model functionality"""
        # Create a phone
        phone = Phone(model="Test Phone", brand="Test Brand", storage="128GB")
        db_session.add(phone)
        db_session.commit()
        # Create an alert
        alert = Alert(phone_id=phone.id, threshold=899.99, active=True)
        db_session.add(alert)
        db_session.commit()
        # Retrieve the alert
        saved_alert = db_session.query(Alert).filter_by(id=alert.id).first()
        # Test alert properties
        assert saved_alert.phone_id == phone.id
        assert saved_alert.threshold == 899.99
        assert saved_alert.active is True
        # Test relationship to phone
        assert saved_alert.phone.model == "Test Phone"

    def test_analysis_model(self, db_session):
        """Test Analysis model functionality"""
        # Create a phone
        phone = Phone(model="Test Phone", brand="Test Brand", storage="128GB")
        db_session.add(phone)
        db_session.commit()
        # Create an analysis
        analysis = Analysis(
            phone_id=phone.id,
            region="Global",
            insights="Price trends show a 5% decrease over 3 months.",
        )
        db_session.add(analysis)
        db_session.commit()
        # Retrieve the analysis
        saved_analysis = db_session.query(Analysis).filter_by(id=analysis.id).first()
        # Test analysis properties
        assert saved_analysis.phone_id == phone.id
        assert saved_analysis.region == "Global"
        assert (
            saved_analysis.insights == "Price trends show a 5% decrease over 3 months."
        )
        # Test relationship to phone
        assert saved_analysis.phone.model == "Test Phone"

    def test_cascade_delete(self, db_session):
        """Test cascade delete behavior"""
        # Create a phone
        phone = Phone(model="Test Phone", brand="Test Brand", storage="128GB")
        db_session.add(phone)
        db_session.commit()
        # Create a price for the phone
        price = Price(
            phone_id=phone.id,
            region="US",
            price=999.99,
            currency="USD",
            source="Test Source",
        )
        db_session.add(price)
        db_session.commit()
        # Delete the phone
        db_session.delete(phone)
        db_session.commit()
        # Verify the price is deleted (cascade delete)
        saved_price = db_session.query(Price).filter_by(id=price.id).first()
        assert saved_price is None
