"""
Study Tracker - Multi-User Cloud-Based Study Session Management App
Features: User Login, Client Management, Study Analytics, Admin Dashboard
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime
import threading
import json
import os
import csv
from PIL import Image, ImageDraw, ImageFont, ImageTk
import hashlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import io

class CloudSyncManager:
    """Handle cloud sync operations"""
    
    def __init__(self):
        self.cloud_enabled = False
    
    def sync_to_cloud(self, data):
        """Sync data to cloud"""
        # Cloud sync optional - app works locally without it
        pass
    
    def sync_from_cloud(self):
        """Sync data from cloud"""
        # Cloud sync optional - app works locally without it
        pass


class DatabaseManager:
    """Handle all database operations for multi-user study tracker"""
    
    def __init__(self, db_path='study_tracker.db'):
        self.db_path = db_path
        self.cloud_sync = CloudSyncManager()
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table with role-based access
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'client',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Study sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Client assignments table (for admins managing clients)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(id),
                FOREIGN KEY (client_id) REFERENCES users(id)
            )
        ''')
        
        # Study goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_text TEXT NOT NULL,
                target_hours REAL,
                start_date DATE,
                end_date DATE,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        
        # Create default admin if not exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            self.create_user('admin', self.hash_password('admin123'), role='admin')
        
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password, role='client'):
        """Create new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            hashed_pw = self.hash_password(password) if not password.startswith('sha') else password
            cursor.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                (username, hashed_pw, role)
            )
            conn.commit()
            return True, "User created successfully"
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        finally:
            conn.close()
    
    def verify_login(self, username, password):
        """Verify user credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        hashed_pw = self.hash_password(password)
        
        cursor.execute(
            'SELECT id, role FROM users WHERE username = ? AND password = ?',
            (username, hashed_pw)
        )
        result = cursor.fetchone()
        
        if result:
            user_id, role = result
            cursor.execute(
                'UPDATE users SET last_login = ? WHERE id = ?',
                (datetime.datetime.now(), user_id)
            )
            conn.commit()
        
        conn.close()
        return result
    
    def add_study_session(self, user_id, subject, topic, start_time, end_time, notes=''):
        """Add study session and sync to cloud"""
        duration = int((end_time - start_time).total_seconds() / 60)  # in minutes
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO study_sessions 
               (user_id, subject, topic, start_time, end_time, duration, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, subject, topic, start_time, end_time, duration, notes)
        )
        conn.commit()
        conn.close()
        
        # Sync to cloud
        session_data = {
            'user_id': user_id,
            'subject': subject,
            'topic': topic,
            'start_time': str(start_time),
            'end_time': str(end_time),
            'duration': duration,
            'notes': notes
        }
        self.cloud_sync.sync_to_cloud(session_data)
    
    def get_user_sessions(self, user_id, days=7):
        """Get study sessions for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        date_filter = datetime.datetime.now() - datetime.timedelta(days=days)
        
        cursor.execute(
            '''SELECT id, subject, topic, start_time, end_time, duration, notes 
               FROM study_sessions 
               WHERE user_id = ? AND created_at > ?
               ORDER BY start_time DESC''',
            (user_id, date_filter)
        )
        
        sessions = cursor.fetchall()
        conn.close()
        return sessions
    
    def get_all_clients(self, admin_id):
        """Get all clients managed by admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT DISTINCT u.id, u.username, u.created_at 
               FROM users u
               INNER JOIN client_assignments ca ON u.id = ca.client_id
               WHERE ca.admin_id = ? AND u.role = 'client'
               ORDER BY u.username''',
            (admin_id,)
        )
        
        clients = cursor.fetchall()
        conn.close()
        return clients
    
    def assign_client(self, admin_id, client_username):
        """Assign client to admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE username = ?', (client_username,))
        client = cursor.fetchone()
        
        if not client:
            conn.close()
            return False, "Client not found"
        
        client_id = client[0]
        
        try:
            cursor.execute(
                'INSERT INTO client_assignments (admin_id, client_id) VALUES (?, ?)',
                (admin_id, client_id)
            )
            conn.commit()
            return True, "Client assigned successfully"
        except sqlite3.IntegrityError:
            return False, "Client already assigned"
        finally:
            conn.close()
    
    def get_all_sessions_for_admin(self, admin_id):
        """Get all sessions from all assigned clients"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT u.username, ss.subject, ss.topic, ss.start_time, ss.end_time, ss.duration
               FROM study_sessions ss
               INNER JOIN users u ON ss.user_id = u.id
               INNER JOIN client_assignments ca ON u.id = ca.client_id
               WHERE ca.admin_id = ?
               ORDER BY ss.start_time DESC''',
            (admin_id,)
        )
        
        sessions = cursor.fetchall()
        conn.close()
        return sessions
    
    def get_client_stats(self, client_id, days=30):
        """Get statistics for a client"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        date_filter = datetime.datetime.now() - datetime.timedelta(days=days)
        
        cursor.execute(
            '''SELECT subject, SUM(duration) as total_minutes, COUNT(*) as sessions
               FROM study_sessions
               WHERE user_id = ? AND created_at > ?
               GROUP BY subject
               ORDER BY total_minutes DESC''',
            (client_id, date_filter)
        )
        
        stats = cursor.fetchall()
        conn.close()
        return stats


class StudyTracker:
    """Core study tracking logic"""
    
    def __init__(self, user_id, db_manager):
        self.user_id = user_id
        self.db = db_manager
        self.current_session = None
        self.session_start = None
        self.session_end = None
        self.is_paused = False
        self.pause_start = None
        self.total_pause_duration = 0
    
    def start_study_session(self, subject, topic=''):
        """Start a new study session"""
        self.session_start = datetime.datetime.now()
        self.current_session = {'subject': subject, 'topic': topic}
        self.is_paused = False
        self.total_pause_duration = 0
    
    def end_study_session(self, notes=''):
        """End current study session"""
        if not self.current_session:
            return False
        
        self.session_end = datetime.datetime.now()
        
        self.db.add_study_session(
            self.user_id,
            self.current_session['subject'],
            self.current_session['topic'],
            self.session_start,
            self.session_end,
            notes
        )
        
        self.current_session = None
        return True
    
    def pause_session(self):
        """Pause session"""
        self.is_paused = True
        self.pause_start = datetime.datetime.now()
    
    def resume_session(self):
        """Resume session"""
        if self.pause_start:
            pause_duration = (datetime.datetime.now() - self.pause_start).total_seconds()
            self.total_pause_duration += pause_duration
        self.is_paused = False
    
    def get_elapsed_time(self):
        """Get elapsed time for current session"""
        if not self.session_start:
            return 0
        
        if self.is_paused:
            end_time = self.pause_start
        else:
            end_time = datetime.datetime.now()
        
        elapsed = (end_time - self.session_start).total_seconds() - self.total_pause_duration
        return int(elapsed)


class StudyTrackerApp(tk.Tk):
    """Main GUI application"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Study Tracker - Advanced Learning Management")
        self.geometry("1200x700")
        self.configure(bg='#f0f8ff')
        
        # Initialize database
        self.db = DatabaseManager()
        self.tracker = None
        self.current_user_id = None
        self.current_role = None
        self.current_username = None
        
        # Setup icon
        self.setup_icon()
        
        # Show login screen
        self.show_login_screen()
    
    def setup_icon(self):
        """Setup window icon"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create icon
            icon_path = 'study_tracker_logo.ico'
            if not os.path.exists(icon_path):
                self.create_study_tracker_logo()
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass
    
    def create_study_tracker_logo(self):
        """Create study tracker logo - nm trademark on black"""
        try:
            img = Image.new('RGB', (256, 256), color='#000000')
            draw = ImageDraw.Draw(img)
            
            # Add text
            try:
                font = ImageFont.truetype("segoeui.ttf", 140)
            except:
                font = ImageFont.load_default()
            
            # Draw "nm" in golden color
            bbox = draw.textbbox((0, 0), "nm", font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x_pos = (256 - text_width) // 2
            y_pos = (256 - text_height) // 2 - 10
            
            draw.text((x_pos, y_pos), "nm", fill='#FFD700', font=font)
            
            img.save('study_tracker_logo.png')
            img.save('study_tracker_logo.ico')
        except:
            pass
    
    def clear_frame(self):
        """Clear current frame"""
        for widget in self.winfo_children():
            widget.destroy()
    
    def show_login_screen(self):
        """Display login screen with admin/student selection"""
        self.clear_frame()
        self.geometry("600x500")
        
        main_frame = tk.Frame(self, bg='#f0f8ff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(main_frame, text="Study Tracker", font=("Segoe UI", 32, "bold"), 
                        fg='#FFD700', bg='#f0f8ff')
        title.pack(pady=20)
        
        subtitle = tk.Label(main_frame, text="nm ❤️ - Learning Management System", 
                           font=("Segoe UI", 11), fg='#666', bg='#f0f8ff')
        subtitle.pack(pady=5)
        
        # Role selection
        role_frame = tk.Frame(main_frame, bg='#f0f8ff')
        role_frame.pack(pady=20)
        
        tk.Label(role_frame, text="Select Login Type:", font=("Segoe UI", 12, "bold"), 
                bg='#f0f8ff', fg='#1a1a1a').pack()
        
        button_frame = tk.Frame(role_frame, bg='#f0f8ff')
        button_frame.pack(pady=15)
        
        admin_btn = tk.Button(button_frame, text="👨‍🏫 Admin Login", font=("Segoe UI", 11, "bold"), 
                             bg='#ff6b6b', fg='white', width=20, height=2,
                             command=lambda: self.show_login_form('admin'))
        admin_btn.pack(pady=10)
        
        student_btn = tk.Button(button_frame, text="👤 Student Login", font=("Segoe UI", 11, "bold"), 
                               bg='#4ecdc4', fg='white', width=20, height=2,
                               command=lambda: self.show_login_form('student'))
        student_btn.pack(pady=10)
        
        # Info text
        info = tk.Label(main_frame, text="👨‍🏫 Admin: Manage students and view reports\n👤 Student: Track your study sessions", 
                       font=("Segoe UI", 9), bg='#f0f8ff', fg='#666', justify=tk.LEFT)
        info.pack(pady=20)
    
    def show_login_form(self, role):
        """Display login form for admin or student"""
        self.clear_frame()
        self.geometry("500x400")
        
        main_frame = tk.Frame(self, bg='#f0f8ff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_text = "👨‍🏫 Admin Login" if role == 'admin' else "👤 Student Login"
        title = tk.Label(main_frame, text=title_text, font=("Segoe UI", 24, "bold"), 
                        fg='#ff6b6b' if role == 'admin' else '#4ecdc4', bg='#f0f8ff')
        title.pack(pady=20)
        
        # Login frame
        login_frame = tk.Frame(main_frame, bg='white', relief='raised', bd=2)
        login_frame.pack(pady=20, fill=tk.BOTH, expand=True, padx=20)
        
        # Username
        tk.Label(login_frame, text="Username:", font=("Segoe UI", 11), bg='white').pack(anchor='w', padx=15, pady=(20, 5))
        username_entry = tk.Entry(login_frame, font=("Segoe UI", 11), width=30)
        username_entry.pack(padx=15, pady=(0, 15))
        
        # Password
        tk.Label(login_frame, text="Password:", font=("Segoe UI", 11), bg='white').pack(anchor='w', padx=15, pady=(5, 5))
        password_entry = tk.Entry(login_frame, font=("Segoe UI", 11), width=30, show='*')
        password_entry.pack(padx=15, pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(login_frame, bg='white')
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        def login():
            username = username_entry.get()
            password = password_entry.get()
            
            if not username or not password:
                messagebox.showerror("Error", "Please enter both username and password")
                return
            
            result = self.db.verify_login(username, password)
            if result:
                user_id, user_role = result
                if (role == 'admin' and user_role == 'admin') or (role == 'student' and user_role == 'client'):
                    self.current_user_id = user_id
                    self.current_role = user_role
                    self.current_username = username
                    self.tracker = StudyTracker(user_id, self.db)
                    
                    if user_role == 'admin':
                        self.show_admin_dashboard()
                    else:
                        self.show_client_dashboard()
                else:
                    messagebox.showerror("Error", f"This account is not an {role} account")
            else:
                messagebox.showerror("Error", "Invalid username or password")
        
        login_btn = tk.Button(button_frame, text="Login", font=("Segoe UI", 11, "bold"), 
                             bg='#ff6b6b' if role == 'admin' else '#4ecdc4', fg='white', 
                             command=login, width=15)
        login_btn.pack(side=tk.LEFT, padx=5)
        
        signup_btn = tk.Button(button_frame, text="New Account", font=("Segoe UI", 11), 
                              bg='#a8e6cf', command=self.show_signup_screen, width=15)
        signup_btn.pack(side=tk.LEFT, padx=5)
        
        back_btn = tk.Button(button_frame, text="Back", font=("Segoe UI", 11), 
                            bg='#ccc', command=self.show_login_screen, width=10)
        back_btn.pack(side=tk.RIGHT, padx=5)
    
    def show_signup_screen(self):
        """Display signup screen"""
        self.clear_frame()
        self.geometry("500x450")
        
        main_frame = tk.Frame(self, bg='#f0f8ff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title = tk.Label(main_frame, text="Create New Account", font=("Segoe UI", 24, "bold"), 
                        fg='#4ecdc4', bg='#f0f8ff')
        title.pack(pady=20)
        
        form_frame = tk.Frame(main_frame, bg='white', relief='raised', bd=2)
        form_frame.pack(pady=20, fill=tk.BOTH, expand=True, padx=20)
        
        # Username
        tk.Label(form_frame, text="Username:", font=("Segoe UI", 11), bg='white').pack(anchor='w', padx=15, pady=(20, 5))
        username_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=30)
        username_entry.pack(padx=15, pady=(0, 15))
        
        # Password
        tk.Label(form_frame, text="Password:", font=("Segoe UI", 11), bg='white').pack(anchor='w', padx=15, pady=(5, 5))
        password_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=30, show='*')
        password_entry.pack(padx=15, pady=(0, 15))
        
        # Confirm Password
        tk.Label(form_frame, text="Confirm Password:", font=("Segoe UI", 11), bg='white').pack(anchor='w', padx=15, pady=(5, 5))
        confirm_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=30, show='*')
        confirm_entry.pack(padx=15, pady=(0, 20))
        
        button_frame = tk.Frame(form_frame, bg='white')
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        def register():
            username = username_entry.get()
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            if not all([username, password, confirm]):
                messagebox.showerror("Error", "All fields required")
                return
            
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match")
                return
            
            if len(password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters")
                return
            
            success, msg = self.db.create_user(username, password, role='client')
            if success:
                messagebox.showinfo("Success", msg)
                self.show_login_screen()
            else:
                messagebox.showerror("Error", msg)
        
        register_btn = tk.Button(button_frame, text="Register", font=("Segoe UI", 11, "bold"), 
                                bg='#4ecdc4', fg='white', command=register, width=15)
        register_btn.pack(side=tk.LEFT, padx=5)
        
        back_btn = tk.Button(button_frame, text="Back", font=("Segoe UI", 11), 
                            bg='#a8e6cf', command=self.show_login_screen, width=15)
        back_btn.pack(side=tk.LEFT, padx=5)
    
    def show_client_dashboard(self):
        """Show client dashboard"""
        self.clear_frame()
        self.geometry("1200x700")
        
        # Header
        header = tk.Frame(self, bg='#4ecdc4', height=60)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text=f"Welcome, {self.current_username}! 👤", 
                        font=("Segoe UI", 16, "bold"), fg='white', bg='#4ecdc4')
        title.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Cloud sync status
        sync_status = "☁️ Cloud Syncing" if self.db.cloud_sync.cloud_enabled else "📱 Local"
        sync_label = tk.Label(header, text=sync_status, font=("Segoe UI", 10), 
                             fg='white', bg='#4ecdc4')
        sync_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        logout_btn = tk.Button(header, text="Logout", font=("Segoe UI", 10), 
                              bg='#ff6b6b', fg='white', command=self.show_login_screen)
        logout_btn.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Main content
        content = ttk.Notebook(self)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Dashboard tab
        self.create_client_dashboard_tab(content)
        
        # Study sessions tab
        self.create_study_sessions_tab(content)
        
        # Analytics tab
        self.create_analytics_tab(content)
    
    def create_client_dashboard_tab(self, notebook):
        """Create client dashboard tab"""
        dash_frame = ttk.Frame(notebook)
        notebook.add(dash_frame, text="📊 Dashboard")
        
        main = tk.Frame(dash_frame, bg='#f0f8ff')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Quick start study
        quick_frame = tk.Frame(main, bg='#a8e6cf', relief='raised', bd=3)
        quick_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(quick_frame, text="Start Study Session", font=("Segoe UI", 12, "bold"), 
                fg='#1a1a1a', bg='#a8e6cf').pack(anchor='w', padx=15, pady=10)
        
        form_frame = tk.Frame(quick_frame, bg='#a8e6cf')
        form_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Label(form_frame, text="Activity:", font=("Segoe UI", 10), bg='#a8e6cf').pack(side=tk.LEFT, padx=5)
        subject_var = tk.StringVar()
        activity_options = ['📚 Study', '💤 Sleep', '🙏 Japa', '📖 Book Reading', 
                           '🌅 Morning Program', '🏃 Exercise', '🍽️ Eating', 
                           '🎯 Goal Setting', '📝 Planning', '💼 Other']
        subject_combo = ttk.Combobox(form_frame, textvariable=subject_var, 
                                     values=activity_options, state='readonly', width=20)
        subject_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(form_frame, text="Notes:", font=("Segoe UI", 10), bg='#a8e6cf').pack(side=tk.LEFT, padx=5)
        topic_entry = tk.Entry(form_frame, font=("Segoe UI", 10), width=25)
        topic_entry.pack(side=tk.LEFT, padx=5)
        
        def start_session():
            subject = subject_var.get()
            topic = topic_entry.get()
            
            if not subject:
                messagebox.showerror("Error", "Please select an activity")
                return
            
            self.tracker.start_study_session(subject, topic)
            messagebox.showinfo("Success", f"Activity started: {subject}")
            topic_entry.delete(0, tk.END)
        
        start_btn = tk.Button(form_frame, text="Start", font=("Segoe UI", 10, "bold"), 
                             bg='#4ecdc4', fg='white', command=start_session)
        start_btn.pack(side=tk.LEFT, padx=5)
        
        # Study stats
        stats_frame = tk.Frame(main, bg='#ffd93d', relief='raised', bd=3)
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        
        tk.Label(stats_frame, text="Today's Activity Stats", font=("Segoe UI", 12, "bold"), 
                fg='#1a1a1a', bg='#ffd93d').pack(anchor='w', padx=15, pady=10)
        
        sessions = self.db.get_user_sessions(self.current_user_id, days=1)
        total_minutes = sum([s[5] for s in sessions])  # s[5] is duration
        
        stats_text = f"""
        📊 Activities Today: {len(sessions)}
        ⏱️  Total Time: {total_minutes // 60}h {total_minutes % 60}m
        ☁️  Cloud Sync: {'Enabled' if self.db.cloud_sync.cloud_enabled else 'Local Mode'}
        """
        
        tk.Label(stats_frame, text=stats_text, font=("Segoe UI", 11), 
                fg='#1a1a1a', bg='#ffd93d', justify=tk.LEFT).pack(anchor='w', padx=15, pady=10)
    
    def create_study_sessions_tab(self, notebook):
        """Create study sessions tab"""
        session_frame = ttk.Frame(notebook)
        notebook.add(session_frame, text="📝 Sessions")
        
        main = tk.Frame(session_frame, bg='#f0f8ff')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Session list
        tk.Label(main, text="Recent Study Sessions (Last 30 days)", font=("Segoe UI", 12, "bold"), 
                fg='#4ecdc4', bg='#f0f8ff').pack(anchor='w', pady=10)
        
        # Create treeview
        columns = ('Subject', 'Topic', 'Date', 'Duration (min)')
        tree = ttk.Treeview(main, columns=columns, height=15)
        tree.heading('#0', text='#')
        tree.column('#0', width=30)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Load sessions
        sessions = self.db.get_user_sessions(self.current_user_id, days=30)
        for idx, session in enumerate(sessions):
            start_time = datetime.datetime.fromisoformat(session[3])
            tree.insert('', tk.END, text=str(idx+1), 
                       values=(session[1], session[2], start_time.strftime('%Y-%m-%d %H:%M'), session[5]))
    
    def create_analytics_tab(self, notebook):
        """Create analytics tab"""
        analytics_frame = ttk.Frame(notebook)
        notebook.add(analytics_frame, text="📈 Analytics")
        
        main = tk.Frame(analytics_frame, bg='#f0f8ff')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Get stats
        stats = self.db.get_client_stats(self.current_user_id, days=30)
        
        if stats:
            # Create chart
            fig = Figure(figsize=(10, 5), dpi=80)
            ax = fig.add_subplot(111)
            
            subjects = [s[0] for s in stats]
            hours = [s[1]/60 for s in stats]  # Convert to hours
            
            ax.bar(subjects, hours, color='#4ecdc4', alpha=0.8)
            ax.set_ylabel('Hours', fontsize=10)
            ax.set_title('Study Time by Subject (Last 30 days)', fontsize=12, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=main)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(main, text="No study data available yet", font=("Segoe UI", 14), 
                    fg='#999', bg='#f0f8ff').pack(pady=20)
    
    def show_admin_dashboard(self):
        """Show admin dashboard"""
        self.clear_frame()
        self.geometry("1400x800")
        
        # Header
        header = tk.Frame(self, bg='#ff6b6b', height=60)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text=f"👨‍🏫 Admin Dashboard - {self.current_username}", 
                        font=("Segoe UI", 16, "bold"), fg='white', bg='#ff6b6b')
        title.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Cloud sync status
        sync_status = "☁️ Cloud Sync: Enabled" if self.db.cloud_sync.cloud_enabled else "📱 Local Mode"
        sync_label = tk.Label(header, text=sync_status, font=("Segoe UI", 10), 
                             fg='white', bg='#ff6b6b')
        sync_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        def sync_now():
            messagebox.showinfo("Cloud Sync", "Syncing all student data...\nThis feature requires Firebase or API setup.")
        
        sync_btn = tk.Button(header, text="🔄 Sync Now", font=("Segoe UI", 10), 
                            bg='#4ecdc4', fg='white', command=sync_now)
        sync_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        logout_btn = tk.Button(header, text="Logout", font=("Segoe UI", 10), 
                              bg='#1a1a1a', fg='white', command=self.show_login_screen)
        logout_btn.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Main content
        content = ttk.Notebook(self)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Clients tab
        self.create_clients_management_tab(content)
        
        # Reports tab
        self.create_reports_tab(content)
        
        # User management tab
        self.create_user_management_tab(content)
    
    def create_clients_management_tab(self, notebook):
        """Create clients management tab"""
        client_frame = ttk.Frame(notebook)
        notebook.add(client_frame, text="👥 Clients")
        
        main = tk.Frame(client_frame, bg='#f0f8ff')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Assign client
        assign_frame = tk.Frame(main, bg='#a8e6cf', relief='raised', bd=3)
        assign_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(assign_frame, text="Assign New Client", font=("Segoe UI", 12, "bold"), 
                fg='#1a1a1a', bg='#a8e6cf').pack(anchor='w', padx=15, pady=10)
        
        form_frame = tk.Frame(assign_frame, bg='#a8e6cf')
        form_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Label(form_frame, text="Client Username:", font=("Segoe UI", 10), bg='#a8e6cf').pack(side=tk.LEFT, padx=5)
        username_entry = tk.Entry(form_frame, font=("Segoe UI", 10), width=25)
        username_entry.pack(side=tk.LEFT, padx=5)
        
        def assign_client():
            username = username_entry.get()
            if not username:
                messagebox.showerror("Error", "Enter client username")
                return
            
            success, msg = self.db.assign_client(self.current_user_id, username)
            messagebox.showinfo("Info", msg)
            
            if success:
                username_entry.delete(0, tk.END)
                refresh_clients()
        
        assign_btn = tk.Button(form_frame, text="Assign", font=("Segoe UI", 10, "bold"), 
                              bg='#4ecdc4', fg='white', command=assign_client)
        assign_btn.pack(side=tk.LEFT, padx=5)
        
        # Clients list
        tk.Label(main, text="Your Clients", font=("Segoe UI", 12, "bold"), 
                fg='#4ecdc4', bg='#f0f8ff').pack(anchor='w', pady=10)
        
        # Create treeview
        columns = ('Username', 'Joined', 'Study Sessions')
        tree = ttk.Treeview(main, columns=columns, height=15)
        tree.heading('#0', text='#')
        tree.column('#0', width=30)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        def refresh_clients():
            # Clear tree
            for item in tree.get_children():
                tree.delete(item)
            
            # Load clients
            clients = self.db.get_all_clients(self.current_user_id)
            for idx, client in enumerate(clients):
                sessions = self.db.get_user_sessions(client[0], days=30)
                tree.insert('', tk.END, text=str(idx+1), 
                           values=(client[1], client[2], len(sessions)))
        
        refresh_clients()
    
    def create_reports_tab(self, notebook):
        """Create reports tab"""
        report_frame = ttk.Frame(notebook)
        notebook.add(report_frame, text="📊 Reports")
        
        main = tk.Frame(report_frame, bg='#f0f8ff')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(main, text="All Clients Study Sessions", font=("Segoe UI", 12, "bold"), 
                fg='#4ecdc4', bg='#f0f8ff').pack(anchor='w', pady=10)
        
        # Create treeview
        columns = ('Client', 'Subject', 'Topic', 'Date', 'Duration (min)')
        tree = ttk.Treeview(main, columns=columns, height=20)
        tree.heading('#0', text='#')
        tree.column('#0', width=30)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Load all sessions
        sessions = self.db.get_all_sessions_for_admin(self.current_user_id)
        for idx, session in enumerate(sessions):
            start_time = datetime.datetime.fromisoformat(session[3])
            tree.insert('', tk.END, text=str(idx+1), 
                       values=(session[0], session[1], session[2], 
                              start_time.strftime('%Y-%m-%d %H:%M'), session[5]))
    
    def create_user_management_tab(self, notebook):
        """Create user management tab"""
        user_frame = ttk.Frame(notebook)
        notebook.add(user_frame, text="⚙️ Users")
        
        main = tk.Frame(user_frame, bg='#f0f8ff')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(main, text="Create New User Account", font=("Segoe UI", 12, "bold"), 
                fg='#4ecdc4', bg='#f0f8ff').pack(anchor='w', pady=10)
        
        form_frame = tk.Frame(main, bg='white', relief='raised', bd=2)
        form_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(form_frame, text="Username:", font=("Segoe UI", 10), bg='white').pack(anchor='w', padx=15, pady=(10, 5))
        username_entry = tk.Entry(form_frame, font=("Segoe UI", 10), width=30)
        username_entry.pack(padx=15, pady=(0, 10))
        
        tk.Label(form_frame, text="Password:", font=("Segoe UI", 10), bg='white').pack(anchor='w', padx=15, pady=(5, 5))
        password_entry = tk.Entry(form_frame, font=("Segoe UI", 10), width=30, show='*')
        password_entry.pack(padx=15, pady=(0, 10))
        
        tk.Label(form_frame, text="Role:", font=("Segoe UI", 10), bg='white').pack(anchor='w', padx=15, pady=(5, 5))
        role_var = tk.StringVar(value='client')
        role_combo = ttk.Combobox(form_frame, textvariable=role_var, 
                                 values=['client', 'admin'], state='readonly', width=28)
        role_combo.pack(padx=15, pady=(0, 15))
        
        def create_user():
            username = username_entry.get()
            password = password_entry.get()
            role = role_var.get()
            
            if not all([username, password]):
                messagebox.showerror("Error", "All fields required")
                return
            
            success, msg = self.db.create_user(username, password, role)
            messagebox.showinfo("Info", msg)
            
            if success:
                username_entry.delete(0, tk.END)
                password_entry.delete(0, tk.END)
        
        create_btn = tk.Button(form_frame, text="Create User", font=("Segoe UI", 10, "bold"), 
                              bg='#4ecdc4', fg='white', command=create_user)
        create_btn.pack(padx=15, pady=15)


if __name__ == '__main__':
    app = StudyTrackerApp()
    app.mainloop()
