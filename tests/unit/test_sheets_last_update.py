"""
Tests for last_time_updated module
Place this file in: tests/unit/test_last_time_updated.py
"""

import unittest
from unittest.mock import Mock, patch, call
from datetime import datetime
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sheets_last_update import last_time_updated


class TestLastTimeUpdated(unittest.TestCase):
    """Test suite for last_time_updated function"""
    
    @patch('sheets_last_update.datetime')
    @patch('sheets_last_update.load_dotenv')
    @patch('sheets_last_update.os.getenv')
    @patch('sheets_last_update.gspread.authorize')
    @patch('sheets_last_update.Credentials.from_service_account_file')
    def test_successful_timestamp_update(self, mock_creds, mock_authorize, mock_getenv, mock_load_dotenv, mock_datetime):
        """Test successful update of timestamp to dashboard"""
        
        # Setup mocks
        mock_getenv.return_value = 'test_sheet_123'
        mock_creds.return_value = Mock()
        
        # Mock datetime to return a fixed time
        fixed_datetime = datetime(2024, 1, 15, 14, 30, 45)
        mock_datetime.now.return_value = fixed_datetime
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        mock_sheet = Mock()
        mock_client.open_by_key.return_value = mock_sheet
        
        mock_worksheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        
        # Execute
        last_time_updated()
        
        # Verify credentials were loaded
        mock_creds.assert_called_once_with(
            "sheets-api-cred.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        # Verify client was authorized
        mock_authorize.assert_called_once()
        
        # Verify environment variable was loaded
        mock_load_dotenv.assert_called_once()
        mock_getenv.assert_called_once_with('SHEET_ID')
        
        # Verify sheet was opened
        mock_client.open_by_key.assert_called_once_with('test_sheet_123')
        
        # Verify dashboard worksheet was accessed
        mock_sheet.worksheet.assert_called_once_with('dashboard')
        
        # Verify cell was updated with correct format
        expected_timestamp = "'15-01 14:30"
        mock_worksheet.update_acell.assert_called_once_with('C9', expected_timestamp)
    
    @patch('sheets_last_update.datetime')
    @patch('sheets_last_update.load_dotenv')
    @patch('sheets_last_update.os.getenv')
    @patch('sheets_last_update.gspread.authorize')
    @patch('sheets_last_update.Credentials.from_service_account_file')
    def test_timestamp_format(self, mock_creds, mock_authorize, mock_getenv, mock_load_dotenv, mock_datetime):
        """Test that timestamp is formatted correctly (DD-MM HH:MM)"""
        
        # Setup mocks
        mock_getenv.return_value = 'test_sheet_123'
        mock_creds.return_value = Mock()
        
        # Test different datetime values
        test_cases = [
            (datetime(2024, 12, 31, 23, 59, 59), "'31-12 23:59"),
            (datetime(2024, 1, 1, 0, 0, 0), "'01-01 00:00"),
            (datetime(2024, 6, 15, 9, 5, 30), "'15-06 09:05"),
        ]
        
        for test_datetime, expected_format in test_cases:
            with self.subTest(datetime=test_datetime):
                mock_datetime.now.return_value = test_datetime
                
                mock_client = Mock()
                mock_authorize.return_value = mock_client
                
                mock_sheet = Mock()
                mock_client.open_by_key.return_value = mock_sheet
                
                mock_worksheet = Mock()
                mock_sheet.worksheet.return_value = mock_worksheet
                
                # Execute
                last_time_updated()
                
                # Verify format
                mock_worksheet.update_acell.assert_called_with('C9', expected_format)
    
    @patch('sheets_last_update.load_dotenv')
    @patch('sheets_last_update.os.getenv')
    def test_missing_sheet_id_raises_error(self, mock_getenv, mock_load_dotenv):
        """Test that missing SHEET_ID raises ValueError"""
        
        mock_getenv.return_value = None
        
        with self.assertRaises(ValueError) as context:
            last_time_updated()
        
        self.assertIn('SHEET_ID not found', str(context.exception))
        mock_load_dotenv.assert_called_once()
    
    @patch('sheets_last_update.load_dotenv')
    @patch('sheets_last_update.os.getenv')
    def test_empty_sheet_id_raises_error(self, mock_getenv, mock_load_dotenv):
        """Test that empty SHEET_ID raises ValueError"""
        
        mock_getenv.return_value = ''
        
        with self.assertRaises(ValueError) as context:
            last_time_updated()
        
        self.assertIn('SHEET_ID not found', str(context.exception))
    
    @patch('sheets_last_update.datetime')
    @patch('sheets_last_update.load_dotenv')
    @patch('sheets_last_update.os.getenv')
    @patch('sheets_last_update.gspread.authorize')
    @patch('sheets_last_update.Credentials.from_service_account_file')
    def test_correct_cell_updated(self, mock_creds, mock_authorize, mock_getenv, mock_load_dotenv, mock_datetime):
        """Test that specifically cell C9 is updated"""
        
        # Setup mocks
        mock_getenv.return_value = 'test_sheet_123'
        mock_creds.return_value = Mock()
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30)
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        mock_sheet = Mock()
        mock_client.open_by_key.return_value = mock_sheet
        
        mock_worksheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        
        # Execute
        last_time_updated()
        
        # Verify only C9 was updated (not C10, D9, etc.)
        self.assertEqual(mock_worksheet.update_acell.call_count, 1)
        call_args = mock_worksheet.update_acell.call_args[0]
        self.assertEqual(call_args[0], 'C9')
    
    @patch('sheets_last_update.datetime')
    @patch('sheets_last_update.load_dotenv')
    @patch('sheets_last_update.os.getenv')
    @patch('sheets_last_update.gspread.authorize')
    @patch('sheets_last_update.Credentials.from_service_account_file')
    def test_dashboard_worksheet_accessed(self, mock_creds, mock_authorize, mock_getenv, mock_load_dotenv, mock_datetime):
        """Test that the 'dashboard' worksheet is specifically accessed"""
        
        # Setup mocks
        mock_getenv.return_value = 'test_sheet_123'
        mock_creds.return_value = Mock()
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30)
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        mock_sheet = Mock()
        mock_client.open_by_key.return_value = mock_sheet
        
        mock_worksheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        
        # Execute
        last_time_updated()
        
        # Verify dashboard worksheet was accessed (not 'data' or 'main')
        mock_sheet.worksheet.assert_called_once_with('dashboard')
    
    @patch('sheets_last_update.datetime')
    @patch('sheets_last_update.load_dotenv')
    @patch('sheets_last_update.os.getenv')
    @patch('sheets_last_update.gspread.authorize')
    @patch('sheets_last_update.Credentials.from_service_account_file')
    def test_timestamp_has_leading_apostrophe(self, mock_creds, mock_authorize, mock_getenv, mock_load_dotenv, mock_datetime):
        """Test that timestamp string starts with apostrophe to prevent Excel interpretation"""
        
        # Setup mocks
        mock_getenv.return_value = 'test_sheet_123'
        mock_creds.return_value = Mock()
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30)
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        mock_sheet = Mock()
        mock_client.open_by_key.return_value = mock_sheet
        
        mock_worksheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        
        # Execute
        last_time_updated()
        
        # Verify the timestamp starts with apostrophe
        call_args = mock_worksheet.update_acell.call_args[0]
        timestamp_value = call_args[1]
        self.assertTrue(timestamp_value.startswith("'"), 
                       f"Timestamp should start with apostrophe, got: {timestamp_value}")
    
    @patch('sheets_last_update.datetime')
    @patch('sheets_last_update.load_dotenv')
    @patch('sheets_last_update.os.getenv')
    @patch('sheets_last_update.gspread.authorize')
    @patch('sheets_last_update.Credentials.from_service_account_file')
    def test_credentials_file_path(self, mock_creds, mock_authorize, mock_getenv, mock_load_dotenv, mock_datetime):
        """Test that correct credentials file is used"""
        
        # Setup mocks
        mock_getenv.return_value = 'test_sheet_123'
        mock_creds.return_value = Mock()
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30)
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        mock_sheet = Mock()
        mock_client.open_by_key.return_value = mock_sheet
        
        mock_worksheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        
        # Execute
        last_time_updated()
        
        # Verify correct credentials file is used
        mock_creds.assert_called_once()
        call_args = mock_creds.call_args
        self.assertEqual(call_args[0][0], "sheets-api-cred.json")
        self.assertEqual(call_args[1]['scopes'], ["https://www.googleapis.com/auth/spreadsheets"])


class TestDatetimeFormatting(unittest.TestCase):
    """Test datetime formatting independently"""
    
    def test_datetime_format_string(self):
        """Test the datetime format string produces correct output"""
        format_string = "%d-%m %H:%M"
        
        test_cases = [
            (datetime(2024, 1, 1, 0, 0), "01-01 00:00"),
            (datetime(2024, 12, 31, 23, 59), "31-12 23:59"),
            (datetime(2024, 6, 15, 9, 5), "15-06 09:05"),
            (datetime(2024, 10, 5, 14, 30), "05-10 14:30"),
        ]
        
        for dt, expected in test_cases:
            with self.subTest(datetime=dt):
                result = dt.strftime(format_string)
                self.assertEqual(result, expected)
    
    def test_leading_zeros_in_format(self):
        """Test that single-digit days, months, hours, minutes have leading zeros"""
        dt = datetime(2024, 1, 5, 9, 3)
        result = dt.strftime("%d-%m %H:%M")
        
        # Should be 05-01 09:03, not 5-1 9:3
        self.assertEqual(result, "05-01 09:03")
        self.assertEqual(len(result), 11)  # DD-MM HH:MM = 11 chars


class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios"""
    
    @patch('sheets_last_update.datetime')
    @patch('sheets_last_update.load_dotenv')
    @patch('sheets_last_update.os.getenv')
    @patch('sheets_last_update.gspread.authorize')
    @patch('sheets_last_update.Credentials.from_service_account_file')
    def test_multiple_consecutive_updates(self, mock_creds, mock_authorize, mock_getenv, mock_load_dotenv, mock_datetime):
        """Test calling the function multiple times in succession"""
        
        # Setup mocks
        mock_getenv.return_value = 'test_sheet_123'
        mock_creds.return_value = Mock()
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        mock_sheet = Mock()
        mock_client.open_by_key.return_value = mock_sheet
        
        mock_worksheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        
        # First call
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30)
        last_time_updated()
        
        # Second call (1 minute later)
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 31)
        last_time_updated()
        
        # Verify both updates occurred
        self.assertEqual(mock_worksheet.update_acell.call_count, 2)
        
        # Verify different timestamps
        calls = mock_worksheet.update_acell.call_args_list
        self.assertEqual(calls[0][0][1], "'15-01 14:30")
        self.assertEqual(calls[1][0][1], "'15-01 14:31")


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestLastTimeUpdated))
    suite.addTests(loader.loadTestsFromTestCase(TestDatetimeFormatting))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_tests()