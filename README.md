# 📚 Study Tracker - Advanced Learning Management System

**Multi-User Cloud-Based Study Session Management Application**

## Overview

Study Tracker is a professional-grade learning management system designed for students, teachers, and educational administrators. It provides:

✅ **User Authentication** - Secure login system with role-based access  
✅ **Multi-User Support** - Multiple clients per admin account  
✅ **Study Session Tracking** - Detailed tracking of study hours by subject  
✅ **Admin Dashboard** - Comprehensive reporting and client management  
✅ **Analytics** - Visual reports of study progress and time allocation  
✅ **Client Management** - Admins can manage and monitor multiple student accounts  
✅ **Data Persistence** - SQLite database for local and cloud-ready data storage  

## Features

### For Students (Client Users)
- 📊 **Dashboard** - Quick overview of today's study sessions
- ✏️ **Study Sessions** - Log study activities with subject, topic, and duration
- 📈 **Analytics** - Visual charts showing study time by subject
- 🎯 **Goal Tracking** - Set and monitor learning objectives
- 💾 **Data History** - Access all past study sessions

### For Teachers/Admins
- 👥 **Client Management** - Assign and manage student accounts
- 📋 **Reports** - View all study sessions from assigned clients
- 📊 **Analytics** - Track student progress across classes
- ⚙️ **User Management** - Create and manage user accounts
- 🔍 **Performance Insights** - Identify study patterns and trends

## System Requirements

- **OS**: Windows 10+, macOS 10.14+, Linux
- **Python**: 3.9 or higher
- **RAM**: 512 MB minimum
- **Storage**: 100 MB for application and database

## Installation

### Step 1: Install Python
Download Python 3.9+ from [python.org](https://www.python.org)

### Step 2: Extract Study Tracker
Extract the Study Tracker folder to your desired location

### Step 3: Install Dependencies
```bash
# Windows
pip install -r requirements.txt

# macOS/Linux
pip3 install -r requirements.txt
```

## Getting Started

### Launch the Application

**Windows:**
```bash
run_app.bat
```

**macOS/Linux:**
```bash
bash run_app.sh
```

**Direct Python:**
```bash
python study_tracker.py
```

### First Time Setup

1. **Login Screen**
   - Default Admin: `admin` / `admin123`
   - New Users: Click "New User" to create account

2. **For Students**
   - Create a new account as a client
   - Wait for admin assignment
   - Start logging study sessions

3. **For Teachers/Admins**
   - Login with admin account
   - Go to "Clients" tab to assign students
   - View reports in "Reports" tab

## User Guide

### Creating Study Sessions (Students)

1. Go to **Dashboard** tab
2. Select subject from dropdown (Mathematics, Science, English, etc.)
3. Enter topic (optional)
4. Click **Start** button
5. Study as usual
6. End session when done

### Viewing Study History (Students)

1. Go to **Sessions** tab
2. View all study sessions with date and duration
3. Filter by date range or subject

### Analyzing Study Patterns (Students)

1. Go to **Analytics** tab
2. View bar chart of study time by subject
3. Identify areas needing more focus

### Managing Clients (Admins)

1. Go to **Clients** tab
2. Enter student username
3. Click **Assign** to link student to your account
4. View all assigned students and their statistics

### Generating Reports (Admins)

1. Go to **Reports** tab
2. View all study sessions from all assigned clients
3. Export data for further analysis

### Creating User Accounts (Admins)

1. Go to **Users** tab
2. Enter username, password, and role
3. Click **Create User**
4. Share credentials with student

## Database Structure

### Users Table
- User ID, Username, Password (hashed), Role, Created Date, Last Login

### Study Sessions Table
- Session ID, User ID, Subject, Topic, Start Time, End Time, Duration, Notes

### Client Assignments Table
- Assignment ID, Admin ID, Client ID, Assignment Date

### Study Goals Table
- Goal ID, User ID, Goal Text, Target Hours, Start/End Date, Completion Status

## Security

- ✅ **Password Hashing** - All passwords hashed with SHA-256
- ✅ **Role-Based Access** - Students and admins have different permissions
- ✅ **Secure Login** - Credentials verified at each login
- ✅ **Local Database** - All data stored securely on your device

## Keyboard Shortcuts

- `Enter` - Start study session
- `Space` - Pause/Resume session (if implementing timer)
- `Esc` - Cancel session

## Troubleshooting

### Python Not Found
**Solution**: Ensure Python is installed and added to PATH
```bash
python --version
```

### PIL Module Not Found
**Solution**: Install Pillow
```bash
pip install pillow
```

### Matplotlib Not Found
**Solution**: Install Matplotlib
```bash
pip install matplotlib
```

### Database Locked Error
**Solution**: Close all instances of Study Tracker and try again

### Login Failed
**Solution**: Verify username and password, reset to `admin`/`admin123` if needed

## Data Management

### Backing Up Data

The database file `study_tracker.db` contains all user and session data.

**To backup:**
1. Locate `study_tracker.db` in application folder
2. Copy to safe location
3. Can be restored by placing in application folder

### Exporting Reports

From Reports tab, you can view all data. To export:
1. Select data in table
2. Copy to clipboard
3. Paste in Excel/spreadsheet

## Performance Tips

- ✅ Keep database backed up regularly
- ✅ Archive old sessions after semester ends
- ✅ Run on systems with 2GB+ RAM for smooth performance
- ✅ Clear browser cache if using web version

## Developer Info

### Project Structure
```
study_tracker/
├── study_tracker.py          # Main application
├── study_tracker.db          # SQLite database (auto-created)
├── study_tracker_logo.ico    # App icon
├── requirements.txt          # Python dependencies
├── run_app.bat              # Windows launcher
├── run_app.sh               # Linux/Mac launcher
└── README.md                # This file
```

### Key Classes

- `DatabaseManager` - Handles all database operations
- `StudyTracker` - Core tracking logic
- `StudyTrackerApp(tk.Tk)` - Main GUI application

## Future Enhancements

- ☐ Cloud sync with Firebase/AWS
- ☐ Mobile app for iOS/Android
- ☐ Email notifications
- ☐ Video study session recordings
- ☐ AI-powered study recommendations
- ☐ Gamification and achievement badges
- ☐ Integration with calendar apps

## Support

For issues or feature requests, contact the development team.

## License

Study Tracker © 2026. All rights reserved.

---

**Happy Studying! 📚✨**
