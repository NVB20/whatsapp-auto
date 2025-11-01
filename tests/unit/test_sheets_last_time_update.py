import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os
import gspread


@pytest.fixture
def mock_credentials():
    """Mock Google OAuth2 credentials"""
    with patch('sheets_last_update.Credentials.from_service_account_file') as mock_creds:
        mock_creds.return_value = Mock()
        yield mock_creds


@pytest.fixture
def mock_gspread_client():
    """Mock gspread client and related objects"""
    with patch('sheets_last_update.gspread.authorize') as mock_authorize:
        # Create mock chain: client -> sheet -> worksheet
        mock_worksheet = Mock()
        mock_sheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        mock_client = Mock()
        mock_client.open_by_key.return_value = mock_sheet
        mock_authorize.return_value = mock_client
        
        yield {
            'authorize': mock_authorize,
            'client': mock_client,
            'sheet': mock_sheet,
            'worksheet': mock_worksheet
        }


@pytest.fixture
def mock_env_vars():
    """Mock environment variables"""
    with patch.dict(os.environ, {'SHEET_ID': 'test_sheet_id_12345'}, clear=False):
        yield


@pytest.fixture
def mock_load_dotenv():
    """Mock load_dotenv function"""
    with patch('sheets_last_update.load_dotenv') as mock_load:
        yield mock_load


@pytest.fixture
def mock_datetime():
    """Mock datetime to return consistent values"""
    # Create a mock datetime that returns a real datetime object
    mock_dt = Mock()
    fixed_datetime = datetime(2025, 11, 1, 14, 30, 45)
    mock_dt.now.return_value = fixed_datetime
    
    with patch('sheets_last_update.datetime', mock_dt):
        yield mock_dt


class TestLastTimeUpdated:
    
    def test_last_time_updated_success(
        self, 
        mock_credentials, 
        mock_gspread_client, 
        mock_env_vars, 
        mock_load_dotenv,
        mock_datetime
    ):
        """Test successful execution of last_time_updated"""
        from sheets_last_update import last_time_updated
        
        # Execute the function
        last_time_updated()
        
        # Verify credentials were loaded correctly
        mock_credentials.assert_called_once_with(
            "sheets-api-cred.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        # Verify gspread client was authorized
        mock_gspread_client['authorize'].assert_called_once()
        
        # Verify sheet was opened with correct ID
        mock_gspread_client['client'].open_by_key.assert_called_once_with('test_sheet_id_12345')
        
        # Verify worksheet was accessed
        mock_gspread_client['sheet'].worksheet.assert_called_once_with("dashboard")
        
        # Verify cell was updated with correct formatted datetime
        expected_datetime = "'01-11 14:30"
        mock_gspread_client['worksheet'].update_acell.assert_called_once_with('C9', expected_datetime)
        
        # Verify load_dotenv was called
        mock_load_dotenv.assert_called_once()
    
    
    def test_last_time_updated_missing_sheet_id(
        self, 
        mock_credentials, 
        mock_gspread_client, 
        mock_load_dotenv
    ):
        """Test that ValueError is raised when SHEET_ID is not in environment"""
        # Clear the environment and reload the module
        with patch('sheets_last_update.load_dotenv'):
            with patch('sheets_last_update.os.getenv', return_value=None):
                from sheets_last_update import last_time_updated
                
                with pytest.raises(ValueError, match="SHEET_ID not found in environment variables!"):
                    last_time_updated()
    
    
    def test_last_time_updated_credentials_file_not_found(
        self, 
        mock_env_vars, 
        mock_load_dotenv
    ):
        """Test handling of missing credentials file"""
        with patch('sheets_last_update.Credentials.from_service_account_file') as mock_creds:
            mock_creds.side_effect = FileNotFoundError("Credentials file not found")
            
            from sheets_last_update import last_time_updated
            
            with pytest.raises(FileNotFoundError):
                last_time_updated()
    
    
    def test_last_time_updated_sheet_not_found(
        self, 
        mock_credentials, 
        mock_gspread_client, 
        mock_env_vars, 
        mock_load_dotenv
    ):
        """Test handling when sheet cannot be opened"""
        mock_gspread_client['client'].open_by_key.side_effect = gspread.exceptions.SpreadsheetNotFound
        
        from sheets_last_update import last_time_updated
        
        with pytest.raises(gspread.exceptions.SpreadsheetNotFound):
            last_time_updated()
    
    
    def test_last_time_updated_worksheet_not_found(
        self, 
        mock_credentials, 
        mock_gspread_client, 
        mock_env_vars, 
        mock_load_dotenv
    ):
        """Test handling when worksheet 'dashboard' is not found"""
        mock_gspread_client['sheet'].worksheet.side_effect = gspread.exceptions.WorksheetNotFound
        
        from sheets_last_update import last_time_updated
        
        with pytest.raises(gspread.exceptions.WorksheetNotFound):
            last_time_updated()
    
    
    def test_datetime_formatting(
        self, 
        mock_credentials, 
        mock_gspread_client, 
        mock_env_vars, 
        mock_load_dotenv
    ):
        """Test that datetime is formatted correctly with leading apostrophe"""
        # Create a mock datetime that returns a real datetime object
        mock_dt = Mock()
        fixed_datetime = datetime(2025, 1, 5, 9, 7, 0)
        mock_dt.now.return_value = fixed_datetime
        
        with patch('sheets_last_update.datetime', mock_dt):
            from sheets_last_update import last_time_updated
            
            last_time_updated()
            
            # Should format as '05-01 09:07
            expected_datetime = "'05-01 09:07"
            mock_gspread_client['worksheet'].update_acell.assert_called_once_with('C9', expected_datetime)
    
    
    @patch('sheets_last_update.print')
    def test_print_statements(
        self, 
        mock_print,
        mock_credentials, 
        mock_gspread_client, 
        mock_env_vars, 
        mock_load_dotenv,
        mock_datetime
    ):
        """Test that print statements are called with correct messages"""
        from sheets_last_update import last_time_updated
        
        last_time_updated()
        
        # Verify print statements
        assert mock_print.call_count == 2
        mock_print.assert_any_call("Loaded Sheet ID: test_sheet_id_12345")
        mock_print.assert_any_call("Updated cell C9 with: 01-11 14:30")