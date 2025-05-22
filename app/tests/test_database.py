import os
import sys
import tempfile
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# pylint: disable=wrong-import-position,invalid-name
from app.core.models import Alert, Analysis, Base, Phone, Price


class TestDatabaseModels(unittest.TestCase):
    """Test suite for database models and connections"""

    def setUp(self):
        """Set up test database"""
        # Create temporary database for testing
        # pylint: disable=consider-using-with
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db")
        self.engine = create_engine(
            f"sqlite:///{self.temp_db.name}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        # Create tables
        Base.metadata.create_all(self.engine)
        # Create session
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):
        """Clean up after tests"""
        self.session.close()
        self.temp_db.close()

    def test_phone_model(self):
        """Test Phone model functionality"""
        # Create test phone
        test_phone = Phone(model="Test Phone", brand="Test Brand", storage="128GB")
        # Add to session
        self.session.add(test_phone)
        self.session.commit()
        # Query and verify
        queried_phone = self.session.query(Phone).filter_by(model="Test Phone").first()
        self.assertIsNotNone(queried_phone)
        self.assertEqual(queried_phone.model, "Test Phone")
        self.assertEqual(queried_phone.brand, "Test Brand")
        self.assertEqual(queried_phone.storage, "128GB")

    def test_price_model(self):
        """Test Price model functionality"""
        # Create test phone
        test_phone = Phone(model="Test Phone", brand="Test Brand", storage="128GB")
        # Add to session
        self.session.add(test_phone)
        self.session.commit()
        # Create test price
        test_price = Price(
            phone_id=test_phone.id,
            region="US",
            price=999.99,
            currency="USD",
            source="test_source",
        )
        # Add to session
        self.session.add(test_price)
        self.session.commit()
        # Query and verify
        queried_price = (
            self.session.query(Price).filter_by(phone_id=test_phone.id).first()
        )
        self.assertIsNotNone(queried_price)
        self.assertEqual(queried_price.region, "US")
        self.assertEqual(queried_price.price, 999.99)
        self.assertEqual(queried_price.currency, "USD")
        self.assertEqual(queried_price.source, "test_source")

    def test_relationship(self):
        """Test relationship between Phone and Price models"""
        # Create test phone
        test_phone = Phone(model="Test Phone", brand="Test Brand", storage="128GB")
        # Add to session
        self.session.add(test_phone)
        self.session.commit()
        # Create test prices
        test_price_1 = Price(
            phone_id=test_phone.id,
            region="US",
            price=999.99,
            currency="USD",
            source="test_source_1",
        )
        test_price_2 = Price(
            phone_id=test_phone.id,
            region="EU",
            price=1099.99,
            currency="EUR",
            source="test_source_2",
        )
        # Add to session
        self.session.add_all([test_price_1, test_price_2])
        self.session.commit()
        # Query phone and check relationship
        queried_phone = self.session.query(Phone).filter_by(id=test_phone.id).first()
        self.assertEqual(len(queried_phone.prices), 2)
        self.assertEqual(queried_phone.prices[0].region, "US")
        self.assertEqual(queried_phone.prices[1].region, "EU")

    def test_alert_model(self):
        """Test Alert model functionality"""
        # Create test phone
        test_phone = Phone(model="Test Phone", brand="Test Brand", storage="128GB")
        # Add to session
        self.session.add(test_phone)
        self.session.commit()
        # Create test alert
        test_alert = Alert(phone_id=test_phone.id, threshold=899.99, active=True)
        # Add to session
        self.session.add(test_alert)
        self.session.commit()
        # Query and verify
        queried_alert = (
            self.session.query(Alert).filter_by(phone_id=test_phone.id).first()
        )
        self.assertIsNotNone(queried_alert)
        self.assertEqual(queried_alert.threshold, 899.99)
        self.assertTrue(queried_alert.active)

    def test_analysis_model(self):
        """Test Analysis model functionality"""
        # Create test phone
        test_phone = Phone(model="Test Phone", brand="Test Brand", storage="128GB")
        # Add to session
        self.session.add(test_phone)
        self.session.commit()
        # Create test analysis
        test_analysis = Analysis(
            phone_id=test_phone.id,
            region="Global",
            insights="Test insights for phone prices",
        )
        # Add to session
        self.session.add(test_analysis)
        self.session.commit()
        # Query and verify
        queried_analysis = (
            self.session.query(Analysis).filter_by(phone_id=test_phone.id).first()
        )
        self.assertIsNotNone(queried_analysis)
        self.assertEqual(queried_analysis.region, "Global")
        self.assertEqual(queried_analysis.insights, "Test insights for phone prices")


if __name__ == "__main__":
    unittest.main()
