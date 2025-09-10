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
    SpreadsheetApp.getUi().alert('Please run this script from either "main" or "students" sheet');
    return;
  }
  
  // Validate student name
  if (!studentName || studentName.toString().trim() === '') {
    SpreadsheetApp.getUi().alert('Please select a row with a student name');
    return;
  }
  
  // Get students sheet data
  const studentsSheet = spreadsheet.getSheetByName('students');
  if (!studentsSheet) {
    SpreadsheetApp.getUi().alert('Students sheet not found');
    return;
  }
  
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
  
  // Extract lesson number from current lesson
  const lessonMatch = currentLesson.toString().match(/שיעור\s+(\d+)/);
  if (!lessonMatch) {
    SpreadsheetApp.getUi().alert(`Cannot parse lesson number from "${currentLesson}". Expected format: "שיעור X"`);
    return;
  }
  
  const currentLessonNumber = parseInt(lessonMatch[1]);
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
      if (folder.getName().startsWith(nextLessonPrefix)) {
        nextLessonFolder = folder;
        break;
      }
    }
    
    if (!nextLessonFolder) {
      ui.alert(`Next lesson folder "${nextLessonPrefix}" not found in master folder`);
      return;
    }
    
    // Access student's folder
    const studentFolder = DriveApp.getFolderById(studentFolderId);
    
    // Copy the lesson folder (this might take a while for large folders)
    ui.alert('Copying lesson folder... This may take a few moments for large folders. Click OK to start.');
    
    const copiedFolder = copyFolderRecursively(nextLessonFolder, studentFolder);
    
    // Extract just "שיעור X" from the folder name for status
    const folderName = nextLessonFolder.getName();
    const lessonMatchNew = folderName.match(/שיעור\s+\d+/);
    const newLessonStatus = lessonMatchNew ? lessonMatchNew[0] : folderName;
    
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
