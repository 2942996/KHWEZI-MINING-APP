# Algorithms


## 1. Login and role-based access control

1. Start
2. Receive the username, Worker ID and password from the login form.
3. Read the saved user accounts from `users.csv`.
4. Find a record with a matching username and Worker ID.
5. Hash the entered password using the saved salt and compare it with the saved password hash.
6. If all three credentials match, store the user profile in the session.
7. Use the user role to get the permitted pages from `ROLE_PAGES`.
8. Open the Home page and display the user's profile and available workspaces.
9. Otherwise, display an incorrect-credentials error.
10. End

## 2. Administrator account creation

1. Start
2. Confirm that the signed-in user is an Administrator.
3. Check that all required fields have been entered.
4. Check that the password contains at least eight characters.
5. Search `workers.csv` to confirm that the Worker ID already exists in the worker database.
6. Read `users.csv` and check that the Worker ID and username are not already in use.
7. Generate a salt and password hash.
8. Add the new account record to `users.csv`.
9. Display a success message; otherwise show the relevant validation message.
10. End

## 3. Password update

1. Start
2. Check that the new password has at least eight characters.
3. Read the user accounts from `users.csv`.
4. Find the account with the signed-in user's Worker ID.
5. Verify the entered current password against the saved password hash.
6. If it matches, create a new salted hash for the new password.
7. Replace only that account's password hash and save `users.csv`.
8. Confirm that the password was updated; otherwise display an error.
9. End

## 4.Data upload and validation

1. Start
2. Receive the uploaded file.
3. Read it as CSV when its extension is `.csv`; otherwise read it as an Excel file.
4. Compare its column names with the current project data table.
5. If one or more required columns are missing, list the missing columns and stop.
6. If all columns exist, show the number of rows found.
7. When the user confirms replacement, keep only the required columns in the correct order.
8. Save the data to the matching project CSV file.
9. Refresh the page so that the new data is used
10. End

## 5. Global search

1. Start
2. Remove unnecessary spaces from the search text.
3. If no text was entered, end the search.
4. Search Worker Safety, Safety Incidents, Equipment, Maintenance and Alerts tables.
5. Convert each column to text and compare it with the search text without considering letter case.
6. Collect rows where at least one column matches.
7. Display each non-empty group with its number of matching records.
8. If no group contains a match, display a no-results message.
9. End

## 6. Worker safety record and risk classification

1. Start
2. Receive the Worker ID, department, job role, shift, PPE, training, fatigue, observations, near misses and previous incidents.
3. Check that Worker ID, department and job role were entered.
4. Apply the worker-risk rules to calculate a score and level.
5. Create a new worker safety record including the calculated risk level.
6. Add the record to the current worker table.
7. Save the revised table to `workers.csv`.
8. Display the score and risk level.
9. End

## 7. Incident recording and filtering

1. Start
2. If the user selects one or more severities, keep only incidents with those severities; otherwise keep all incidents.
3. Display the selected incident records and calculate incident counts by department.
4. When an incident is submitted, check that Incident ID, location, department, incident type, cause and corrective action are completed.
5. If any required item is missing, display a warning.
6. Otherwise create a new incident record from the form values.
7. Append the new record to the incident table.
8. Save the revised table to `incidents.csv` and confirm the save.
9. End

## 8. Equipment condition monitoring

1. Start
2. Build an equipment summary from the equipment and maintenance data.
3. Allow the user to select one machine.
4. Read the machine's temperature and vibration readings.
5. If temperature is above 100 °C or vibration is above 8 mm/s, classify the machine as **Critical**.
6. Otherwise, if temperature is from 80 to 100 °C or vibration is from 5 to 8 mm/s, classify it as **Warning**.
7. Otherwise classify it as **Normal**.
8. Display the result and show a temperature-versus-vibration scatter plot.
9. State that these are educational prototype thresholds only.
10. End

## 9. Maintenance priority monitoring

1. Start
2. Set the high-downtime threshold to 12 hours and low-availability threshold to 85%.
3. Create a maintenance summary record for each equipment item.
4. Find all maintenance records belonging to that item.
5. Add the alert counts for the item.
6. Mark the item as Overdue when a record is overdue or its next due date has passed.
7. Otherwise mark it Under Maintenance when applicable, or Due when it has a scheduled record.
8. Group equipment as Due, Overdue, Under Maintenance, Excessive Downtime, Repeated Alerts, and Low Availability.
9. Display every group with its number of items.
10. End

## 10. Risk assessment

1. Start
2. Receive the likelihood and consequence values.
3. Calculate `risk score = likelihood × consequence`.
4. Classify scores 1–4 as Low, 5–9 as Medium, 10–16 as High, and 17–25 as Critical.
5. Display the score.
6. Show a monitoring message for Low, a review message for Medium, and a stop-and-escalate message for High or Critical.
7. End

## 11. Alert generation and dashboard summary

1. Start
2. Load the current CSV tables.
3. Build the equipment summary.
4. Apply the visible safety, incident, equipment and maintenance rules to create alerts.
5. Count the active alerts and critical alerts.
6. Calculate dashboard indicators: workers, open incidents, workers at high risk, critical equipment and critical alerts.
7. Create incident and equipment charts.
8. Display the dashboard and show the active-alert count in the workspace bar.
9. End

## 12. Navigation and sign out

1. Start
2. Create the list `Home + pages_for_role(user role)`.
3. If the selected page is not in this list, set the page to Home.
4. When a workspace is opened, place the current page in page history and open the new page.
5. When Back is selected, remove the latest page from page history and open it.
6. When Home is selected, store the current page and open Home.
7. When Sign out is selected, remove the session user and navigation data.
8. Return to the login page.
9. End
