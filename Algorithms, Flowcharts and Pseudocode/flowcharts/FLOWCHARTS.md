# Flowcharts

These diagrams use **Mermaid**. GitHub renders them automatically in Markdown files.

## F1. Login and role-based access control

```mermaid
flowchart TD
    A([Start]) --> B[Enter username, Worker ID and password]
    B --> C[Read users.csv]
    C --> D{Username, Worker ID and password hash match?}
    D -- No --> E[Show login error]
    E --> B
    D -- Yes --> F[Store user profile in session]
    F --> G[Get pages allowed for user role]
    G --> H[Open Home page]
    H --> I([End])
```

## F2. Administrator account creation

```mermaid
flowchart TD
    A([Administrator opens account form]) --> B[Enter worker details and temporary password]
    B --> C{All fields completed and password at least 8 characters?}
    C -- No --> D[Show validation message]
    D --> B
    C -- Yes --> E{Worker ID exists in workers.csv?}
    E -- No --> F[Show invalid Worker ID message]
    F --> B
    E -- Yes --> G{Worker ID or username already used?}
    G -- Yes --> H[Show duplicate account message]
    H --> B
    G -- No --> I[Hash password and save account to users.csv]
    I --> J[Show account created message]
    J --> K([End])
```

## F3. Data upload and validation

```mermaid
flowchart TD
    A([Start upload]) --> B[Select CSV or Excel file]
    B --> C[Read uploaded table]
    C --> D[Compare uploaded columns to current table]
    D --> E{Any required columns missing?}
    E -- Yes --> F[Display missing columns]
    F --> B
    E -- No --> G[Display number of rows found]
    G --> H{User confirms replacement?}
    H -- No --> I([Keep current data])
    H -- Yes --> J[Save accepted columns to project CSV]
    J --> K[Refresh page]
    K --> L([End])
```

## F4. Change password

```mermaid
flowchart TD
    A([Start]) --> B[Enter current and new password]
    B --> C{New password has at least 8 characters?}
    C -- No --> D[Show password-length error]
    D --> B
    C -- Yes --> E[Read users.csv and find signed-in Worker ID]
    E --> F{Current password hash matches?}
    F -- No --> G[Show current-password error]
    G --> B
    F -- Yes --> H[Create new salted password hash]
    H --> I[Update only this user record in users.csv]
    I --> J[Show password updated message]
    J --> K([End])
```

## F5. Global search

```mermaid
flowchart TD
    A([Start]) --> B[Enter search text]
    B --> C{Search text blank?}
    C -- Yes --> D([End])
    C -- No --> E[Search worker, incident, equipment, maintenance and alert tables]
    E --> F{Matches found in a table?}
    F -- Yes --> G[Display matching rows and count]
    G --> H{More tables to search?}
    H -- Yes --> E
    H -- No --> D
    F -- No --> H
```

## F6. Worker safety observation

```mermaid
flowchart TD
    A([Start]) --> B[Enter worker safety observation]
    B --> C{Worker ID, department and job role entered?}
    C -- No --> D[Display required-fields warning]
    D --> B
    C -- Yes --> E[Calculate worker risk score and level]
    E --> F[Create worker safety record]
    F --> G[Append record to workers table]
    G --> H[Save workers.csv]
    H --> I[Display score and level]
    I --> J([End])
```

## F7. Incident record and filter

```mermaid
flowchart TD
    A([Open incident page]) --> B{Severity filter selected?}
    B -- Yes --> C[Show matching incidents]
    B -- No --> D[Show all incidents]
    C --> E[Create incidents by department chart]
    D --> E
    E --> F{User submits a new incident?}
    F -- No --> G([End])
    F -- Yes --> H{Required fields complete?}
    H -- No --> I[Show warning]
    I --> F
    H -- Yes --> J[Append incident and save incidents.csv]
    J --> K[Show success message]
    K --> G
```

## F8. Equipment condition monitoring

```mermaid
flowchart TD
    A([Start]) --> B[Build equipment summary]
    B --> C[User selects machine]
    C --> D[Read temperature and vibration]
    D --> E{Temperature above 100 C OR vibration above 8 mm/s?}
    E -- Yes --> F[Set CRITICAL and require inspection]
    E -- No --> G{Temperature at least 80 C OR vibration at least 5 mm/s?}
    G -- Yes --> H[Set WARNING]
    G -- No --> I[Set NORMAL]
    F --> J[Display message and scatter chart]
    H --> J
    I --> J
    J --> K([End])
```

## F9. Maintenance monitoring

```mermaid
flowchart TD
    A([Start]) --> B[Create record for each equipment item]
    B --> C[Find its maintenance records]
    C --> D[Add alert counts]
    D --> E{Overdue status or due date passed?}
    E -- Yes --> F[Set status to Overdue]
    E -- No --> G{Under Maintenance status present?}
    G -- Yes --> H[Set status to Under Maintenance]
    G -- No --> I{Scheduled status present?}
    I -- Yes --> J[Set status to Due]
    I -- No --> K[Set status to Not Due]
    F --> L[Group by priority conditions]
    H --> L
    J --> L
    K --> L
    L --> M[Display maintenance groups]
    M --> N([End])
```

## F10. Risk assessment

```mermaid
flowchart TD
    A([Start]) --> B[Select likelihood 1 to 5]
    B --> C[Select consequence 1 to 5]
    C --> D[Calculate score = likelihood x consequence]
    D --> E{Score category?}
    E -- 1 to 4 --> F[Low: continue monitoring]
    E -- 5 to 9 --> G[Medium: review and apply controls]
    E -- 10 to 16 --> H[High: controls required before work]
    E -- 17 to 25 --> I[Critical: stop and escalate]
    F --> J([End])
    G --> J
    H --> J
    I --> J
```

## F11. Alert generation and dashboard

```mermaid
flowchart TD
    A([Application opens]) --> B[Load worker, incident, equipment and maintenance CSV files]
    B --> C[Build equipment summary]
    C --> D[Apply rule-based alert conditions]
    D --> E[Count active and critical alerts]
    E --> F[Calculate dashboard indicators]
    F --> G[Create incident and equipment charts]
    G --> H[Show dashboard and alert count]
    H --> I([End])
```

## F12. Navigation and sign out

```mermaid
flowchart TD
    A([Signed-in user]) --> B[Create Home plus role-permitted page list]
    B --> C{Selected page permitted?}
    C -- No --> D[Set page to Home]
    C -- Yes --> E[Open selected page]
    D --> E
    E --> F{Navigation action?}
    F -- Open workspace --> G[Save current page in history and open workspace]
    F -- Back --> H[Open latest page in history]
    F -- Home --> I[Open Home]
    F -- Sign out --> J[Clear user session and page history]
    G --> E
    H --> E
    I --> E
    J --> K([Show login page])
```
