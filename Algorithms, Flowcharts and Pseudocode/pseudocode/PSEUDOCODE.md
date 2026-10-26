# Pseudocode


## 1. Login and role-based access

```text
FUNCTION Login(username, workerID, password)
    users ← ReadUsers()

    FOR EACH user IN users DO
        IF user.Username = username AND user.Worker_ID = workerID AND
           PasswordMatches(password, user.Password_Hash) THEN
            RETURN user profile
        END IF
    END FOR

    RETURN null
END FUNCTION

IF Login form is submitted THEN
    user ← Login(username, workerID, password)
    IF user is not null THEN
        Save user in session
        currentPage ← "Home"
        pageHistory ← empty list
        allowedPages ← PagesForRole(user.Role)
    ELSE
        Display incorrect-credentials error
    END IF
END IF
```

## 2. Administrator creates a worker account

```text
FUNCTION CreateAccount(workerID, username, password, fullName, title, role)
    IF any required field is empty THEN
        RETURN false, "Complete every required account field"
    END IF

    IF length(password) < 8 THEN
        RETURN false, "Password must contain at least 8 characters"
    END IF

    IF workerID is not in workers.csv THEN
        RETURN false, "Worker ID is not in worker safety data"
    END IF

    users ← ReadUsers()
    IF workerID already exists in users OR username already exists in users THEN
        RETURN false, "Account already exists"
    END IF

    passwordHash ← PasswordHash(password)
    Add account record to users
    WriteUsers(users)
    RETURN true, "Account created"
END FUNCTION
```

## 3. Change password

```text
FUNCTION UpdatePassword(workerID, currentPassword, newPassword)
    IF length(newPassword) < 8 THEN
        RETURN false, "New password is too short"
    END IF

    users ← ReadUsers()
    FOR EACH user IN users DO
        IF user.Worker_ID = workerID THEN
            IF PasswordMatches(currentPassword, user.Password_Hash) = false THEN
                RETURN false, "Current password is incorrect"
            END IF

            user.Password_Hash ← PasswordHash(newPassword)
            WriteUsers(users)
            RETURN true, "Password updated successfully"
        END IF
    END FOR

    RETURN false, "Worker account not found"
END FUNCTION
```

## 4. Upload data

```text
FUNCTION ImportData(uploadedFile, currentData, fileName)
    IF uploadedFile extension is ".csv" THEN
        uploadedData ← ReadCSV(uploadedFile)
    ELSE
        uploadedData ← ReadExcel(uploadedFile)
    END IF

    missingColumns ← columns in currentData that are not in uploadedData
    IF missingColumns is not empty THEN
        Display missingColumns
        STOP
    END IF

    Display row count of uploadedData
    IF user confirms replacement THEN
        Save uploadedData using currentData column order to fileName
        Refresh application
    END IF
END FUNCTION
```

## 5. Global search

```text
FUNCTION SearchSystem(query, workers, incidents, equipment, maintenance, alerts)
    IF Trim(query) is empty THEN
        RETURN
    END IF

    FOR EACH dataSet IN [workers, incidents, equipment, maintenance, alerts] DO
        Convert every column to text
        Select rows where any column contains query, ignoring case
        IF selected rows are not empty THEN
            Display data-set name, count and selected rows
            resultsFound ← true
        END IF
    END FOR

    IF resultsFound = false THEN
        Display "No matching records were found"
    END IF
END FUNCTION
```

## 6. Save worker safety observation

```text
IF SaveWorkerRecord is selected THEN
    IF workerID AND department AND jobRole are provided THEN
        score, level ← WorkerRisk(PPE, training, fatigue, observations,
                                  nearMisses, previousIncidents)
        newRecord ← form values plus level
        workers ← Append(workers, newRecord)
        SaveData(workers, "workers.csv")
        Display score and level
    ELSE
        Display required-fields warning
    END IF
END IF
```

## 7. Save incident

```text
IF SaveIncident is selected THEN
    required ← [incidentID, location, department, incidentType, cause, action]

    IF every item in required is completed THEN
        newIncident ← values from incident form
        incidents ← Append(incidents, newIncident)
        SaveData(incidents, "incidents.csv")
        Display successful-save message
    ELSE
        Display complete-all-text-fields warning
    END IF
END IF
```

## 8. Equipment condition monitoring

```text
FUNCTION EquipmentStatus(temperature, vibration)
    IF temperature > 100 OR vibration > 8 THEN
        RETURN "CRITICAL", "Inspection required"
    ELSE IF temperature ≥ 80 OR vibration ≥ 5 THEN
        RETURN "WARNING", "Approaching critical threshold"
    ELSE
        RETURN "NORMAL", "Within monitoring limits"
    END IF
END FUNCTION

selectedMachine ← machine selected by user
status, message ← EquipmentStatus(selectedMachine.temperature,
                                  selectedMachine.vibration)
Display status, message and temperature-vibration chart
```

## 9. Maintenance monitoring

```text
FOR EACH equipment item IN equipmentSummary DO
    relatedRecords ← maintenance records for equipment item
    alertsCount ← Sum(relatedRecords.Alert_Count)

    IF any related record is overdue OR next due date is before today THEN
        maintenanceStatus ← "Overdue"
    ELSE IF any related record is under maintenance THEN
        maintenanceStatus ← "Under Maintenance"
    ELSE IF any related record is scheduled THEN
        maintenanceStatus ← "Due"
    ELSE
        maintenanceStatus ← "Not Due"
    END IF
END FOR

Display groups for Due, Overdue, Under Maintenance,
Downtime > 12 hours, Alert Count ≥ 4 and Availability < 85%
```

## 10. Risk assessment

```text
FUNCTION AssessRisk(likelihood, consequence)
    score ← likelihood × consequence

    IF score ≤ 4 THEN
        level ← "Low"
    ELSE IF score ≤ 9 THEN
        level ← "Medium"
    ELSE IF score ≤ 16 THEN
        level ← "High"
    ELSE
        level ← "Critical"
    END IF

    RETURN score, level
END FUNCTION
```

## 11. Dashboard, alerts and navigation

```text
workers ← LoadData("workers.csv")
incidents ← LoadData("incidents.csv")
equipment ← LoadData("equipment.csv")
maintenance ← LoadData("maintenance.csv")

equipmentSummary ← BuildEquipmentSummary(equipment, maintenance)
alerts ← BuildAlerts(workers, incidents, equipmentSummary, maintenance)
activeAlertCount ← Count(alerts)

availablePages ← ["Home"] + PagesForRole(currentUser.role)
IF currentPage is not in availablePages THEN
    currentPage ← "Home"
END IF

IF SignOut is selected THEN
    Remove session user, currentPage and pageHistory
    Return to login page
END IF

Display selected page and its permitted data
```
