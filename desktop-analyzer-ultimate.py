#!/usr/bin/env python3
"""
AI Log Analyzer - Ultimate Desktop Edition
Streamlined desktop application with comprehensive analysis capabilities.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import re
import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
import tempfile

try:
    import customtkinter as ctk
    MODERN_GUI = True
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
except ImportError:
    MODERN_GUI = False
    print("CustomTkinter not available. Using standard GUI.")

class UltimateLogAnalyzer:
    def __init__(self):
        """Initialize the ultimate log analyzer"""
        self.selected_file = None
        self.analysis_results = None
        self.ai_available = False
        self.ai_models = []
        self.selected_ai_model = "Rule-based"
        self.analysis_running = False
        
        # AI model preferences for different log types
        self.optimal_models = {
            'firmware': ['deepseek-coder:6.7b', 'codellama:13b', 'phi3:medium'],
            'pipeline': ['codellama:13b', 'mistral:7b-instruct', 'llama3.1:8b'],
            'testing': ['deepseek-coder:6.7b', 'codellama:7b', 'phi3:mini'],
            'general': ['llama3.1:8b', 'mistral:7b-instruct', 'codellama:7b']
        }
        
        self.check_ai_status()
        self.setup_gui()
    
    def check_ai_status(self):
        """Check AI model availability"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    self.ai_available = True
                    self.ai_models = [model['name'] for model in models]
        except:
            self.ai_available = False
    
    def detect_log_type(self, content):
        """Detect log type from content"""
        content_lower = content.lower()
        
        # Firmware/Hardware indicators
        firmware_keywords = ['vrm', 'voltage', 'thermal', 'ecc', 'memory', 'cpu', 'bios', 'dimm', 'sensors', 'temperature']
        firmware_score = sum(1 for keyword in firmware_keywords if keyword in content_lower)
        
        # Pipeline/CI-CD indicators  
        pipeline_keywords = ['build', 'deploy', 'pipeline', 'azure', 'jenkins', 'docker', 'npm', 'maven', 'gradle']
        pipeline_score = sum(1 for keyword in pipeline_keywords if keyword in content_lower)
        
        # Testing indicators
        testing_keywords = ['test', 'assert', 'pytest', 'jest', 'junit', 'spec', 'mock', 'fixture']
        testing_score = sum(1 for keyword in testing_keywords if keyword in content_lower)
        
        # Determine log type
        scores = {'firmware': firmware_score, 'pipeline': pipeline_score, 'testing': testing_score}
        detected_type = max(scores, key=scores.get) if max(scores.values()) > 2 else 'general'
        
        return detected_type
    
    def select_optimal_model(self, log_type):
        """Select optimal AI model for log type"""
        if not self.ai_available or not self.ai_models:
            return "Rule-based"
        
        recommended = self.optimal_models.get(log_type, self.optimal_models['general'])
        available_recommended = [model for model in recommended if model in self.ai_models]
        
        if available_recommended:
            return available_recommended[0]
        else:
            return self.ai_models[0] if self.ai_models else "Rule-based"
    
    def setup_gui(self):
        """Setup the main GUI"""
        if MODERN_GUI:
            self.setup_modern_gui()
        else:
            self.setup_fallback_gui()
    
    def setup_modern_gui(self):
        """Setup modern CustomTkinter GUI"""
        self.root = ctk.CTk()
        self.root.title("AI Log Analyzer - RCA companion")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Main container
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(main_container, height=80, fg_color="#1e1e1e")
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="🏢 AI Log Analyzer",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        title.pack(side="left", padx=20, pady=20)
        
        # AI Status
        self.ai_status_label = ctk.CTkLabel(
            header,
            text="🔴 AI Offline",
            font=ctk.CTkFont(size=14),
            text_color="#ff4444"
        )
        self.ai_status_label.pack(side="right", padx=20, pady=20)
        
        if self.ai_available:
            self.ai_status_label.configure(
                text=f"🟢 AI Ready ({len(self.ai_models)} models)",
                text_color="#00ff88"
            )
        
        # Content area
        content_frame = ctk.CTkFrame(main_container)
        content_frame.pack(fill="both", expand=True)
        
        # Left panel - Controls
        left_panel = ctk.CTkFrame(content_frame, width=400)
        left_panel.pack(side="left", fill="y", padx=(20, 10), pady=20)
        left_panel.pack_propagate(False)
        
        self.setup_controls(left_panel)
        
        # Right panel - Results
        right_panel = ctk.CTkFrame(content_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 20), pady=20)
        
        self.setup_results(right_panel)
    
    def setup_fallback_gui(self):
        """Setup fallback tkinter GUI"""
        self.root = tk.Tk()
        self.root.title("AI Log Analyzer - RCA companion")
        self.root.geometry("1400x900")
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Controls frame
        controls_frame = ttk.LabelFrame(main_frame, text="Analysis Controls", padding=10)
        controls_frame.pack(side="left", fill="y", padx=(0, 10))
        
        self.setup_basic_controls(controls_frame)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.pack(side="right", fill="both", expand=True)
        
        self.setup_basic_results(results_frame)
    
    def setup_controls(self, parent):
        """Setup modern control panel"""
        # File selection
        file_section = ctk.CTkFrame(parent, fg_color="transparent")
        file_section.pack(fill="x", pady=(20, 20))
        
        file_title = ctk.CTkLabel(
            file_section,
            text="📁 File Selection",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        file_title.pack(anchor="w", pady=(0, 15))
        
        self.file_label = ctk.CTkLabel(
            file_section,
            text="No file selected",
            font=ctk.CTkFont(size=12),
            text_color="#cccccc",
            wraplength=350
        )
        self.file_label.pack(anchor="w", pady=(0, 10))
        
        file_buttons = ctk.CTkFrame(file_section, fg_color="transparent")
        file_buttons.pack(fill="x")
        
        self.browse_btn = ctk.CTkButton(
            file_buttons,
            text="📂 Browse",
            command=self.select_file,
            width=120,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.browse_btn.pack(side="left", padx=(0, 10))
        
        self.clear_btn = ctk.CTkButton(
            file_buttons,
            text="🗑️ Clear",
            command=self.clear_file,
            width=80,
            height=35,
            fg_color="#d13438",
            hover_color="#b52d31"
        )
        self.clear_btn.pack(side="left")
        
        # Analysis mode
        mode_section = ctk.CTkFrame(parent, fg_color="transparent")
        mode_section.pack(fill="x", pady=(30, 20))
        
        mode_title = ctk.CTkLabel(
            mode_section,
            text="⚙️ Analysis Mode",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        mode_title.pack(anchor="w", pady=(0, 15))
        
        self.analysis_mode = tk.StringVar(value="smart")
        
        modes = [
            ("fast", "⚡ Fast", "Quick pattern detection"),
            ("smart", "🧠 Smart", "Balanced analysis with AI"),
            ("thorough", "🔬 Thorough", "Deep analysis with causal chains")
        ]
        
        for value, display, desc in modes:
            mode_frame = ctk.CTkFrame(mode_section, fg_color="transparent")
            mode_frame.pack(fill="x", pady=5)
            
            radio = ctk.CTkRadioButton(
                mode_frame,
                text=f"{display} - {desc}",
                variable=self.analysis_mode,
                value=value,
                font=ctk.CTkFont(size=13),
                text_color="white"
            )
            radio.pack(anchor="w")
        
        # AI Model info
        ai_section = ctk.CTkFrame(parent, fg_color="transparent")
        ai_section.pack(fill="x", pady=(30, 20))
        
        ai_title = ctk.CTkLabel(
            ai_section,
            text="🤖 AI Configuration",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        ai_title.pack(anchor="w", pady=(0, 15))
        
        self.model_label = ctk.CTkLabel(
            ai_section,
            text="Model: Rule-based analysis",
            font=ctk.CTkFont(size=12),
            text_color="#cccccc"
        )
        self.model_label.pack(anchor="w", pady=(0, 10))
        
        # Analysis button
        action_section = ctk.CTkFrame(parent, fg_color="transparent")
        action_section.pack(fill="x", pady=(30, 20))
        
        self.analyze_btn = ctk.CTkButton(
            action_section,
            text="🔬 Start Analysis",
            command=self.start_analysis,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#107c10",
            hover_color="#0e6e0e",
            state="disabled"
        )
        self.analyze_btn.pack(pady=10)
        
        # Progress
        self.progress_frame = ctk.CTkFrame(action_section, fg_color="transparent")
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=350,
            height=8
        )
        self.progress_bar.pack(fill="x", pady=(15, 5))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Ready to analyze",
            font=ctk.CTkFont(size=12),
            text_color="#cccccc"
        )
        self.progress_label.pack()
    
    def setup_basic_controls(self, parent):
        """Setup basic controls for fallback GUI"""
        # File selection
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill="x", pady=10)
        
        ttk.Label(file_frame, text="Log File:").pack(anchor="w")
        
        self.file_label = ttk.Label(file_frame, text="No file selected", foreground="gray")
        self.file_label.pack(anchor="w", pady=(5, 10))
        
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill="x")
        
        self.browse_btn = ttk.Button(button_frame, text="Browse", command=self.select_file)
        self.browse_btn.pack(side="left", padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="Clear", command=self.clear_file)
        self.clear_btn.pack(side="left")
        
        # Analysis mode
        mode_frame = ttk.LabelFrame(parent, text="Analysis Mode", padding=10)
        mode_frame.pack(fill="x", pady=10)
        
        self.analysis_mode = tk.StringVar(value="smart")
        
        ttk.Radiobutton(mode_frame, text="Fast - Quick analysis", variable=self.analysis_mode, value="fast").pack(anchor="w")
        ttk.Radiobutton(mode_frame, text="Smart - Balanced analysis", variable=self.analysis_mode, value="smart").pack(anchor="w")
        ttk.Radiobutton(mode_frame, text="Thorough - Deep analysis", variable=self.analysis_mode, value="thorough").pack(anchor="w")
        
        # AI Status
        ai_frame = ttk.Frame(parent)
        ai_frame.pack(fill="x", pady=10)
        
        self.ai_status_label = ttk.Label(ai_frame, text="AI: Offline", foreground="red")
        self.ai_status_label.pack(anchor="w")
        
        if self.ai_available:
            self.ai_status_label.configure(text=f"AI: Ready ({len(self.ai_models)} models)", foreground="green")
        
        self.model_label = ttk.Label(ai_frame, text="Model: Rule-based", foreground="gray")
        self.model_label.pack(anchor="w")
        
        # Analysis button
        self.analyze_btn = ttk.Button(parent, text="Start Analysis", command=self.start_analysis, state="disabled")
        self.analyze_btn.pack(pady=20)
        
        # Progress
        self.progress_frame = ttk.Frame(parent)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress_bar.pack(fill="x", pady=5)
        
        self.progress_label = ttk.Label(self.progress_frame, text="Ready to analyze")
        self.progress_label.pack()
    
    def setup_results(self, parent):
        """Setup modern results panel"""
        results_title = ctk.CTkLabel(
            parent,
            text="📊 Analysis Results",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        )
        results_title.pack(pady=(20, 15))
        
        # Tabs
        self.results_tabview = ctk.CTkTabview(parent, width=800, height=600)
        self.results_tabview.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Create tabs
        tabs = ["Summary", "Root Causes", "Timeline", "Export"]
        self.tab_textboxes = {}
        
        for tab_name in tabs:
            tab = self.results_tabview.add(tab_name)
            
            if tab_name == "Export":
                self.setup_export_tab(tab)
            else:
                textbox = ctk.CTkTextbox(
                    tab,
                    wrap="word",
                    font=ctk.CTkFont(size=12, family="Consolas"),
                    fg_color="#2d2d2d",
                    text_color="white"
                )
                textbox.pack(fill="both", expand=True, padx=10, pady=10)
                self.tab_textboxes[tab_name.lower()] = textbox
    
    def setup_basic_results(self, parent):
        """Setup basic results for fallback GUI"""
        self.results_notebook = ttk.Notebook(parent)
        self.results_notebook.pack(fill="both", expand=True)
        
        tabs = ["Summary", "Root Causes", "Timeline", "Export"]
        self.tab_textboxes = {}
        
        for tab_name in tabs:
            frame = ttk.Frame(self.results_notebook)
            self.results_notebook.add(frame, text=tab_name)
            
            if tab_name == "Export":
                self.setup_basic_export_tab(frame)
            else:
                text_widget = tk.Text(frame, wrap="word", font=("Consolas", 10))
                scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
                text_widget.configure(yscrollcommand=scrollbar.set)
                
                text_widget.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
                
                self.tab_textboxes[tab_name.lower()] = text_widget
    
    def setup_export_tab(self, parent):
        """Setup export controls"""
        export_container = ctk.CTkFrame(parent, fg_color="transparent")
        export_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        export_title = ctk.CTkLabel(
            export_container,
            text="📦 Export Analysis Results",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        export_title.pack(pady=(0, 20))
        
        self.export_json_btn = ctk.CTkButton(
            export_container,
            text="💾 Export as JSON",
            command=lambda: self.export_results("json"),
            width=200,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.export_json_btn.pack(pady=5)
        
        self.export_report_btn = ctk.CTkButton(
            export_container,
            text="📄 Export Report",
            command=lambda: self.export_results("report"),
            width=200,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#107c10",
            hover_color="#0e6e0e",
            state="disabled"
        )
        self.export_report_btn.pack(pady=5)
    
    def setup_basic_export_tab(self, parent):
        """Setup basic export controls"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=20)
        
        self.export_json_btn = ttk.Button(button_frame, text="Export JSON", command=lambda: self.export_results("json"), state="disabled")
        self.export_json_btn.pack(pady=5)
        
        self.export_report_btn = ttk.Button(button_frame, text="Export Report", command=lambda: self.export_results("report"), state="disabled")
        self.export_report_btn.pack(pady=5)
    
    def select_file(self):
        """Select log file for analysis"""
        file_path = filedialog.askopenfilename(
            title="Select Log File",
            filetypes=[
                ("Log files", "*.log"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.selected_file = file_path
            filename = Path(file_path).name
            self.file_label.configure(text=f"Selected: {filename}")
            
            if MODERN_GUI:
                self.analyze_btn.configure(state="normal")
            else:
                self.analyze_btn.configure(state="normal")
    
    def clear_file(self):
        """Clear selected file"""
        self.selected_file = None
        self.file_label.configure(text="No file selected")
        
        if MODERN_GUI:
            self.analyze_btn.configure(state="disabled")
        else:
            self.analyze_btn.configure(state="disabled")
    
    def start_analysis(self):
        """Start log analysis"""
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a log file first.")
            return
        
        if self.analysis_running:
            return
        
        self.analysis_running = True
        
        if MODERN_GUI:
            self.progress_frame.pack(fill="x", pady=(20, 0))
            self.analyze_btn.configure(state="disabled")
        else:
            self.progress_frame.pack(fill="x", pady=10)
            self.analyze_btn.configure(state="disabled")
        
        # Start analysis in background thread
        threading.Thread(target=self.run_analysis, daemon=True).start()
    
    def run_analysis(self):
        """Run comprehensive log analysis"""
        try:
            # Read file
            self.update_progress(0.1, "Reading log file...")
            
            with open(self.selected_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Detect log type and select optimal model
            self.update_progress(0.2, "Analyzing log type...")
            log_type = self.detect_log_type(content)
            self.selected_ai_model = self.select_optimal_model(log_type)
            
            # Update model display
            self.root.after(0, lambda: self.model_label.configure(
                text=f"Model: {self.selected_ai_model} (for {log_type} logs)"
            ))
            
            # Parse entries
            self.update_progress(0.4, "Parsing log entries...")
            entries = self.parse_log_entries(content)
            
            # Analyze patterns
            self.update_progress(0.6, "Detecting patterns...")
            errors, patterns = self.analyze_patterns(entries)
            
            # Build causal chains
            self.update_progress(0.8, "Building causal chains...")
            root_causes = self.identify_root_causes(entries, errors, patterns)
            
            # Calculate metrics
            self.update_progress(0.9, "Calculating metrics...")
            performance_metrics = self.calculate_performance_metrics(entries)
            
            # Compile results
            self.analysis_results = {
                'file_info': {
                    'name': Path(self.selected_file).name,
                    'size': len(content),
                    'total_lines': len([line for line in content.split('\n') if line.strip()])
                },
                'mode': self.analysis_mode.get(),
                'ai_model': self.selected_ai_model,
                'log_type': log_type,
                'entries': entries,
                'errors': errors,
                'warnings': [e for e in entries if 5 <= e.get('severity', 0) < 7],
                'patterns': patterns,
                'root_causes': root_causes,
                'performance_metrics': performance_metrics,
                'analysis_time': time.time() - self.start_time
            }
            
            self.update_progress(1.0, "Analysis complete!")
            
            # Display results
            self.root.after(100, self.display_results)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Analysis Error", f"Failed to analyze log file:\n{str(e)}"))
        finally:
            self.analysis_running = False
    
    def parse_log_entries(self, content):
        """Parse log entries with timestamp and severity"""
        entries = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Extract timestamp
            timestamp = self.extract_timestamp(line)
            
            # Extract log level
            level = self.extract_log_level(line)
            
            # Calculate severity
            severity = self.calculate_severity(level, line)
            
            entry = {
                'line': i,
                'timestamp': timestamp,
                'level': level,
                'message': line,
                'severity': severity
            }
            entries.append(entry)
        
        return entries
    
    def extract_timestamp(self, line):
        """Extract timestamp from log line"""
        patterns = [
            r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?)',
            r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})',
            r'(\w{3} \d{2} \d{2}:\d{2}:\d{2})',
            r'(\d{2}-\w{3}-\d{4} \d{2}:\d{2}:\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    timestamp_str = match.group(1)
                    formats = [
                        '%Y-%m-%d %H:%M:%S.%f',
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%dT%H:%M:%S.%fZ',
                        '%Y-%m-%dT%H:%M:%S',
                        '%m/%d/%Y %H:%M:%S',
                        '%b %d %H:%M:%S',
                        '%d-%b-%Y %H:%M:%S'
                    ]
                    
                    for fmt in formats:
                        try:
                            if fmt == '%b %d %H:%M:%S':
                                current_year = datetime.now().year
                                return datetime.strptime(f"{current_year} {timestamp_str}", f'%Y {fmt}')
                            else:
                                return datetime.strptime(timestamp_str.replace('T', ' ').replace('Z', ''), fmt)
                        except:
                            continue
                except:
                    continue
        
        return datetime.now()
    
    def extract_log_level(self, line):
        """Extract log level from line"""
        levels = ['CRITICAL', 'FATAL', 'ERROR', 'WARNING', 'WARN', 'INFO', 'DEBUG', 'TRACE']
        line_upper = line.upper()
        
        for level in levels:
            if f'[{level}]' in line_upper or f' {level} ' in line_upper or f'{level}:' in line_upper:
                return level
        
        # Infer from keywords
        error_indicators = ['exception', 'error', 'failed', 'failure', 'crash', 'panic']
        warning_indicators = ['warning', 'warn', 'deprecated', 'timeout', 'retry']
        
        line_lower = line.lower()
        
        if any(indicator in line_lower for indicator in error_indicators):
            return 'ERROR'
        elif any(indicator in line_lower for indicator in warning_indicators):
            return 'WARNING'
        else:
            return 'INFO'
    
    def calculate_severity(self, level, message):
        """Calculate severity score with success detection"""
        message_lower = message.lower()
        
        # Check for success indicators first (completely exclude from severity analysis)
        success_indicators = [
            'completed successfully', 'success', 'passed', 'ok', 'normal',
            'healthy', 'good', 'operational', 'ready', 'online', 'active',
            'optimal', 'excellent', 'within normal range', 'is good', 'is normal',
            'is optimal', 'is excellent', '100%', 'all systems operational',
            'is valid', 'are running normally', 'test passed', 'responded successfully'
        ]
        
        if any(indicator in message_lower for indicator in success_indicators):
            return 0  # No severity for successful operations
        
        base_scores = {
            'CRITICAL': 10, 'FATAL': 10, 'ERROR': 7, 
            'WARNING': 5, 'WARN': 5, 'INFO': 3, 'DEBUG': 1, 'TRACE': 1
        }
        
        # Check for actual failure indicators
        failure_keywords = {
            'panic': 2.0, 'crash': 1.8, 'failed': 1.7, 'failure': 1.7,
            'segfault': 1.9, 'timeout': 1.4, 'denied': 1.5,
            'authentication': 1.4, 'permission': 1.3, 'refused': 1.4,
            'unreachable': 1.5, 'disconnected': 1.3, 'lost': 1.3
        }
        
        score = base_scores.get(level, 3)
        
        # Only apply multipliers for actual failures
        for keyword, multiplier in failure_keywords.items():
            if keyword in message_lower:
                score *= multiplier
                break
        
        return min(score, 10)
    
    def analyze_patterns(self, entries):
        """Analyze patterns and extract errors"""
        errors = []
        patterns = defaultdict(int)
        
        for entry in entries:
            # Only treat as error if severity > 0 (excludes successful operations)
            if entry['severity'] > 0:  # Any severity above 0 (successful ops have 0)
                message_lower = entry['message'].lower()
                
                # Double-check: Skip entries that are clearly successful operations
                success_indicators = [
                    'completed successfully', 'success', 'passed', 'ok', 'normal',
                    'healthy', 'good', 'operational', 'ready', 'online', 'active',
                    'optimal', 'excellent', 'within normal range', 'is good', 'is normal',
                    'is optimal', 'is excellent', '100%', 'all systems operational',
                    'is valid', 'are running normally', 'test passed', 'responded successfully'
                ]
                
                is_success = any(indicator in message_lower for indicator in success_indicators)
                
                if not is_success:  # Only add to errors if it's not a success message
                    error_type = self.classify_error(entry['message'])
                    errors.append({
                        **entry,
                        'type': error_type
                    })
                    patterns[error_type] += 1
        
        return errors, dict(patterns)
    
    def classify_error(self, line):
        """Classify error type"""
        line_lower = line.lower()
        
        classifications = {
            'Hardware': ['vrm', 'voltage', 'thermal', 'temperature', 'cpu', 'memory', 'dimm', 'ecc', 'sensors', 'fan'],
            'Firmware': ['bios', 'uefi', 'firmware', 'boot', 'microcode', 'driver'],
            'Database': ['database', 'sql', 'connection', 'query', 'table', 'schema', 'mysql', 'postgres'],
            'Network': ['network', 'timeout', 'socket', 'connection', 'http', 'tcp', 'udp', 'dns', 'ssl'],
            'Memory': ['memory', 'heap', 'oom', 'allocation', 'garbage', 'leak', 'buffer'],
            'Filesystem': ['file', 'permission', 'disk', 'directory', 'io', 'read', 'write', 'space'],
            'Authentication': ['auth', 'login', 'credential', 'token', 'session', 'password', 'unauthorized'],
            'Security': ['security', 'access', 'forbidden', 'ssl', 'tls', 'certificate', 'encryption'],
            'Performance': ['slow', 'performance', 'latency', 'bottleneck', 'cpu', 'lag', 'delay'],
            'Configuration': ['config', 'setting', 'parameter', 'property', 'environment', 'variable'],
            'Pipeline': ['build', 'deploy', 'pipeline', 'ci', 'cd', 'jenkins', 'azure', 'docker'],
            'Testing': ['test', 'assert', 'pytest', 'jest', 'junit', 'spec', 'mock', 'fixture']
        }
        
        for category, keywords in classifications.items():
            if any(keyword in line_lower for keyword in keywords):
                return category
        
        # Check for common error indicators
        if any(word in line_lower for word in ['error', 'exception', 'fail', 'crash', 'panic']):
            return "Application"
        
        if any(word in line_lower for word in ['warn', 'warning', 'deprecated']):
            return "Warning"
        
        return "General"
    
    def identify_root_causes(self, entries, errors, patterns):
        """Identify root causes using causal chain analysis"""
        root_causes = []
        
        # Build causal chains
        chains = self.build_causal_chains(entries, errors)
        
        # Add causal chain analysis
        for chain in chains:
            if len(chain['events']) >= 3:
                root_causes.append({
                    'title': chain['title'],
                    'description': chain['description'],
                    'causal_chain': chain['chain_text'],
                    'confidence': chain['confidence'],
                    'count': len(chain['events']),
                    'severity': chain['severity'],
                    'recommendations': chain['recommendations']
                })
        
        # Pattern-based analysis (lowered threshold from 3 to 1)
        for error_type, count in patterns.items():
            if count >= 1:  # Generate root causes for any error pattern
                confidence = min(0.95, 0.5 + count * 0.1)
                
                root_causes.append({
                    'title': f'{error_type} System Issue',
                    'description': f'Multiple {error_type.lower()} events ({count} occurrences) indicate systematic problem',
                    'confidence': confidence,
                    'count': count,
                    'severity': 'High' if count >= 5 else 'Medium' if count >= 2 else 'Low',
                    'recommendations': [
                        f'Investigate {error_type.lower()} infrastructure components',
                        'Monitor system resources and performance metrics',
                        'Review recent configuration changes',
                        'Implement preventive monitoring alerts'
                    ]
                })
        
        # Add generic analysis if no specific patterns found
        if not root_causes and errors:
            # Analyze error distribution by severity
            high_severity_errors = [e for e in errors if e['severity'] >= 8]
            medium_severity_errors = [e for e in errors if 6 <= e['severity'] < 8]
            
            if high_severity_errors:
                root_causes.append({
                    'title': 'Critical System Events Detected',
                    'description': f'Found {len(high_severity_errors)} critical severity events requiring immediate attention',
                    'confidence': 0.8,
                    'count': len(high_severity_errors),
                    'severity': 'Critical',
                    'recommendations': [
                        'Review critical events immediately',
                        'Check system stability and performance',
                        'Investigate resource constraints',
                        'Implement monitoring for early detection'
                    ]
                })
            
            if medium_severity_errors:
                root_causes.append({
                    'title': 'System Performance Issues',
                    'description': f'Found {len(medium_severity_errors)} medium severity events indicating performance degradation',
                    'confidence': 0.7,
                    'count': len(medium_severity_errors),
                    'severity': 'Medium',
                    'recommendations': [
                        'Monitor system performance metrics',
                        'Review error patterns for trends',
                        'Consider capacity planning',
                        'Optimize system configuration'
                    ]
                })
        
        # If still no root causes, analyze general log health
        if not root_causes:
            total_errors = len(errors)
            total_entries = len(entries)
            error_rate = (total_errors / total_entries * 100) if total_entries > 0 else 0
            
            if error_rate > 5:  # More than 5% error rate
                root_causes.append({
                    'title': 'High Error Rate Detected',
                    'description': f'Error rate of {error_rate:.1f}% ({total_errors}/{total_entries}) exceeds normal thresholds',
                    'confidence': 0.6,
                    'count': total_errors,
                    'severity': 'Medium',
                    'recommendations': [
                        'Investigate causes of elevated error rate',
                        'Review system configuration and resources',
                        'Implement error rate monitoring',
                        'Consider system optimization'
                    ]
                })
            elif total_entries > 100:  # Large log with low errors
                root_causes.append({
                    'title': 'System Operating Normally',
                    'description': f'Low error rate of {error_rate:.1f}% indicates stable system operation',
                    'confidence': 0.9,
                    'count': total_errors,
                    'severity': 'Low',
                    'recommendations': [
                        'Continue current monitoring practices',
                        'Maintain regular log reviews',
                        'Keep current configuration',
                        'Document stable configuration for reference'
                    ]
                })
        
        return sorted(root_causes, key=lambda x: (x['confidence'], x['count']), reverse=True)
    
    def build_causal_chains(self, entries, errors):
        """Build causal chains showing event progression"""
        chains = []
        
        # Define causal relationships
        causal_patterns = {
            'power_cascade': {
                'triggers': ['vrm', 'voltage', 'power'],
                'chain': ['VRM instability', 'Voltage regulation failure', 'Power delivery issues', 'Component undervolt', 'System instability'],
                'effects': ['thermal', 'cpu', 'hang', 'crash', 'reset']
            },
            'thermal_cascade': {
                'triggers': ['thermal', 'temperature', 'overheat'],
                'chain': ['Thermal threshold exceeded', 'CPU throttling engaged', 'Performance degradation', 'Thermal protection triggered', 'Emergency shutdown'],
                'effects': ['throttle', 'slow', 'hang', 'shutdown', 'reboot']
            },
            'memory_cascade': {
                'triggers': ['memory', 'dram', 'ecc'],
                'chain': ['Memory error detected', 'ECC correction attempts', 'Uncorrectable errors', 'Memory controller panic', 'System halt'],
                'effects': ['correction', 'uncorrectable', 'panic', 'halt', 'crash']
            }
        }
        
        # Sort entries by timestamp
        sorted_entries = sorted(entries, key=lambda x: x['timestamp'])
        
        for pattern_name, pattern_info in causal_patterns.items():
            # Look for trigger events
            trigger_events = []
            for entry in sorted_entries:
                message_lower = entry['message'].lower()
                if any(trigger in message_lower for trigger in pattern_info['triggers']):
                    trigger_events.append(entry)
            
            if not trigger_events:
                continue
            
            # For each trigger, look for subsequent effect events
            for trigger in trigger_events:
                causal_sequence = [trigger]
                current_time = trigger['timestamp']
                
                # Look for effects within the next 30 minutes
                time_window = timedelta(minutes=30)
                
                for entry in sorted_entries:
                    if entry['timestamp'] <= current_time:
                        continue
                    if entry['timestamp'] > current_time + time_window:
                        break
                    
                    message_lower = entry['message'].lower()
                    if any(effect in message_lower for effect in pattern_info['effects']):
                        if entry['severity'] >= 6:  # Medium to high severity
                            causal_sequence.append(entry)
                            current_time = entry['timestamp']
                
                # If we found a meaningful sequence, create a causal chain (lowered from 3 to 2)
                if len(causal_sequence) >= 2:
                    chain_text = ' → '.join(pattern_info['chain'][:len(causal_sequence)])
                    
                    # Calculate confidence based on sequence length and timing
                    confidence = min(0.95, 0.7 + len(causal_sequence) * 0.05)
                    
                    # Determine severity
                    max_severity = max(event['severity'] for event in causal_sequence)
                    severity = 'Critical' if max_severity >= 9 else 'High' if max_severity >= 7 else 'Medium'
                    
                    chains.append({
                        'title': f'{pattern_name.replace("_", " ").title()} Failure Chain',
                        'description': f'Detected cascading failure pattern with {len(causal_sequence)} linked events',
                        'chain_text': chain_text,
                        'events': causal_sequence,
                        'confidence': confidence,
                        'severity': severity,
                        'recommendations': [
                            f'Investigate root cause in {pattern_info["triggers"][0]} subsystem',
                            'Implement early warning monitoring for cascade prevention',
                            'Review protection mechanisms and failsafes',
                            'Consider redundancy improvements for critical components'
                        ]
                    })
        
        return chains
    
    def calculate_performance_metrics(self, entries):
        """Calculate performance metrics"""
        severity_distribution = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for entry in entries:
            severity = entry['severity']
            if severity >= 9:
                severity_distribution['critical'] += 1
            elif severity >= 7:
                severity_distribution['high'] += 1
            elif severity >= 5:
                severity_distribution['medium'] += 1
            else:
                severity_distribution['low'] += 1
        
        error_count = len([e for e in entries if e['severity'] >= 7])
        
        return {
            'lines_per_second': len(entries) / (time.time() - self.start_time) if hasattr(self, 'start_time') else 0,
            'errors_per_1000_lines': (error_count / len(entries)) * 1000 if entries else 0,
            'severity_distribution': severity_distribution
        }
    
    def update_progress(self, value, message):
        """Update progress bar and message"""
        if not hasattr(self, 'start_time'):
            self.start_time = time.time()
        
        def update_ui():
            if MODERN_GUI:
                self.progress_bar.set(value)
            else:
                self.progress_bar['value'] = value * 100
            
            self.progress_label.configure(text=message)
            self.root.update_idletasks()
        
        self.root.after(0, update_ui)
    
    def display_results(self):
        """Display analysis results"""
        if not self.analysis_results:
            return
        
        results = self.analysis_results
        
        # Summary
        summary = f"""🏢 ENTERPRISE LOG ANALYSIS REPORT
{'═' * 60}

📄 File Information:
   • Name: {results['file_info']['name']}
   • Size: {results['file_info']['size']:,} bytes
   • Lines: {results['file_info']['total_lines']:,}

⚙️ Analysis Configuration:
   • Mode: {results['mode'].title()}
   • AI Model: {results['ai_model']}
   • Log Type: {results['log_type'].title()}
   • Processing Time: {results['analysis_time']:.2f} seconds
   • Performance: {results['performance_metrics']['lines_per_second']:.0f} lines/sec

📊 Findings Summary:
   • Errors Found: {len(results['errors'])}
   • Warnings Found: {len(results['warnings'])}
   • Root Causes: {len(results['root_causes'])}
   • Error Density: {results['performance_metrics']['errors_per_1000_lines']:.1f} per 1000 lines

🎯 Severity Distribution:
   • Critical: {results['performance_metrics']['severity_distribution']['critical']}
   • High: {results['performance_metrics']['severity_distribution']['high']}
   • Medium: {results['performance_metrics']['severity_distribution']['medium']}
   • Low: {results['performance_metrics']['severity_distribution']['low']}

📈 Error Patterns:"""
        
        if results['patterns']:
            for error_type, count in sorted(results['patterns'].items(), key=lambda x: x[1], reverse=True):
                summary += f"\n   • {error_type}: {count} occurrences"
        else:
            summary += "\n   • No error patterns detected - System appears stable"
        
        summary += f"\n\n💡 Analysis Quality: {'Excellent' if len(results['errors']) > 0 else 'Good'}"
        
        # Update summary tab
        if 'summary' in self.tab_textboxes:
            self.tab_textboxes['summary'].delete("1.0", "end")
            self.tab_textboxes['summary'].insert("1.0", summary)
        
        # Root Causes
        causes_text = "🎯 COMPREHENSIVE ROOT CAUSE ANALYSIS\n" + "═" * 60 + "\n\n"
        
        if results['root_causes']:
            for i, cause in enumerate(results['root_causes'], 1):
                severity_icon = "🔴" if cause['severity'] == 'Critical' else "🟡" if cause['severity'] == 'High' else "🟢"
                
                causes_text += f"{i}. {severity_icon} {cause['title']}\n"
                causes_text += f"   📊 Confidence: {cause['confidence']:.1%}\n"
                causes_text += f"   📈 Severity: {cause['severity']}\n"
                causes_text += f"   📝 Description: {cause['description']}\n"
                
                # Display causal chain if available
                if 'causal_chain' in cause:
                    causes_text += f"   🔗 Causal Chain:\n"
                    causes_text += f"      {cause['causal_chain']}\n"
                
                causes_text += f"   🛠️ Recommendations:\n"
                
                for rec in cause['recommendations']:
                    causes_text += f"      • {rec}\n"
                causes_text += "\n"
        else:
            causes_text += "✅ No systematic root causes identified.\n"
            causes_text += "   System appears to be operating within normal parameters.\n"
            causes_text += "   Detected issues appear to be isolated incidents.\n"
        
        if 'root causes' in self.tab_textboxes:
            self.tab_textboxes['root causes'].delete("1.0", "end")
            self.tab_textboxes['root causes'].insert("1.0", causes_text)
        
        # Timeline
        timeline_text = "⏱️ CRITICAL EVENT TIMELINE\n" + "═" * 50 + "\n\n"
        
        high_severity_events = [e for e in results['entries'] if e['severity'] >= 6]
        high_severity_events.sort(key=lambda x: x['timestamp'])
        
        if high_severity_events:
            for event in high_severity_events[:25]:  # Show top 25 events
                severity_icon = "🔴" if event['severity'] >= 9 else "🟡" if event['severity'] >= 7 else "🟠"
                time_str = event['timestamp'].strftime('%H:%M:%S')
                
                timeline_text += f"{severity_icon} [{time_str}] {event['level']} (Line {event['line']})\n"
                timeline_text += f"   📄 {event['message'][:120]}{'...' if len(event['message']) > 120 else ''}\n"
                timeline_text += f"   ⚡ Severity: {event['severity']:.1f}/10\n\n"
        else:
            timeline_text += "✅ No high-severity events detected in the timeline.\n"
            timeline_text += "   System appears to be operating normally.\n"
        
        if 'timeline' in self.tab_textboxes:
            self.tab_textboxes['timeline'].delete("1.0", "end")
            self.tab_textboxes['timeline'].insert("1.0", timeline_text)
        
        # Enable export buttons
        if MODERN_GUI:
            self.export_json_btn.configure(state="normal")
            self.export_report_btn.configure(state="normal")
        else:
            self.export_json_btn.configure(state="normal")
            self.export_report_btn.configure(state="normal")
        
        # Hide progress and re-enable analysis
        if MODERN_GUI:
            self.progress_frame.pack_forget()
            self.analyze_btn.configure(state="normal")
        else:
            self.progress_frame.pack_forget()
            self.analyze_btn.configure(state="normal")
    
    def export_results(self, format_type):
        """Export analysis results"""
        if not self.analysis_results:
            messagebox.showerror("Error", "No analysis results to export.")
            return
        
        if format_type == "json":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                title="Save Analysis as JSON"
            )
            
            if file_path:
                try:
                    # Prepare data for JSON serialization
                    export_data = dict(self.analysis_results)
                    # Convert datetime objects to strings
                    for entry in export_data['entries']:
                        entry['timestamp'] = entry['timestamp'].isoformat()
                    
                    with open(file_path, 'w') as f:
                        json.dump(export_data, f, indent=2)
                    
                    messagebox.showinfo("Success", f"Analysis exported to {file_path}")
                except Exception as e:
                    messagebox.showerror("Export Error", f"Failed to export JSON:\n{str(e)}")
        
        elif format_type == "report":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                title="Save Analysis Report"
            )
            
            if file_path:
                try:
                    with open(file_path, 'w') as f:
                        # Write comprehensive report
                        f.write("ENTERPRISE LOG ANALYSIS REPORT\n")
                        f.write("=" * 60 + "\n\n")
                        
                        # Get content from all tabs
                        for tab_name, textbox in self.tab_textboxes.items():
                            if tab_name != "export":
                                f.write(f"\n{tab_name.upper()} SECTION\n")
                                f.write("-" * 40 + "\n")
                                content = textbox.get("1.0", "end-1c")
                                f.write(content)
                                f.write("\n\n")
                    
                    messagebox.showinfo("Success", f"Report exported to {file_path}")
                except Exception as e:
                    messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    app = UltimateLogAnalyzer()
    app.run()

if __name__ == "__main__":
    main()