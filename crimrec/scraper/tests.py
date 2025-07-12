from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from unittest.mock import patch, MagicMock
import os
from .models import CriminalRecord
from .scrapers import EClerksScraper


class CriminalRecordModelTest(TestCase):
    def test_criminal_record_creation(self):
        """Test creating a criminal record"""
        record = CriminalRecord.objects.create(
            defendant_name="John Doe",
            sex="M",
            race="W",
            case_number="2023-12345",
            date_filed="2023-01-15",
            charges="Test charge",
            parish="Orleans"
        )
        
        self.assertEqual(record.defendant_name, "John Doe")
        self.assertEqual(record.case_number, "2023-12345")
        self.assertEqual(str(record), "John Doe - 2023-12345")

    def test_unique_case_number(self):
        """Test that case numbers must be unique"""
        CriminalRecord.objects.create(
            defendant_name="John Doe",
            case_number="2023-12345",
            date_filed="2023-01-15",
            charges="Test charge",
            parish="Orleans"
        )
        
        # This should work (update_or_create)
        record, created = CriminalRecord.objects.update_or_create(
            case_number="2023-12345",
            defaults={
                'defendant_name': "Jane Doe",
                'date_filed': "2023-01-15",
                'charges': "Updated charge",
                'parish': "Orleans"
            }
        )
        
        self.assertFalse(created)
        self.assertEqual(record.defendant_name, "Jane Doe")


class EClerksScraperTest(TestCase):
    @patch.dict(os.environ, {'ECLERKS_EMAIL': 'test@test.com', 'ECLERKS_PASSWORD': 'password'})
    def test_scraper_initialization_with_credentials(self):
        """Test scraper initializes with proper credentials"""
        with patch('scraper.scrapers.uc.Chrome') as mock_chrome:
            mock_chrome.return_value = MagicMock()
            scraper = EClerksScraper(headless=True)
            self.assertEqual(scraper.login_email, 'test@test.com')
            self.assertEqual(scraper.login_password, 'password')

    def test_scraper_initialization_without_credentials(self):
        """Test scraper fails without credentials"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                EClerksScraper(headless=True)

    def test_parse_date_valid_formats(self):
        """Test date parsing with various formats"""
        self.assertEqual(
            EClerksScraper.parse_date("01/15/2023").strftime("%Y-%m-%d"),
            "2023-01-15"
        )
        self.assertEqual(
            EClerksScraper.parse_date("2023-01-15").strftime("%Y-%m-%d"),
            "2023-01-15"
        )
        self.assertIsNone(EClerksScraper.parse_date(""))
        self.assertIsNone(EClerksScraper.parse_date("invalid"))


class RunScraperCommandTest(TestCase):
    @patch('scraper.management.commands.run_scraper.EClerksScraper')
    def test_run_scraper_command_success(self, mock_scraper_class):
        """Test successful scraper command execution"""
        mock_scraper = MagicMock()
        mock_scraper.run.return_value = True
        mock_scraper.records = []
        mock_scraper_class.return_value = mock_scraper
        
        # Should not raise an exception
        call_command('run_scraper', '--max-pages=1')
        
        mock_scraper.run.assert_called_once()

    @patch('scraper.management.commands.run_scraper.EClerksScraper')
    def test_run_scraper_command_failure(self, mock_scraper_class):
        """Test scraper command handles failure gracefully"""
        mock_scraper = MagicMock()
        mock_scraper.run.side_effect = Exception("Test error")
        mock_scraper_class.return_value = mock_scraper
        
        # Should not raise an exception but handle it gracefully
        call_command('run_scraper', '--max-pages=1')
