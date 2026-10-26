# Algorithms

These algorithms describe the key functions implemented in the Khwezi Mining application.

## A1. Login and role-based access control

**Input:** Username, Worker ID and password.  
**Output:** Access to the permitted pages, or an error message.

1. Receive the username, Worker ID and password from the login form.
2. Read the saved user accounts from `users.csv`.
3. Find a record with a matching username and Worker ID.
4. Hash the entered password using the saved salt and compare it with the saved password hash.
5. If all three credentials match, store the user profile in the session.
6. Use the user role to get the permitted pages from `ROLE_PAGES`.
7. Open the Home page and display the user's profile and available workspaces.
8. Otherwise, display an incorrect-credentials error.

## A2. Administrator account creation

**Input:** Worker ID, username, full name, title, role and temporary password.  
**Output:** New secure user account or validation feedback.

1. Confirm that the signed-in user is an Administrator.
2. Check that all required fields have been entered.
3. Check that the password contains at least eight characters.
4. Search `workers.csv` to confirm that the Worker ID already exists in the worker database.
5. Read `users.csv` and check that the Worker ID and username are not already in use.
6. Generate a salt and password hash.
7. Add the new account record to `users.csv`.
8. Display a success message; otherwise show the relevant validation message.

## A3. Password update

**Input:** Current password and new password.  
**Output:** Updated password hash or an error message.

1. Check that the new password has at least eight characters.
2. Read the user accounts from `users.csv`.
3. Find the account with the signed-in user's Worker ID.
4. Verify the entered current password against the saved password hash.
5. If it matches, create a new salted hash for the new password.
6. Replace only that account's password hash and save `users.csv`.
7. Confirm that the password was updated; otherwise display an error.

## A4. Data upload and validation

**Input:** CSV, XLSX or XLS file for a selected data area.  
**Output:** A safely replaced project CSV file or a validation error.

1. Receive the uploaded file.
2. Read it as CSV when its extension is `.csv`; otherwise read it as an Excel file.
3. Compare its column names with the current project data table.
4. If one or more required columns are missing, list the missing columns and stop.
5. If all columns exist, show the number of rows found.
6. When the user confirms replacement, keep only the required columns in the correct order.
7. Save the data to the matching project CSV file.
8. Refresh the page so that the new data is used.

## A5. Global search

**Input:** Search text.  
**Output:** Matching records grouped by data area.

1. Remove unnecessary spaces from the search text.
2. If no text was entered, end the search.
3. Search Worker Safety, Safety Incidents, Equipment, Maintenance and Alerts tables.
4. Convert each column to text and compare it with the search text without considering letter case.
5. Collect rows where at least one column matches.
6. Display each non-empty group with its number of matching records.
7. If no group contains a match, display a no-results message.

## A6. Worker safety record and risk classification

**Input:** Worker safety observation fields.  
**Output:** Stored worker record with a rule-based risk level.

1. Receive the Worker ID, department, job role, shift, PPE, training, fatigue, observations, near misses and previous incidents.
2. Check that Worker ID, department and job role were entered.
3. Apply the worker-risk rules to calculate a score and level.
4. Create a new worker safety record including the calculated risk level.
5. Add the record to the current worker table.
6. Save the revised table to `workers.csv`.
7. Display the score and risk level.

## A7. Incident recording and filtering

**Input:** Incident information or severity filter.  
**Output:** Filtered incident view or saved incident record.

1. If the user selects one or more severities, keep only incidents with those severities; otherwise keep all incidents.
2. Display the selected incident records and calculate incident counts by department.
3. When an incident is submitted, check that Incident ID, location, department, incident type, cause and corrective action are completed.
4. If any required item is missing, display a warning.
5. Otherwise create a new incident record from the form values.
6. Append the new record to the incident table.
7. Save the revised table to `incidents.csv` and confirm the save.

## A8. Equipment condition monitoring

**Input:** Equipment temperature and vibration readings.  
**Output:** Normal, Warning or Critical equipment condition.

1. Build an equipment summary from the equipment and maintenance data.
2. Allow the user to select one machine.
3. Read the machine's temperature and vibration readings.
4. If temperature is above 100 °C or vibration is above 8 mm/s, classify the machine as **Critical**.
5. Otherwise, if temperature is from 80 to 100 °C or vibration is from 5 to 8 mm/s, classify it as **Warning**.
6. Otherwise classify it as **Normal**.
7. Display the result and show a temperature-versus-vibration scatter plot.
8. State that these are educational prototype thresholds only.

## A9. Maintenance priority monitoring

**Input:** Maintenance records and equipment summary.  
**Output:** Equipment groups requiring attention.

1. Set the high-downtime threshold to 12 hours and low-availability threshold to 85%.
2. Create a maintenance summary record for each equipment item.
3. Find all maintenance records belonging to that item.
4. Add the alert counts for the item.
5. Mark the item as Overdue when a record is overdue or its next due date has passed.
6. Otherwise mark it Under Maintenance when applicable, or Due when it has a scheduled record.
7. Group equipment as Due, Overdue, Under Maintenance, Excessive Downtime, Repeated Alerts, and Low Availability.
8. Display every group with its number of items.

## A10. Risk assessment

**Input:** Likelihood and consequence values from 1 to 5.  
**Output:** Risk score, category and action message.

1. Receive the likelihood and consequence values.
2. Calculate `risk score = likelihood × consequence`.
3. Classify scores 1–4 as Low, 5–9 as Medium, 10–16 as High, and 17–25 as Critical.
4. Display the score.
5. Show a monitoring message for Low, a review message for Medium, and a stop-and-escalate message for High or Critical.

## A11. Alert generation and dashboard summary

**Input:** Worker, incident, equipment and maintenance data.  
**Output:** Current alerts and dashboard indicators.

1. Load the current CSV tables.
2. Build the equipment summary.
3. Apply the visible safety, incident, equipment and maintenance rules to create alerts.
4. Count the active alerts and critical alerts.
5. Calculate dashboard indicators: workers, open incidents, workers at high risk, critical equipment and critical alerts.
6. Create incident and equipment charts.
7. Display the dashboard and show the active-alert count in the workspace bar.

## A12. Navigation and sign out

**Input:** Selected workspace, Home button, Back button or Sign out button.  
**Output:** Correct page or login screen.

1. Create the list `Home + pages_for_role(user role)`.
2. If the selected page is not in this list, set the page to Home.
3. When a workspace is opened, place the current page in page history and open the new page.
4. When Back is selected, remove the latest page from page history and open it.
5. When Home is selected, store the current page and open Home.
6. When Sign out is selected, remove the session user and navigation data.
7. Return to the login page.
