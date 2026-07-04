import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Toplevel, simpledialog
import pandas as pd
import io
import threading
import os
import re
import logging
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Setup basic logging for error handling
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Attempt to import necessary libraries for advanced features
# Please install with:
# pip install fuzzywuzzy[speedup]
# pip install spacy
# python -m spacy download en_core_web_sm
# pip install scikit-learn nltk openpyxl xlrd
try:
    from fuzzywuzzy import fuzz
except ImportError:
    fuzz = None
    logging.warning("FuzzyWuzzy not found. Please install with: pip install fuzzywuzzy[speedup]")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not found. Semantic matching will be disabled. Install with: pip install spacy && python -m spacy download en_core_web_sm")

try:
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    import nltk
    # Check if NLTK data is downloaded and if not, download it
    NLTK_AVAILABLE = True
    try:
        nltk.data.find('corpora/stopwords')
        nltk.data.find('corpora/wordnet')
    except LookupError:
        logging.info("NLTK data not found. Attempting to download...")
        try:
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            logging.info("NLTK data downloaded successfully.")
        except Exception as e:
            NLTK_AVAILABLE = False
            logging.error(f"Failed to download NLTK data. Advanced preprocessing will be disabled. Error: {e}")
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not found. Advanced preprocessing will be disabled. Please install with: pip install nltk")

try:
    import openpyxl
    import xlrd
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    logging.warning("openpyxl or xlrd not found. Excel file support will be disabled. Please install with: pip install openpyxl xlrd")

try:
    import fuzzy
    PHONETIC_AVAILABLE = True
except ImportError:
    PHONETIC_AVAILABLE = False

# Add these dictionaries to your class or as class variables
ACRONYM_DICT = {
    "n't": "not",
    "i'm": "i am",
    "let's": "let us",
    "usa": "united states",
    "uk": "united kingdom",
    # Add more as needed
}
SYNONYM_DICT = {
    "buy": "purchase",
    "big": "large",
    "small": "little",
    # Add more as needed
}

class DataMatcherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sophisticated Data Matcher")
        # Maximize window for best fit on all screens
        try:
            self.state('zoomed')  # Windows
        except Exception:
            self.attributes('-zoomed', True)  # Linux/Mac fallback

        # Define a dark theme color palette
        self.bg_color = "#1f1f1f"
        self.frame_bg_color = "#2c2c2c"
        self.btn_color = "#61dafb"
        self.btn_active_color = "#00b8d4"
        self.fg_color = "#ffffff"
        self.header_font = ("Helvetica", 16, "bold")
        self.label_font = ("Helvetica", 12)
        
        self.source_df = None
        self.target_df = None
        self.results_df = None
        self.spacy_model = None
        self.lemmatizer = WordNetLemmatizer() if NLTK_AVAILABLE else None
        self.stopwords = set(stopwords.words('english')) if NLTK_AVAILABLE else set()
        self.secondary_source_vars = {}
        self.secondary_target_vars = {}
        self.is_matching = False

        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure("TFrame", background=self.frame_bg_color)
        self.style.configure("TLabel", background=self.frame_bg_color, foreground=self.fg_color)
        self.style.configure("TCheckbutton", background=self.frame_bg_color, foreground=self.fg_color)
        self.style.map("TCheckbutton", background=[('active', self.frame_bg_color)], foreground=[('disabled', '#666666')])
        self.style.configure("TCombobox", fieldbackground="#444444", background="#444444", foreground=self.fg_color)
        self.style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'), background="#444444", foreground=self.fg_color)
        self.style.configure("Treeview", font=('Helvetica', 10), rowheight=25, background="#333333", foreground=self.fg_color, fieldbackground="#333333")
        self.style.configure("TPanedwindow", background=self.bg_color)
        self.style.configure("TPanedwindow.Sash", background=self.frame_bg_color, sashthickness=6)
        self.style.map('Treeview', background=[('selected', '#555555')])

        self.configure(bg=self.bg_color)
        self.create_widgets()

        # Defer model loading to avoid startup crash due to network/SSL issues
        self.sentence_model = None
        self.ml_model = None  # Will be set after training

    def create_widgets(self):
        """Builds the main UI layout and widgets."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main vertical PanedWindow to separate top (input) and bottom (controls/results)
        main_v_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_v_pane.grid(row=0, column=0, sticky="nsew")

        # Top section for data input
        data_input_frame = tk.Frame(main_v_pane, bg=self.bg_color, padx=10, pady=10)
        main_v_pane.add(data_input_frame, weight=1)  # Add to vertical pane, smaller initial size

        data_input_frame.grid_columnconfigure(0, weight=1)
        data_input_frame.grid_columnconfigure(1, weight=1)
        data_input_frame.grid_rowconfigure(0, weight=1)

        source_frame = tk.Frame(data_input_frame, bg=self.frame_bg_color, padx=10, pady=10)
        source_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        data_input_frame.grid_rowconfigure(0, weight=1)
        tk.Label(source_frame, text="Source Data (Paste or Load)", font=self.label_font, bg=self.frame_bg_color, fg=self.fg_color).pack(pady=5)
        self.source_text = tk.Text(source_frame, height=10, wrap="none", bg="#444444", fg=self.fg_color, insertbackground=self.fg_color, relief="flat")
        self.source_text.pack(fill=tk.BOTH, expand=True)
        source_scroll_x = ttk.Scrollbar(source_frame, orient=tk.HORIZONTAL, command=self.source_text.xview)
        self.source_text.configure(xscrollcommand=source_scroll_x.set)
        source_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        filetypes_source = [("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("TSV files", "*.tsv"), ("All files", "*.*")]
        self.source_file_button = tk.Button(source_frame, text="Load Source from File", command=lambda: self.load_data_from_file("source", filetypes_source), bg=self.btn_color, fg="#1f1f1f", font=self.label_font, relief="flat", bd=0, activebackground=self.btn_active_color)
        self.source_file_button.pack(pady=5)

        target_frame = tk.Frame(data_input_frame, bg=self.frame_bg_color, padx=10, pady=10)
        target_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        tk.Label(target_frame, text="Target Data (Paste or Load)", font=self.label_font, bg=self.frame_bg_color, fg=self.fg_color).pack(pady=5)
        self.target_text = tk.Text(target_frame, height=10, wrap="none", bg="#444444", fg=self.fg_color, insertbackground=self.fg_color, relief="flat")
        self.target_text.pack(fill=tk.BOTH, expand=True)
        target_scroll_x = ttk.Scrollbar(target_frame, orient=tk.HORIZONTAL, command=self.target_text.xview)
        self.target_text.configure(xscrollcommand=target_scroll_x.set)
        target_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        filetypes_target = [("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("TSV files", "*.tsv"), ("All files", "*.*")]
        self.target_file_button = tk.Button(target_frame, text="Load Target from File", command=lambda: self.load_data_from_file("target", filetypes_target), bg=self.btn_color, fg="#1f1f1f", font=self.label_font, relief="flat", bd=0, activebackground=self.btn_active_color)
        self.target_file_button.pack(pady=5)

        # Bottom horizontal PanedWindow for Controls and Results
        bottom_h_pane = ttk.PanedWindow(main_v_pane, orient=tk.HORIZONTAL)
        main_v_pane.add(bottom_h_pane, weight=4) # Give more space to this pane

        # Controls section - Made scrollable to fit on all screen sizes
        outer_control_frame = tk.Frame(bottom_h_pane, bg=self.bg_color)
        bottom_h_pane.add(outer_control_frame, weight=1) # Add to horizontal pane, smaller initial size
        outer_control_frame.grid_rowconfigure(0, weight=1)
        outer_control_frame.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(outer_control_frame, bg=self.bg_color, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(outer_control_frame, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        control_frame = tk.Frame(canvas, bg=self.bg_color, padx=10)
        control_frame_id = canvas.create_window((0, 0), window=control_frame, anchor="nw")

        def on_frame_configure(event):
            # Update the scroll region to encompass the inner frame
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            # Resize the inner frame to match the canvas width
            canvas.itemconfig(control_frame_id, width=event.width)

        control_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        tk.Label(control_frame, text="Matching Controls", font=self.header_font, bg=self.bg_color, fg=self.fg_color).pack(pady=(0, 10))

        self.load_button = tk.Button(control_frame, text="Load Data from Text", command=self.load_data, bg=self.btn_color, fg="#1f1f1f", font=self.label_font, relief="flat", bd=0, activebackground=self.btn_active_color)
        self.load_button.pack(fill=tk.X, pady=5)

        # Matching methods checkboxes
        match_method_frame = tk.LabelFrame(control_frame, text="Matching Methods", font=self.label_font, bg=self.frame_bg_color, fg=self.fg_color, padx=10, pady=5)
        match_method_frame.pack(fill=tk.X, pady=(10, 5))
        
        self.fuzzy_var = tk.IntVar(value=1)
        self.semantic_var = tk.IntVar(value=0)
        self.jaccard_var = tk.IntVar(value=0)
        self.cosine_var = tk.IntVar(value=0)
        self.phonetic_var = tk.IntVar(value=0)
        self.ml_var = tk.IntVar(value=0)
        
        if fuzz:
            ttk.Checkbutton(match_method_frame, text="Fuzzy Matching", variable=self.fuzzy_var).pack(anchor="w")
        ttk.Checkbutton(match_method_frame, text="AI/Semantic Matching", variable=self.semantic_var, state=tk.NORMAL if SPACY_AVAILABLE else tk.DISABLED).pack(anchor="w")
        ttk.Checkbutton(match_method_frame, text="Jaccard Similarity", variable=self.jaccard_var).pack(anchor="w")
        ttk.Checkbutton(match_method_frame, text="Cosine Similarity", variable=self.cosine_var).pack(anchor="w")
        ttk.Checkbutton(match_method_frame, text="Phonetic Matching", variable=self.phonetic_var).pack(anchor="w")
        self.ml_checkbox = ttk.Checkbutton(match_method_frame, text="ML Model Matching", variable=self.ml_var, state=tk.DISABLED)
        self.ml_checkbox.pack(anchor="w")

        # Text preprocessing checkbox
        preprocessing_frame = tk.LabelFrame(control_frame, text="Text Preprocessing", font=self.label_font, bg=self.frame_bg_color, fg=self.fg_color, padx=10, pady=5)
        preprocessing_frame.pack(fill=tk.X, pady=5)
        self.preprocess_var = tk.IntVar(value=1)
        ttk.Checkbutton(preprocessing_frame, text="Enable Preprocessing", variable=self.preprocess_var, state=tk.NORMAL if NLTK_AVAILABLE else tk.DISABLED).pack(anchor="w")
        
        # Threshold section
        threshold_frame = tk.Frame(control_frame, bg=self.bg_color)
        threshold_frame.pack(anchor="w", pady=(5, 10))
        tk.Label(threshold_frame, text="Threshold:", bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        self.min_threshold_entry = tk.Entry(threshold_frame, width=5, bg="#444444", fg=self.fg_color, insertbackground=self.fg_color, relief="flat")
        self.min_threshold_entry.insert(0, "70")
        self.min_threshold_entry.pack(side=tk.LEFT, padx=(5, 0))
        tk.Label(threshold_frame, text="to", bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        self.max_threshold_entry = tk.Entry(threshold_frame, width=5, bg="#444444", fg=self.fg_color, insertbackground=self.fg_color, relief="flat")
        self.max_threshold_entry.insert(0, "100")
        self.max_threshold_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Column selection frame for primary and secondary columns
        self.column_selection_frame = tk.LabelFrame(control_frame, text="Select Columns to Match", font=self.label_font, bg=self.frame_bg_color, fg=self.fg_color, padx=10, pady=10)
        self.column_selection_frame.pack(pady=10, fill=tk.X)

        tk.Label(self.column_selection_frame, text="Primary Match Column", font=self.label_font, bg=self.frame_bg_color, fg=self.fg_color).pack(pady=(0, 5))
        primary_frame = tk.Frame(self.column_selection_frame, bg=self.frame_bg_color)
        primary_frame.pack()
        tk.Label(primary_frame, text="Source:", bg=self.frame_bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        self.source_primary_col = ttk.Combobox(primary_frame, state="readonly", width=15)
        self.source_primary_col.pack(side=tk.LEFT, padx=5)
        tk.Label(primary_frame, text="Target:", bg=self.frame_bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        self.target_primary_col = ttk.Combobox(primary_frame, state="readonly", width=15)
        self.target_primary_col.pack(side=tk.LEFT, padx=5)

        tk.Label(self.column_selection_frame, text="Secondary Columns (for combined matching)", font=self.label_font, bg=self.frame_bg_color, fg=self.fg_color).pack(pady=(10, 5))
        self.secondary_source_frame = tk.Frame(self.column_selection_frame, bg=self.frame_bg_color)
        self.secondary_source_frame.pack(fill=tk.X)
        self.secondary_target_frame = tk.Frame(self.column_selection_frame, bg=self.frame_bg_color)
        self.secondary_target_frame.pack(fill=tk.X)
        
        self.run_button = tk.Button(control_frame, text="Run Match", command=self.start_matching_thread, bg=self.btn_color, fg="#1f1f1f", font=self.header_font, relief="flat", bd=0, activebackground=self.btn_active_color, state=tk.DISABLED)
        self.run_button.pack(fill=tk.X, pady=15)
        
        self.progressbar = ttk.Progressbar(control_frame, orient=tk.HORIZONTAL, length=200, mode='determinate', style="TProgressbar")
        self.progressbar.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(control_frame, text="", font=("Helvetica", 10, "italic"), bg=self.bg_color, fg="#666666")
        self.status_label.pack(pady=(5, 0))
        
        # New buttons for user feedback and download
        self.feedback_button = tk.Button(control_frame, text="Manual Match Review", command=self.open_feedback_window, state=tk.DISABLED, bg=self.btn_color, fg="#1f1f1f", font=self.label_font, relief="flat", bd=0, activebackground=self.btn_active_color)
        self.feedback_button.pack(fill=tk.X, pady=5)
        
        # New button to train the ML model
        self.train_ml_button = tk.Button(control_frame, text="Train ML Model", command=self.train_model_from_file, bg=self.btn_color, fg="#1f1f1f", font=self.label_font, relief="flat", bd=0, activebackground=self.btn_active_color)
        self.train_ml_button.pack(fill=tk.X, pady=5)

        # New button to load a review file directly
        review_filetypes = [("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")]
        self.load_review_button = tk.Button(control_frame, text="Load Data for Review", command=self.load_review_data, bg=self.btn_color, fg="#1f1f1f", font=self.label_font, relief="flat", bd=0, activebackground=self.btn_active_color)
        self.load_review_button.pack(fill=tk.X, pady=5)

        self.download_button = tk.Button(control_frame, text="Download Results as CSV", command=self.download_results, state=tk.DISABLED, bg=self.btn_color, fg="#1f1f1f", font=self.label_font, relief="flat", bd=0, activebackground=self.btn_active_color)
        self.download_button.pack(fill=tk.X, pady=5)
        
        # Results section
        result_frame = tk.Frame(bottom_h_pane, bg=self.bg_color, padx=10, pady=10)
        bottom_h_pane.add(result_frame, weight=3) # Add to horizontal pane, larger initial size
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        tk.Label(result_frame, text="Matching Results", font=self.header_font, bg=self.bg_color, fg=self.fg_color).grid(row=0, column=0, sticky="ew", pady=5)
        self.tree = ttk.Treeview(result_frame)
        self.tree.grid(row=1, column=0, sticky="nsew")
        tree_scroll_y = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll_y.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=tree_scroll_y.set)
        tree_scroll_x = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        tree_scroll_x.grid(row=2, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=tree_scroll_x.set)

    def expand_acronym(self, token):
        """Expand common acronyms."""
        return ACRONYM_DICT.get(token, token)

    def replace_synonym(self, token):
        """Replace words with their synonyms."""
        return SYNONYM_DICT.get(token, token)

    def soundex(self, word):
        """Simple Soundex implementation for phonetic matching."""
        word = str(word).upper()
        codes = ("BFPV", "CGJKQSXZ", "DT", "L", "MN", "R")
        soundex_val = ""
        if not word:
            return ""
        soundex_val += word[0]
        last_code = ""
        for char in word[1:]:
            for idx, group in enumerate(codes, 1):
                if char in group:
                    code = str(idx)
                    if code != last_code:
                        soundex_val += code
                    last_code = code
                    break
            else:
                last_code = "" # Reset for non-mappable chars like vowels
        soundex_val = soundex_val.replace("0", "")
        return (soundex_val + "000")[:4]

    def jaccard_similarity(self, a, b):
        """Jaccard similarity between two strings."""
        set_a = set(str(a).split())
        set_b = set(str(b).split())
        intersection = set_a & set_b
        union = set_a | set_b
        return float(len(intersection)) / len(union) if union else 0.0

    def load_data(self):
        """Parses data from text boxes and populates column menus and checkboxes."""
        if self.is_matching: return # Prevent reload during matching
        try:
            source_data = self.source_text.get("1.0", tk.END).strip()
            target_data = self.target_text.get("1.0", tk.END).strip()
            
            if not source_data or not target_data:
                messagebox.showerror("Error", "Please paste data into both the Source and Target lists.")
                logging.error("Data loading failed: one or both text areas were empty.")
                return

            self.source_df = pd.read_csv(io.StringIO(source_data), sep='\t') if '\t' in source_data else pd.read_csv(io.StringIO(source_data))
            self.target_df = pd.read_csv(io.StringIO(target_data), sep='\t') if '\t' in target_data else pd.read_csv(io.StringIO(target_data))
            
            self.update_column_widgets(list(self.source_df.columns), list(self.target_df.columns))
            self.run_button.config(state=tk.NORMAL)
            logging.info("Data loaded successfully.")
            messagebox.showinfo("Success", "Data loaded and columns are ready for selection.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not parse data. Please ensure it's a valid CSV or TSV format.\nError: {e}")
            logging.error(f"Error during data loading: {e}", exc_info=True)
            self.run_button.config(state=tk.DISABLED)

    def load_data_from_file(self, data_type, filetypes):
        """Loads data from a file into the specified text box."""
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if not file_path:
            return

        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                if not EXCEL_AVAILABLE:
                    messagebox.showerror("Error", "Excel support libraries (openpyxl, xlrd) not found. Please install them.")
                    return
                df = pd.read_excel(file_path)
                content = df.to_csv(index=False)
            else: # Assuming CSV/TSV
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            if data_type == "source":
                self.source_text.delete("1.0", tk.END)
                self.source_text.insert("1.0", content)
            elif data_type == "target":
                self.target_text.delete("1.0", tk.END)
                self.target_text.insert("1.0", content)
            
            messagebox.showinfo("File Loaded", f"{data_type.capitalize()} data successfully loaded from file.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file.\nError: {e}")
            logging.error(f"Error loading {data_type} file: {e}", exc_info=True)

    def load_review_data(self):
        """Allows the user to load a previously saved results file for manual review."""
        if not EXCEL_AVAILABLE:
            messagebox.showerror("Error", "Excel support libraries (openpyxl, xlrd) not found. Please install them to load a file for review.")
            return

        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                loaded_df = pd.read_excel(file_path)
            else: # Assuming CSV
                loaded_df = pd.read_csv(file_path)

            if 'Status' not in loaded_df.columns:
                messagebox.showwarning("Invalid File", "The loaded file does not appear to be a matching results file. It must contain a 'Status' column.")
                return

            self.results_df = loaded_df
            self.display_results()
            self.feedback_button.config(state=tk.NORMAL)
            self.download_button.config(state=tk.NORMAL)
            messagebox.showinfo("Review File Loaded", "Matching results file loaded successfully for manual review.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file for review. Error: {e}")
            logging.error(f"Error loading review file: {e}", exc_info=True)


    def update_column_widgets(self, source_cols, target_cols):
        """Populates the column dropdowns and checkboxes with available columns."""
        self.source_primary_col["values"] = source_cols
        self.target_primary_col["values"] = target_cols
        if source_cols: self.source_primary_col.set(source_cols[0])
        if target_cols: self.target_primary_col.set(target_cols[0])

        for widget in self.secondary_source_frame.winfo_children(): widget.destroy()
        for widget in self.secondary_target_frame.winfo_children(): widget.destroy()
        
        self.secondary_source_vars = {}
        for col in source_cols:
            var = tk.IntVar()
            cb = ttk.Checkbutton(self.secondary_source_frame, text=col, variable=var)
            cb.pack(side=tk.LEFT, padx=5)
            self.secondary_source_vars[col] = var
        
        self.secondary_target_vars = {}
        for col in target_cols:
            var = tk.IntVar()
            cb = ttk.Checkbutton(self.secondary_target_frame, text=col, variable=var)
            cb.pack(side=tk.LEFT, padx=5)
            self.secondary_target_vars[col] = var

    def preprocess_text(self, text):
        """ Applies data cleaning and normalization steps. This includes lowercasing, punctuation removal, stop word removal, and lemmatization. This function handles the 'Data Cleaning and Normalization' strategy. """
        text = str(text).lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        tokens = text.split()
        tokens = [t for t in tokens if t not in self.stopwords]
        tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
        # Optionally add acronym/synonym expansion here
        return ' '.join(tokens)

    def start_matching_thread(self):
        """Starts the matching process in a separate thread to keep the GUI responsive."""
        if self.source_df is None or self.target_df is None:
            messagebox.showerror("Error", "Please load the data first.")
            logging.error("Attempted to start matching without loading data.")
            return

        self.is_matching = True
        self.run_button.config(state=tk.DISABLED, text="Matching...")
        self.load_button.config(state=tk.DISABLED)
        self.source_file_button.config(state=tk.DISABLED)
        self.target_file_button.config(state=tk.DISABLED)
        self.train_ml_button.config(state=tk.DISABLED)
        self.download_button.config(state=tk.DISABLED)
        self.feedback_button.config(state=tk.DISABLED)
        self.status_label.config(text="Processing data...")
        self.progressbar.stop()
        self.progressbar['value'] = 0
        self.clear_results()
        
        matching_thread = threading.Thread(target=self.run_matching)
        matching_thread.daemon = True
        matching_thread.start()

    def load_spacy_model(self):
        """Loads a spaCy model for semantic matching."""
        self.status_label.config(text="Loading AI model (this may take a moment)...")
        self.update_idletasks()
        try:
            self.spacy_model = spacy.load("en_core_web_sm")
            self.status_label.config(text="AI model loaded.")
            logging.info("spaCy model loaded successfully.")
        except OSError:
            self.status_label.config(text="Error: spaCy model 'en_core_web_sm' not found.")
            messagebox.showerror("Model Error", "The spaCy model 'en_core_web_sm' is not installed. Please run 'python -m spacy download en_core_web_sm' in your terminal.")
            self.spacy_model = None
            logging.error("Failed to load spaCy model 'en_core_web_sm'.", exc_info=True)

    def _ensure_models_loaded(self, needs_spacy=False, needs_sentence_transformer=False):
        """Checks and loads required AI models, returns True if successful."""
        if needs_spacy and not self.spacy_model:
            self.load_spacy_model()  # This method already exists and shows errors
            if not self.spacy_model:
                return False

        if needs_sentence_transformer and not self.sentence_model:
            try:
                self.status_label.config(text="Loading Sentence Transformer model (first time only)...")
                self.update_idletasks()
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.status_label.config(text="Sentence Transformer model loaded.")
                logging.info("Sentence Transformer model loaded successfully.")
            except Exception as e:
                error_message = f"Failed to load Sentence Transformer model.\nError: {e}"
                if "SSL: CERTIFICATE_VERIFY_FAILED" in str(e):
                    error_message = (
                        "Failed to download Sentence Transformer model due to an SSL certificate error. "
                        "This is common on corporate networks.\n\n"
                        "ML-based features will be unavailable until this is resolved."
                    )
                messagebox.showerror("Model Loading Error", error_message)
                logging.error(f"Failed to load Sentence Transformer model: {e}", exc_info=True)
                self.sentence_model = None
                return False
        
        return True

    def compute_similarity(self, source_text, target_text):
        """Computes various similarity scores between two texts, robust to missing models."""
        scores = {}
        if fuzz:
            scores['fuzzy_score'] = fuzz.ratio(source_text, target_text)
        if self.spacy_model:
            source_doc = self.spacy_model(source_text)
            target_doc = self.spacy_model(target_text)
            sim = source_doc.similarity(target_doc)
            scores['semantic_score'] = (sim * 100) if sim is not None and np.isfinite(sim) else 0
        if self.sentence_model:
            source_embedding = self.sentence_model.encode([str(source_text)])
            target_embedding = self.sentence_model.encode([str(target_text)])
            scores['sentence_score'] = cosine_similarity(source_embedding, target_embedding)[0][0] * 100
        return scores

    def run_matching(self):
        """
        Executes the data matching logic and displays the results. This function uses a ThreadPoolExecutor
        for efficient, batched processing, addressing the 'Batch Processing' strategy.
        """
        try:
            # Determine which models are needed BEFORE getting selected methods
            needs_spacy = self.semantic_var.get() == 1 or self.ml_var.get() == 1
            needs_sentence_transformer = self.ml_var.get() == 1

            if not self._ensure_models_loaded(needs_spacy, needs_sentence_transformer):
                messagebox.showwarning("Matching Aborted", "One or more required AI models failed to load. Please check the logs.")
                # The finally block will still run to re-enable buttons
                return

            selected_methods = []
            if self.fuzzy_var.get() == 1 and fuzz:
                selected_methods.append("fuzzy")
            if self.semantic_var.get() == 1 and SPACY_AVAILABLE:
                selected_methods.append("semantic")
            if self.jaccard_var.get() == 1:
                selected_methods.append("jaccard")
            if self.cosine_var.get() == 1:
                selected_methods.append("tfidf") # Internally we use TF-IDF for cosine
            if self.phonetic_var.get() == 1 and PHONETIC_AVAILABLE:
                selected_methods.append("phonetic")
            # Assuming ML model is trained and available as self.ml_model
            if self.ml_var.get() == 1 and hasattr(self, 'ml_model'):
                selected_methods.append("ml")

            if not selected_methods:
                messagebox.showwarning("Warning", "Please select at least one matching method.")
                return

            min_threshold = int(self.min_threshold_entry.get())
            max_threshold = int(self.max_threshold_entry.get())
            if not (0 <= min_threshold <= 100 and 0 <= max_threshold <= 100 and min_threshold <= max_threshold):
                messagebox.showerror("Error", "Please enter a valid threshold range (0-100).")
                return

            source_col = self.source_primary_col.get()
            target_col = self.target_primary_col.get()
            
            # Additional columns for combined matching
            secondary_source_cols = [col for col, var in self.secondary_source_vars.items() if var.get() == 1]
            secondary_target_cols = [col for col, var in self.secondary_target_vars.items() if var.get() == 1]
            
            if not source_col or not target_col:
                messagebox.showerror("Error", "Please select a primary column for both source and target data.")
                return

            # Pre-process the columns to be matched
            self.status_label.config(text="Preprocessing data...")
            self.update_idletasks()

            source_df_copy = self.source_df.copy()
            target_df_copy = self.target_df.copy()
            
            source_df_copy['search_text'] = source_df_copy[source_col].astype(str)
            target_df_copy['search_text'] = target_df_copy[target_col].astype(str)

            for col in secondary_source_cols:
                source_df_copy['search_text'] += ' ' + source_df_copy[col].astype(str)

            for col in secondary_target_cols:
                target_df_copy['search_text'] += ' ' + target_df_copy[col].astype(str)

            # Apply text preprocessing
            if self.preprocess_var.get() and NLTK_AVAILABLE:
                source_df_copy['search_text'] = source_df_copy['search_text'].apply(self.preprocess_text)
                target_df_copy['search_text'] = target_df_copy['search_text'].apply(self.preprocess_text)
            
            self.status_label.config(text="Matching in progress...")
            self.update_idletasks()
            
            # Using ThreadPoolExecutor for concurrent matching
            results = []
            total_targets = len(target_df_copy)
            
            with ThreadPoolExecutor(max_workers=os.cpu_count() or 1) as executor:
                futures = {executor.submit(self.find_best_match, source_row, target_df_copy, min_threshold, max_threshold, selected_methods): source_row for _, source_row in source_df_copy.iterrows()}
                
                for i, future in enumerate(futures):
                    try:
                        results.append(future.result())
                        progress = int((i + 1) / len(futures) * 100)
                        self.progressbar['value'] = progress
                        self.status_label.config(text=f"Matching in progress... {progress}% done.")
                        self.update_idletasks()
                    except Exception as e:
                        logging.error(f"Error processing a match: {e}", exc_info=True)
                        results.append(None)

            self.results_df = pd.DataFrame([r for r in results if r is not None])
            
            if self.results_df.empty:
                messagebox.showinfo("No Matches", "No matches were found within the specified criteria.")
                self.status_label.config(text="Matching complete. No matches found.")
            else:
                self.display_results()
                self.status_label.config(text="Matching complete. Results displayed.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during matching: {e}")
            logging.error(f"Error during matching process: {e}", exc_info=True)
        finally:
            self.is_matching = False
            self.run_button.config(state=tk.NORMAL, text="Run Match")
            self.load_button.config(state=tk.NORMAL)
            self.source_file_button.config(state=tk.NORMAL)
            self.target_file_button.config(state=tk.NORMAL)
            self.train_ml_button.config(state=tk.NORMAL)
            self.download_button.config(state=tk.NORMAL if not self.results_df.empty else tk.DISABLED)
            self.feedback_button.config(state=tk.NORMAL if not self.results_df.empty else tk.DISABLED)

    def train_model_from_file(self):
        """Loads a labeled CSV/Excel file and trains the ML model."""
        file_path = filedialog.askopenfilename(
            title="Select Labeled Data File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            # Training requires both models for feature generation
            if not self._ensure_models_loaded(needs_spacy=True, needs_sentence_transformer=True):
                messagebox.showerror("Training Failed", "Could not load required AI models for training.")
                return

            if file_path.endswith('.csv'):
                labeled_data = pd.read_csv(file_path)
            else:
                labeled_data = pd.read_excel(file_path)

            # Expecting columns 'Source_Original', 'Target_Original', and 'Status' (with 'Approved' as positive label)
            required_cols = ['Source_Original', 'Target_Original', 'Status']
            if not all(col in labeled_data.columns for col in required_cols):
                messagebox.showerror("Error", f"File must contain columns: {', '.join(required_cols)}")
                return

            # Convert 'Status' to a binary label (1 for 'Approved', 0 otherwise)
            labeled_data['label'] = (labeled_data['Status'] == 'Approved').astype(int)
            
            # Rename for consistency with training function
            labeled_data.rename(columns={'Source_Original': 'source_text', 'Target_Original': 'target_text'}, inplace=True)

            self.status_label.config(text="Training ML model...")
            self.update_idletasks()
            self.train_ml_model(labeled_data)
            self.status_label.config(text="ML model training complete.")
            messagebox.showinfo("Success", "ML Model has been trained and is ready to use.")
            self.ml_checkbox.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to train model from file: {e}")
            logging.error(f"Error during model training from file: {e}", exc_info=True)

    def train_ml_model(self, labeled_data):
        """Trains a RandomForest model on labeled data."""
        labeled_data['source_text'] = labeled_data['source_text'].apply(self.preprocess_text)
        labeled_data['target_text'] = labeled_data['target_text'].apply(self.preprocess_text)
        features = []
        # This now relies on the robust compute_similarity method
        for _, row in labeled_data.iterrows():
            sim = self.compute_similarity(row['source_text'], row['target_text'])
            features.append([sim.get('fuzzy_score', 0), sim.get('semantic_score', 0), sim.get('tfidf_score', 0), sim.get('sentence_score', 0)])
        X = np.array(features)
        y = labeled_data['label'].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        print(classification_report(y_test, y_pred))
        self.ml_model = model

    def find_best_match(self, source_row, target_df, min_threshold, max_threshold, selected_methods):
        """Finds the best match for a source entry within the target data using selected methods."""
        source_text_preprocessed = source_row['search_text']
        scores_df = pd.DataFrame(index=target_df.index)

        # --- Calculate scores for all selected methods ---
        if "semantic" in selected_methods:
            source_doc = self.spacy_model(source_text_preprocessed)
            scores_df['semantic'] = target_df['search_text'].apply(lambda x: source_doc.similarity(self.spacy_model(x)) * 100)
        if "fuzzy" in selected_methods:
            scores_df['fuzzy'] = target_df['search_text'].apply(lambda x: fuzz.ratio(source_text_preprocessed, x))
        if "jaccard" in selected_methods:
            scores_df['jaccard'] = target_df['search_text'].apply(lambda x: self.jaccard_similarity(source_text_preprocessed, x) * 100)
        if "tfidf" in selected_methods:
            all_texts = [source_text_preprocessed] + target_df['search_text'].tolist()
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            scores_df['tfidf'] = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0] * 100
        if "phonetic" in selected_methods:
            source_soundex = self.soundex(source_text_preprocessed)
            scores_df['phonetic'] = target_df['search_text'].apply(lambda x: 100 if self.soundex(x) == source_soundex else 0)
        if "ml" in selected_methods and self.ml_model:
            def ml_score_func(target_text):
                sim = self.compute_similarity(source_text_preprocessed, target_text)
                features = np.array([[sim.get('fuzzy_score', 0), sim.get('semantic_score', 0), sim.get('tfidf_score', 0), sim.get('sentence_score', 0)]]) # Ensure all features are present
                return self.ml_model.predict_proba(features)[0][1] * 100
            scores_df['ml'] = target_df['search_text'].apply(ml_score_func)

        if scores_df.empty:
            return self.create_unmatched_row(source_row)

        # Combine scores by taking the maximum score across all selected methods for each target row
        target_df['score'] = scores_df.max(axis=1)
        
        # Find the best match within the threshold range
        matches = target_df[(target_df['score'] >= min_threshold) & (target_df['score'] <= max_threshold)].sort_values(by='score', ascending=False)
        
        if not matches.empty:
            best_match = matches.iloc[0]
            best_score = best_match['score']
            
            # Prepare the result row for the output DataFrame
            result_row = {
                'Source_Original': source_row[self.source_primary_col.get()],
                'Target_Original': best_match[self.target_primary_col.get()],
                'Match_Score': best_score,
                'Status': 'Matched'
            }
            # Add other columns from the source and target dataframes
            for col in self.source_df.columns:
                result_row[f"Source_{col}"] = source_row[col]
            for col in self.target_df.columns:
                result_row[f"Target_{col}"] = best_match[col]
            
            return result_row
        else:
            return self.create_unmatched_row(source_row)

    def create_unmatched_row(self, source_row):
        # Return an unmatched row if no match is found
        unmatched_row = {
            'Source_Original': source_row[self.source_primary_col.get()],
            'Target_Original': None,
            'Match_Score': None,
            'Status': 'Unmatched'
        }
        for col in self.source_df.columns:
            unmatched_row[f"Source_{col}"] = source_row[col]
        for col in self.target_df.columns:
            unmatched_row[f"Target_{col}"] = None # Set target columns to None for unmatched rows
        return unmatched_row


    def display_results(self):
        """Populates the Treeview widget with matching results."""
        if self.results_df is None or self.results_df.empty:
            self.clear_results()
            return

        self.clear_results()
        self.tree["columns"] = list(self.results_df.columns)
        self.tree["show"] = "headings"

        for col in self.results_df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor='w')

        for _, row in self.results_df.iterrows():
            self.tree.insert("", "end", values=list(row.values))

    def clear_results(self):
        """Clears the Treeview widget and resets its columns."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree["columns"] = []
        self.tree["show"] = "tree headings"

    def download_results(self):
        """Saves the results DataFrame to a CSV file."""
        if self.results_df is None or self.results_df.empty:
            messagebox.showwarning("No Data", "No results to download. Please run the matching process first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Matching Results"
        )
        
        if file_path:
            try:
                self.results_df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Results saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def open_feedback_window(self):
        """
        Opens a new Toplevel window for manual review of matched and unmatched results.
        This function implements the 'Manual Review and Feedback' strategy.
        """
        if self.results_df is None or self.results_df.empty:
            messagebox.showwarning("No Data", "Please run the matching process first or load a results file.")
            return

        win = Toplevel(self)
        win.title("Manual Match Review")
        win.configure(bg=self.bg_color)
        win.geometry("1000x800")
        
        # Create a copy of the results for this window
        review_df = self.results_df.copy()
        
        def save_changes(df_to_save):
            """Saves the approved/disapproved status back to the main dataframe."""
            # Use the index to update the main results_df
            self.results_df.loc[df_to_save.index, 'Status'] = df_to_save['Status']
            self.display_results() # Refresh the main treeview
            messagebox.showinfo("Changes Saved", "Your changes have been saved to the main results.")

        def update_status(event):
            """Updates the status of a selected row."""
            selected_item = tree_review.focus()
            if not selected_item:
                return

            current_status = tree_review.item(selected_item, "values")[-1]
            if current_status == "Matched":
                new_status = "Disapproved"
            elif current_status == "Unmatched":
                new_status = "Approved"
            else: # From Approved/Disapproved to original status
                new_status = "Matched" if "Source_Original" in review_df.columns else "Unmatched"
            
            # Find the row in the DataFrame by its index
            item_index = tree_review.index(selected_item)
            review_df.loc[review_df.index[item_index], 'Status'] = new_status
            
            # Update the treeview item
            values = list(tree_review.item(selected_item, "values"))
            values[-1] = new_status
            tree_review.item(selected_item, values=values)
            
            # Apply color tags
            tree_review.tag_configure("matched", background="light green")
            tree_review.tag_configure("unmatched", background="light coral")
            tree_review.tag_configure("approved", background="green")
            tree_review.tag_configure("disapproved", background="red")
            
            if new_status == "Matched":
                tree_review.item(selected_item, tags=("matched",))
            elif new_status == "Unmatched":
                tree_review.item(selected_item, tags=("unmatched",))
            elif new_status == "Approved":
                tree_review.item(selected_item, tags=("approved",))
            elif new_status == "Disapproved":
                tree_review.item(selected_item, tags=("disapproved",))

        def filter_view(status):
            """Filters the treeview based on the selected status."""
            for item in tree_review.get_children():
                tree_review.delete(item)

            if status is None: # Show all
                df_to_show = review_df
            else:
                df_to_show = review_df[review_df['Status'] == status]

            for _, row in df_to_show.iterrows():
                tree_review.insert("", "end", values=list(row.values), tags=(str(row['Status']).lower(),))
        
        def export_approved():
            """Exports approved rows to a new CSV file."""
            approved_df = review_df[review_df['Status'] == 'Approved']
            if approved_df.empty:
                messagebox.showwarning("No Data", "No approved rows to export.")
                return
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Approved Rows"
            )
            if file_path:
                try:
                    approved_df.to_csv(file_path, index=False)
                    messagebox.showinfo("Success", f"Approved rows saved to {file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {e}")
        
        def load_file_for_review():
            """Callback for the 'Load Data for Review' button in the review window."""
            self.load_review_data()
            win.destroy()

        # Review UI
        main_frame = tk.Frame(win, bg=self.frame_bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Buttons frame
        btn_frame = tk.Frame(win, bg=self.bg_color)
        btn_frame.pack(pady=5)
        
        # Add a new button to load files for review
        filetypes_review = [("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")]
        tk.Button(btn_frame, text="Load Data from File", command=load_file_for_review, bg=self.btn_color, fg="#1f1f1f").pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Show All", command=lambda: filter_view(None), bg=self.btn_color, fg="#1f1f1f").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Show Matched", command=lambda: filter_view("Matched"), bg=self.btn_color, fg="#1f1f1f").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Show Unmatched", command=lambda: filter_view("Unmatched"), bg=self.btn_color, fg="#1f1f1f").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Show Approved", command=lambda: filter_view("Approved"), bg=self.btn_color, fg="#1f1f1f").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Show Disapproved", command=lambda: filter_view("Disapproved"), bg=self.btn_color, fg="#1f1f1f").pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Export Approved Rows", command=export_approved, bg=self.btn_color, fg="#1f1f1f").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=win.destroy, bg=self.btn_color, fg="#1f1f1f").pack(side=tk.LEFT, padx=5)

        tree_review = ttk.Treeview(main_frame)
        tree_review.pack(fill=tk.BOTH, expand=True)
        
        tree_review.bind("<Double-1>", update_status)  # Double-click to change status
        
        tree_review["columns"] = list(review_df.columns)
        tree_review["show"] = "headings"
        for col in review_df.columns:
            tree_review.heading(col, text=col)
            tree_review.column(col, width=100, anchor='w')

        for _, row in review_df.iterrows():
            tree_review.insert("", "end", values=list(row.values), tags=(str(row['Status']).lower(),))

        tree_review.tag_configure("matched", background="#e0ffe0")
        tree_review.tag_configure("unmatched", background="#ffe0e0")
        tree_review.tag_configure("approved", background="#c0ffc0")
        tree_review.tag_configure("disapproved", background="#ffc0c0")

if __name__ == "__main__":
    app = DataMatcherApp()
    app.mainloop()
