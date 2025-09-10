function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🚀 My Tools')
    .addItem('Check Inactive Names', 'checkInactiveNames')
    .addToUi();
}

function checkInactiveNames() {
  // Get the "main" sheet
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("main");
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Sheet 'main' not found!");
    return;
  }
  
  // Get all data from columns C and D
  const lastRow = sheet.getLastRow();
  
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert("No data found in the sheet!");
    return;
  }
  
  const namesRange = sheet.getRange("C2:C" + lastRow);
  const datesRange = sheet.getRange("D2:D" + lastRow);
  
  const names = namesRange.getValues();
  const dates = datesRange.getValues();
  
  // Calculate the date from one week ago
  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
  
  const inactiveList = [];
  
  // Check each row for inactive names
  for (let i = 0; i < names.length; i++) {
    const name = names[i][0];
    const date = dates[i][0];
    
    // Skip empty rows
    if (!name || !date) continue;
    
    // Convert date to Date object if it's not already
    let dateObj;
    if (date instanceof Date) {
      dateObj = date;
    } else {
      dateObj = new Date(date);
    }
    
    // Check if date is valid and older than one week
    if (!isNaN(dateObj.getTime()) && dateObj < oneWeekAgo) {
      // Format the date for display
      const formattedDate = Utilities.formatDate(dateObj, Session.getScriptTimeZone(), "MM/dd/yyyy");
      inactiveList.push(`${name} - ${formattedDate}`);
    }
  }
  
  // Display results in a popup
  if (inactiveList.length > 0) {
    const message = "Inactive Names (more than 1 week old):\n\n" + inactiveList.join("\n");
    
    // Create HTML dialog for better copying experience
    const htmlOutput = HtmlService.createHtmlOutput(`
      <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h3>Inactive Names (more than 1 week old)</h3>
        <textarea id="resultText" style="width: 100%; height: 300px; font-family: monospace;" readonly>${inactiveList.join("\n")}</textarea>
        <br><br>
        <button onclick="selectAll()" style="padding: 8px 16px; background-color: #4285f4; color: white; border: none; border-radius: 4px; cursor: pointer;">Select All</button>
        <button onclick="google.script.host.close()" style="padding: 8px 16px; background-color: #ea4335; color: white; border: none; border-radius: 4px; cursor: pointer; margin-left: 10px;">Close</button>
        
        <script>
          function selectAll() {
            document.getElementById('resultText').select();
            document.execCommand('copy');
            alert('Text copied to clipboard!');
          }
        </script>
      </div>
    `).setWidth(500).setHeight(400);
    
    SpreadsheetApp.getUi().showModalDialog(htmlOutput, 'Inactive Names Report');
    
  } else {
    SpreadsheetApp.getUi().alert("No inactive names found! All names have been active within the last week.");
  }
}