function advanceStudentLesson() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const activeSheet = spreadsheet.getActiveSheet();
  const activeRange = activeSheet.getActiveRange();
  const currentRow = activeRange.getRow();
  
  let studentName = '';
  
  // Determine which sheet we're on and get student name
  if (activeSheet.getName() === 'main') {
    // In main sheet: Column C has names
    studentName = activeSheet.getRange(currentRow, 3).getValue();
  } else if (activeSheet.getName() === 'students') {
    // In students sheet: Column B has names
    studentName = activeSheet.getRange(currentRow, 2).getValue();
  } else {
    SpreadsheetApp.getUi().alert('Please run this script from "main"');
    return;
  }
  
  // Validate student name
  if (!studentName || studentName.toString().trim() === '') {
    SpreadsheetApp.getUi().alert('Please select a row with a student name');
    return;
  }
  
  // Get students sheet data
  const studentsSheet = spreadsheet.getSheetByName('students');
  
  // Find student in students sheet
  const studentsData = studentsSheet.getDataRange().getValues();
  let studentRow = -1;
  let studentFolderId = '';
  let currentLesson = '';
  
  for (let i = 1; i < studentsData.length; i++) { // Start from row 1 (skip header)
    if (studentsData[i][1] && studentsData[i][1].toString().trim() === studentName.toString().trim()) { // Column B (index 1)
      studentRow = i + 1; // Convert to sheet row number
      studentFolderId = studentsData[i][3]; // Column D (index 3)
      currentLesson = studentsData[i][4]; // Column E (index 4)
      break;
    }
  }
  
  if (studentRow === -1) {
    SpreadsheetApp.getUi().alert(`Student "${studentName}" not found in students sheet`);
    return;
  }
  
  if (!studentFolderId) {
    SpreadsheetApp.getUi().alert(`No folder ID found for student "${studentName}"`);
    return;
  }
  
  if (!currentLesson) {
    SpreadsheetApp.getUi().alert(`No current lesson found for student "${studentName}"`);
    return;
  }
  
  // Better lesson number parsing with multiple patterns
  let currentLessonNumber = -1;
  const currentLessonStr = currentLesson.toString().trim();
  
// Try patterns
const patterns = [
  /שיעור\s*(\d+)/,       // שיעור 5
  /^(\d+)$/,             // plain number
];
  
  let lessonMatch = null;
  for (const pattern of patterns) {
    lessonMatch = currentLessonStr.match(pattern);
    if (lessonMatch) {
      currentLessonNumber = parseInt(lessonMatch[1]);
      break;
    }
  }
  
// allow zero as valid; only reject negative numbers / NaN
if (lessonMatch === null || isNaN(currentLessonNumber) || currentLessonNumber < 0) {
  SpreadsheetApp.getUi().alert(
    `Cannot parse lesson number from "${currentLesson}".\n` +
    `Expected "שיעור X" or a number (X can be 0 or higher).\n` +
    `Normalized value: "${currentLessonStr}"`
  );
  return;
}
  
  const nextLessonNumber = currentLessonNumber + 1;
  const nextLessonPrefix = `שיעור ${nextLessonNumber}`;
  
  // Confirm with user before proceeding
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    'Confirm Lesson Advancement',
    `Advance "${studentName}" from "${currentLesson}" to "${nextLessonPrefix}"?\n\nThis will copy the next lesson folder to their drive.`,
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    // Access master lessons folder
    const masterFolderId = '1YDYp0sd-dfqNz8iotcHzqGNRZdgc3JEZ';
    const masterFolder = DriveApp.getFolderById(masterFolderId);
    
    // Find the next lesson folder
    const masterFolders = masterFolder.getFolders();
    let nextLessonFolder = null;
    
    while (masterFolders.hasNext()) {
      const folder = masterFolders.next();
      const folderName = folder.getName();
      
      // FIXED: More flexible folder matching
      if (folderName.includes(`שיעור ${nextLessonNumber}`) || 
          folderName.includes(`שיעור${nextLessonNumber}`) ||
          folderName.startsWith(`${nextLessonNumber} `) ||
          folderName === nextLessonNumber.toString()) {
        nextLessonFolder = folder;
        break;
      }
    }
    
    if (!nextLessonFolder) {
      ui.alert(`Next lesson folder for lesson ${nextLessonNumber} not found in master folder`);
      return;
    }
    
    // Access student's folder
    const studentFolder = DriveApp.getFolderById(studentFolderId);
    
    // Copy the lesson folder (this might take a while for large folders)
    ui.alert('Copying lesson folder... This may take a few moments for large folders. Click OK to start.');
    
    const copiedFolder = copyFolderRecursively(nextLessonFolder, studentFolder);
    
    // FIXED: Use consistent lesson format instead of full folder name
    const newLessonStatus = `שיעור ${nextLessonNumber}`;
    
    // Update students sheet
    studentsSheet.getRange(studentRow, 5).setValue(newLessonStatus); // Column E
    
    // Update main sheet if applicable
    const mainSheet = spreadsheet.getSheetByName('main');
    if (mainSheet) {
      const mainData = mainSheet.getDataRange().getValues();
      for (let i = 1; i < mainData.length; i++) {
        if (mainData[i][2] && mainData[i][2].toString().trim() === studentName.toString().trim()) { // Column C
          mainSheet.getRange(i + 1, 2).setValue(newLessonStatus); // Column B
          break;
        }
      }
    }
    
    ui.alert(
      'Success!', 
      `Student "${studentName}" advanced to "${newLessonStatus}"\n\nFolder "${copiedFolder.getName()}" copied to student's drive.`,
      ui.ButtonSet.OK
    );
    
  } catch (error) {
    ui.alert('Error', `An error occurred: ${error.toString()}`, ui.ButtonSet.OK);
    console.error('Error in advanceStudentLesson:', error);
    
    // Additional error logging for debugging
    console.error('Debug info:', {
      studentName: studentName,
      currentLesson: currentLesson,
      currentLessonNumber: currentLessonNumber,
      nextLessonNumber: nextLessonNumber
    });
  }
}

function copyFolderRecursively(sourceFolder, destinationFolder) {
  // Create new folder in destination
  const newFolder = destinationFolder.createFolder(sourceFolder.getName());
  
  // Copy all files
  const files = sourceFolder.getFiles();
  while (files.hasNext()) {
    const file = files.next();
    file.makeCopy(file.getName(), newFolder);
  }
  
  // Copy all subfolders recursively
  const subFolders = sourceFolder.getFolders();
  while (subFolders.hasNext()) {
    const subFolder = subFolders.next();
    copyFolderRecursively(subFolder, newFolder);
  }
  
  return newFolder;
}

// BONUS: Helper function to clean up lesson data if needed
function cleanupLessonData() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const studentsSheet = spreadsheet.getSheetByName('students');
  
  if (!studentsSheet) {
    SpreadsheetApp.getUi().alert('Students sheet not found');
    return;
  }
  
  const data = studentsSheet.getDataRange().getValues();
  let changesMade = 0;
  let invalidEntries = [];
  
  for (let i = 1; i < data.length; i++) { // Skip header row
    const studentName = data[i][1]; // Column B
    const currentLesson = data[i][4]; // Column E
    
    if (currentLesson) {
      const lessonStr = currentLesson.toString().trim();
      
      // Extract lesson number
      const numberMatch = lessonStr.match(/שיעור\s*(-?\d+)/);
      if (numberMatch) {
        const lessonNumber = parseInt(numberMatch[1]);
        
        if (lessonNumber < 0) {
          invalidEntries.push(`${studentName}: "${lessonStr}" (negative lesson number)`);
        } else if (lessonNumber === 0) {
          invalidEntries.push(`${studentName}: "${lessonStr}" (zero lesson number)`);
        } else {
          const cleanFormat = `שיעור ${lessonNumber}`;
          
          if (lessonStr !== cleanFormat) {
            studentsSheet.getRange(i + 1, 5).setValue(cleanFormat);
            changesMade++;
          }
        }
      } else {
        invalidEntries.push(`${studentName}: "${lessonStr}" (cannot parse lesson number)`);
      }
    }
  }
  
  let message = '';
  if (changesMade > 0) {
    message += `Cleaned up ${changesMade} lesson entries.\n`;
  }
  
  if (invalidEntries.length > 0) {
    message += `\nFound ${invalidEntries.length} entries that need manual fixing:\n`;
    message += invalidEntries.slice(0, 10).join('\n'); // Show first 10
    if (invalidEntries.length > 10) {
      message += `\n... and ${invalidEntries.length - 10} more`;
    }
  }
  
  if (!message) {
    message = 'No cleanup needed - all lesson entries are properly formatted';
  }
  
  SpreadsheetApp.getUi().alert('Cleanup Results', message, SpreadsheetApp.getUi().ButtonSet.OK);
}

// NEW: Helper function to fix specific student's lesson number
function fixStudentLesson() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const activeSheet = spreadsheet.getActiveSheet();
  const activeRange = activeSheet.getActiveRange();
  const currentRow = activeRange.getRow();
  
  let studentName = '';
  
  // Determine which sheet we're on and get student name
  if (activeSheet.getName() === 'main') {
    studentName = activeSheet.getRange(currentRow, 3).getValue();
  } else if (activeSheet.getName() === 'students') {
    studentName = activeSheet.getRange(currentRow, 2).getValue();
  } else {
    SpreadsheetApp.getUi().alert('Please run this script from either "main" or "students" sheet');
    return;
  }
  
  if (!studentName || studentName.toString().trim() === '') {
    SpreadsheetApp.getUi().alert('Please select a row with a student name');
    return;
  }
  
  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt(
    'Fix Student Lesson',
    `Enter the correct lesson number for "${studentName}":\n(Enter just the number, e.g., "1" for שיעור 1)`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (result.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const lessonInput = result.getResponseText().trim();
  const lessonNumber = parseInt(lessonInput);
  
  if (isNaN(lessonNumber) || lessonNumber < 1) {
    ui.alert('Invalid input. Please enter a positive number (1, 2, 3, etc.)');
    return;
  }
  
  const newLessonStatus = `שיעור ${lessonNumber}`;
  
  // Update students sheet
  const studentsSheet = spreadsheet.getSheetByName('students');
  if (studentsSheet) {
    const studentsData = studentsSheet.getDataRange().getValues();
    for (let i = 1; i < studentsData.length; i++) {
      if (studentsData[i][1] && studentsData[i][1].toString().trim() === studentName.toString().trim()) {
        studentsSheet.getRange(i + 1, 5).setValue(newLessonStatus);
        break;
      }
    }
  }
  
  // Update main sheet if applicable
  const mainSheet = spreadsheet.getSheetByName('main');
  if (mainSheet) {
    const mainData = mainSheet.getDataRange().getValues();
    for (let i = 1; i < mainData.length; i++) {
      if (mainData[i][2] && mainData[i][2].toString().trim() === studentName.toString().trim()) {
        mainSheet.getRange(i + 1, 2).setValue(newLessonStatus);
        break;
      }
    }
  }
  
  ui.alert(`Success! Set "${studentName}" to "${newLessonStatus}"`);
}