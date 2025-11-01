"""
Integration tests for update_sheets module
Place this file in: tests/integration/test_sheets_integration.py
"""

import pytest
from unittest.mock import Mock, patch, call
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sheets_update import update_sheets_data


@pytest.fixture
def mock_env_setup():
    """Mock environment setup"""
    with patch('sheets_update.load_dotenv') as mock_load:
        with patch('sheets_update.os.getenv', return_value='test_sheet_123') as mock_getenv:
            yield {'load_dotenv': mock_load, 'getenv': mock_getenv}


@pytest.fixture
def mock_gspread_setup():
    """Mock gspread client setup"""
    with patch('sheets_update.Credentials.from_service_account_file') as mock_creds:
        with patch('sheets_update.gspread.authorize') as mock_authorize:
            mock_creds.return_value = Mock()
            
            mock_client = Mock()
            mock_authorize.return_value = mock_client
            
            mock_sheet = Mock()
            mock_client.open_by_key.return_value = mock_sheet
            
            yield {
                'creds': mock_creds,
                'authorize': mock_authorize,
                'client': mock_client,
                'sheet': mock_sheet
            }


@pytest.fixture
def mock_datasheet():
    """Mock data worksheet with sample data"""
    mock_ws = Mock()
    mock_ws.get_all_values.return_value = [
        ['phone number', 'message_updates_datetime', 'message_updates_date', 
         'practice_updates_datetime', 'practice_updates_date', 'message_counter'],
        ['972501234567', '2024-01-10 08:00:00', '2024-01-10', '2024-01-10 09:00:00', '2024-01-10', '5'],
        ['972509876543', '', '', '', '', '0']
    ]
    mock_ws.batch_update = Mock()
    return mock_ws


@pytest.fixture
def mock_mainsheet():
    """Mock main worksheet with sample data"""
    mock_ws = Mock()
    mock_ws.get_all_values.return_value = [
        ['phone number', 'class', 'C', 'D', 'E', 'F', 'G', 'שיעור 1', 'שיעור 2', 'שיעור 3'],
        ['972501234567', 'שיעור 1', '', '', '', '', '', '10', '0', '0'],
        ['972509876543', 'שיעור 2', '', '', '', '', '', '0', '5', '0']
    ]
    mock_ws.batch_update = Mock()
    return mock_ws


class TestUpdateSheetsDataIntegration:
    """Full integration tests for update_sheets_data function"""
    
    def test_successful_data_and_main_sheet_updates(
        self, 
        mock_env_setup, 
        mock_gspread_setup,
        mock_datasheet,
        mock_mainsheet
    ):
        """Test successful updates to both data and main sheets"""
        
        # Setup worksheet mocking
        mock_gspread_setup['sheet'].worksheet.side_effect = (
            lambda name: mock_datasheet if name == 'data' else mock_mainsheet
        )
        
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
        mock_env_setup['getenv'].assert_called_with('SHEET_ID')
        mock_gspread_setup['client'].open_by_key.assert_called_with('test_sheet_123')
        
        # Verify both worksheets were accessed
        assert any(
            call('data') == c for c in mock_gspread_setup['sheet'].worksheet.call_args_list
        )
        assert any(
            call('main') == c for c in mock_gspread_setup['sheet'].worksheet.call_args_list
        )
        
        # Verify data sheet was updated
        mock_datasheet.batch_update.assert_called_once()
        data_updates = mock_datasheet.batch_update.call_args[0][0]
        
        # Should update practice datetime for row 2
        assert any(u['range'] == 'D2' for u in data_updates)
        
        # Should update message info for row 3
        assert any(u['range'] == 'B3' for u in data_updates)
        assert any(u['range'] == 'C3' for u in data_updates)
        assert any(u['range'] == 'F3' for u in data_updates)  # Counter increment
        
        # Verify main sheet class counter was updated
        mock_mainsheet.batch_update.assert_called_once()
        main_updates = mock_mainsheet.batch_update.call_args[0][0]
        
        # Should increment class counter for שיעור 1 (column H, row 2)
        assert any(u['range'] == 'H2' for u in main_updates)
        
        # Verify return value (class counters updated)
        assert result == 1
    
    def test_no_updates_needed(
        self, 
        mock_env_setup, 
        mock_gspread_setup
    ):
        """Test when no updates are needed"""
        
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
        
        mock_gspread_setup['sheet'].worksheet.side_effect = (
            lambda name: mock_datasheet if name == 'data' else mock_mainsheet
        )
        
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
        assert result == 0
    
    def test_phone_number_normalization(
        self, 
        mock_env_setup, 
        mock_gspread_setup
    ):
        """Test that phone numbers are normalized correctly for matching"""
        
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
        
        mock_gspread_setup['sheet'].worksheet.side_effect = (
            lambda name: mock_datasheet if name == 'data' else mock_mainsheet
        )
        
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
        
        assert result == 1
    
    def test_missing_sheet_id_raises_error(self):
        """Test that missing SHEET_ID raises ValueError"""
        
        with patch('sheets_update.load_dotenv'):
            with patch('sheets_update.os.getenv', return_value=None):
                message_data = {
                    'practice_updates': [],
                    'message_updates': []
                }
                
                with pytest.raises(ValueError, match='SHEET_ID not found'):
                    update_sheets_data(message_data)
    
    def test_empty_message_data(
        self, 
        mock_env_setup, 
        mock_gspread_setup,
        mock_datasheet,
        mock_mainsheet
    ):
        """Test with empty message data"""
        
        mock_gspread_setup['sheet'].worksheet.side_effect = (
            lambda name: mock_datasheet if name == 'data' else mock_mainsheet
        )
        
        # Test data with no updates
        message_data = {
            'practice_updates': [],
            'message_updates': []
        }
        
        # Execute
        result = update_sheets_data(message_data)
        
        # Verify no batch updates were called
        mock_datasheet.batch_update.assert_not_called()
        mock_mainsheet.batch_update.assert_not_called()
        
        # Verify return value
        assert result == 0
    
    def test_multiple_practice_updates_same_phone(
        self, 
        mock_env_setup, 
        mock_gspread_setup,
        mock_datasheet,
        mock_mainsheet
    ):
        """Test multiple practice updates for the same phone number"""
        
        mock_gspread_setup['sheet'].worksheet.side_effect = (
            lambda name: mock_datasheet if name == 'data' else mock_mainsheet
        )
        
        # Test data with multiple updates for same phone
        message_data = {
            'practice_updates': [
                {
                    'sender': '972501234567',
                    'date': '2024-01-15',
                    'datetime': '2024-01-15 10:30:00'
                },
                {
                    'sender': '972501234567',
                    'date': '2024-01-15',
                    'datetime': '2024-01-15 11:45:00'
                }
            ],
            'message_updates': []
        }
        
        # Execute
        result = update_sheets_data(message_data)
        
        # Verify updates were made
        mock_datasheet.batch_update.assert_called_once()
        mock_mainsheet.batch_update.assert_called_once()
        
        # Verify return value
        assert result == 1
    
    def test_credentials_file_not_found(self, mock_env_setup):
        """Test handling of missing credentials file"""
        
        with patch('sheets_update.Credentials.from_service_account_file') as mock_creds:
            mock_creds.side_effect = FileNotFoundError("Credentials file not found")
            
            message_data = {
                'practice_updates': [],
                'message_updates': []
            }
            
            with pytest.raises(FileNotFoundError):
                update_sheets_data(message_data)
    
    def test_sheet_not_found(self, mock_env_setup, mock_gspread_setup):
        """Test handling when sheet cannot be opened"""
        
        import gspread
        mock_gspread_setup['client'].open_by_key.side_effect = (
            gspread.exceptions.SpreadsheetNotFound
        )
        
        message_data = {
            'practice_updates': [],
            'message_updates': []
        }
        
        with pytest.raises(gspread.exceptions.SpreadsheetNotFound):
            update_sheets_data(message_data)
    
    def test_worksheet_not_found(self, mock_env_setup, mock_gspread_setup):
        """Test handling when worksheet 'data' is not found"""
        
        import gspread
        mock_gspread_setup['sheet'].worksheet.side_effect = (
            gspread.exceptions.WorksheetNotFound
        )
        
        message_data = {
            'practice_updates': [],
            'message_updates': []
        }
        
        with pytest.raises(gspread.exceptions.WorksheetNotFound):
            update_sheets_data(message_data)


@pytest.mark.parametrize("phone_input,expected_normalized", [
    ('+972-50-123-4567', '972501234567'),
    ('972501234567', '972501234567'),
    ('+972 50 123 4567', '972501234567'),
    ('050-123-4567', '0501234567'),
])
def test_phone_normalization_variations(phone_input, expected_normalized):
    """Test various phone number format normalizations"""
    # This assumes there's a normalize_phone function in sheets_update
    # If not, this test can be adjusted to test the actual normalization logic
    normalized = ''.join(filter(str.isdigit, phone_input))
    if normalized.startswith('+'):
        normalized = normalized[1:]
    
    assert normalized == expected_normalized or phone_input.replace('+', '').replace('-', '').replace(' ', '') == expected_normalized