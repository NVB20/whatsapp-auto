"""
Integration tests for update_sheets module
Place this file in: tests/integration/test_sheets_integration.py
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Now import your actual function
from sheets_update import update_sheets_data


class TestUpdateSheetsDataIntegration(unittest.TestCase):
    """Full integration tests for update_sheets_data function"""
    
    @patch('sheets_update.load_dotenv')
    @patch('sheets_update.os.getenv')
    @patch('sheets_update.gspread.authorize')
    @patch('sheets_update.Credentials.from_service_account_file')
    def test_successful_data_and_main_sheet_updates(self, mock_creds, mock_authorize, mock_getenv, mock_load_dotenv):
        """Test successful updates to both data and main sheets"""
        
        # Setup mocks
        mock_getenv.return_value = 'test_sheet_123'
        mock_creds.return_value = Mock()
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        mock_sheet = Mock()
        mock_client.open_by_key.return_value = mock_sheet
        
        # Mock data worksheet
        mock_datasheet = Mock()
        mock_datasheet.get_all_values.return_value = [
            ['phone number', 'message_updates_datetime', 'message_updates_date', 
             'practice_updates_datetime', 'practice_updates_date', 'message_counter'],
            ['972501234567', '2024-01-10 08:00:00', '2024-01-10', '2024-01-10 09:00:00', '2024-01-10', '5'],
            ['972509876543', '', '', '', '', '0']
        ]
        mock_datasheet.batch_update = Mock()
        
        # Mock main worksheet
        mock_mainsheet = Mock()
        mock_mainsheet.get_all_values.return_value = [
            ['phone number', 'class', 'C', 'D', 'E', 'F', 'G', 'שיעור 1', 'שיעור 2', 'שיעור 3'],
            ['972501234567', 'שיעור 1', '', '', '', '', '', '10', '0', '0'],
            ['972509876543', 'שיעור 2', '', '', '', '', '', '0', '5', '0']
        ]
        mock_mainsheet.batch_update = Mock()
        
        mock_sheet.worksheet.side_effect = lambda name: mock_datasheet if name == 'data' else mock_mainsheet
        
        # Test data with updates
        message_data = {
            'practice_updates': [
                {
                    'sender': '972501234567',
                    'date': '2024-01-15',
                    'datetime': '2024-01-15 10:30:00'
                }
            ],
            'message_updates': [
                {
                    'sender': '972509876543',
                    'date': '2024-01-15',
                    'datetime': '2024-01-15 09:15:00'
                }
            ]
        }
        
        # Execute
        result = update_sheets_data(message_data)
        
        # Verify
        mock_getenv.assert_called_with('SHEET_ID')
        mock_client.open_by_key.assert_called_with('test_sheet_123')
        mock_sheet.worksheet.assert_any_call('data')
        mock_sheet.worksheet.assert_any_call('main')
        
        # Verify data sheet was updated
        mock_datasheet.batch_update.assert_called_once()
        data_updates = mock_datasheet.batch_update.call_args[0][0]
        
        # Should update practice datetime for row 2
        self.assertTrue(any(u['range'] == 'D2' for u in data_updates))
        
        # Should update message info for row 3
        self.assertTrue(any(u['range'] == 'B3' for u in data_updates))
        self.assertTrue(any(u['range'] == 'C3' for u in data_updates))
        self.assertTrue(any(u['range'] == 'F3' for u in data_updates))  # Counter increment
        
        # Verify main sheet class counter was updated
        mock_mainsheet.batch_update.assert_called_once()
        main_updates = mock_mainsheet.batch_update.call_args[0][0]
        
        # Should increment class counter for שיעור 1 (column H, row 2)
        self.assertTrue(any(u['range'] == 'H2' for u in main_updates))
        
        # Verify return value (class counters updated)
        self.assertEqual(result, 1)
    
    @patch('sheets_update.load_dotenv')
    @patch('sheets_update.os.getenv')
    @patch('sheets_update.gspread.authorize')
    @patch('sheets_update.Credentials.from_service_account_file')
    def test_no_updates_needed(self, mock_creds, mock_authorize, mock_getenv, mock_load_dotenv):
        """Test when no updates are needed"""
        
        # Setup mocks
        mock_getenv.return_value = 'test_sheet_123'
        mock_creds.return_value = Mock()
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        mock_sheet = Mock()
        mock_client.open_by_key.return_value = mock_sheet
        
        # Mock data worksheet with no matching phones
        mock_datasheet = Mock()
        mock_datasheet.get_all_values.return_value = [
            ['phone number', 'message_updates_datetime', 'message_updates_date', 
             'practice_updates_datetime', 'practice_updates_date', 'message_counter'],
            ['972501111111', '', '', '', '', '0']  # Different phone number
        ]
        mock_datasheet.batch_update = Mock()
        
        # Mock main worksheet
        mock_mainsheet = Mock()
        mock_mainsheet.get_all_values.return_value = [
            ['phone number', 'class', 'C', 'D', 'E', 'F', 'G', 'שיעור 1'],
            ['972501111111', 'שיעור 1', '', '', '', '', '', '0']
        ]
        mock_mainsheet.batch_update = Mock()
        
        mock_sheet.worksheet.side_effect = lambda name: mock_datasheet if name == 'data' else mock_mainsheet
        
        # Test data
        message_data = {
            'practice_updates': [
                {
                    'sender': '972509999999',  # Not in sheet
                    'date': '2024-01-15',
                    'datetime': '2024-01-15 10:30:00'
                }
            ],
            'message_updates': []
        }
        
        # Execute
        result = update_sheets_data(message_data)
        
        # Verify no batch updates were called
        mock_datasheet.batch_update.assert_not_called()
        mock_mainsheet.batch_update.assert_not_called()
        
        # Verify return value
        self.assertEqual(result, 0)
    
    @patch('sheets_update.load_dotenv')
    @patch('sheets_update.os.getenv')
    @patch('sheets_update.gspread.authorize')
    @patch('sheets_update.Credentials.from_service_account_file')
    def test_phone_number_normalization(self, mock_creds, mock_authorize, mock_getenv, mock_load_dotenv):
        """Test that phone numbers are normalized correctly for matching"""
        
        # Setup mocks
        mock_getenv.return_value = 'test_sheet_123'
        mock_creds.return_value = Mock()
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        mock_sheet = Mock()
        mock_client.open_by_key.return_value = mock_sheet
        
        # Mock data worksheet with formatted phone
        mock_datasheet = Mock()
        mock_datasheet.get_all_values.return_value = [
            ['phone number', 'message_updates_datetime', 'message_updates_date', 
             'practice_updates_datetime', 'practice_updates_date', 'message_counter'],
            ['+972-50-123-4567', '', '', '', '', '0']  # Formatted phone
        ]
        mock_datasheet.batch_update = Mock()
        
        # Mock main worksheet
        mock_mainsheet = Mock()
        mock_mainsheet.get_all_values.return_value = [
            ['phone number', 'class', 'C', 'D', 'E', 'F', 'G', 'שיעור 1'],
            ['+972-50-123-4567', 'שיעור 1', '', '', '', '', '', '0']
        ]
        mock_mainsheet.batch_update = Mock()
        
        mock_sheet.worksheet.side_effect = lambda name: mock_datasheet if name == 'data' else mock_mainsheet
        
        # Test data with normalized phone
        message_data = {
            'practice_updates': [
                {
                    'sender': '972501234567',  # Normalized version
                    'date': '2024-01-15',
                    'datetime': '2024-01-15 10:30:00'
                }
            ],
            'message_updates': []
        }
        
        # Execute
        result = update_sheets_data(message_data)
        
        # Verify updates were made despite different formatting
        mock_datasheet.batch_update.assert_called_once()
        mock_mainsheet.batch_update.assert_called_once()
        
        self.assertEqual(result, 1)
    
    @patch('sheets_update.load_dotenv')
    @patch('sheets_update.os.getenv')
    def test_missing_sheet_id_raises_error(self, mock_getenv, mock_load_dotenv):
        """Test that missing SHEET_ID raises ValueError"""
        
        mock_getenv.return_value = None
        
        message_data = {
            'practice_updates': [],
            'message_updates': []
        }
        
        with self.assertRaises(ValueError) as context:
            update_sheets_data(message_data)
        
        self.assertIn('SHEET_ID not found', str(context.exception))


if __name__ == '__main__':
    unittest.main()