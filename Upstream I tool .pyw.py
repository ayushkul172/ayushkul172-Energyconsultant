import sys
import io
import PyQt5
import matplotlib
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QTabWidget, QMessageBox, QApplication, QStyle, QProgressBar, QTextEdit, QHBoxLayout,
    QDialog, QCalendarWidget, QDialogButtonBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# YOUR ORIGINAL IMPORTS, UNTOUCHED
import pandas as pd
import os
import time
from datetime import date, datetime, timedelta
from tkinter import Tk, Label, Button
from tkcalendar import Calendar
from selenium import webdriver
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
try:
    from dateutil.parser import parse as dateutil_parse
except ImportError:
    print("Warning: 'python-dateutil' library not found. Date parsing will be less robust.")
    print("Install it using: pip install python-dateutil")
    dateutil_parse = None
try:
    import requests
except ImportError:
    print("Warning: 'requests' library not found. Online year verification is disabled.")
    print("Install it using: pip install requests")
    requests = None
import re
import spacy
import numpy as np
from collections import Counter
from string import punctuation
import heapq
from sklearn.metrics.pairwise import cosine_similarity
from spacy.matcher import Matcher
import tkinter as tk
from tkinter import filedialog
from tqdm import tqdm
import spacy.cli

DARK_STYLESHEET = """
QWidget{
    background-color: #2c3e50;
    color: #ecf0f1;
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 14px;
}
QMainWindow {
    background-color: #2c3e50;
}
QTabWidget::pane {
    border-top: 2px solid #34495e;
    margin-top: -1px;
}
QTabBar::tab {
    background-color: #34495e;
    color: #ecf0f1;
    padding: 10px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #2c3e50;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #5d9cec; /* A bright blue for selected tab */
    color: #ffffff;
    font-weight: bold;
}
QTabBar::tab:hover {
    background-color: #4a627a;
}
QTabBar::tab:disabled {
    background-color: #2c3e50;
    color: #7f8c8d;
}
QLabel#TitleLabel {
    font-size: 28px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 10px;
}
QLabel#DescriptionLabel {
    font-size: 16px;
    color: #bdc3c7;
    margin-bottom: 20px;
}
QPushButton {
    background-color: #5d9cec;
    color: white;
    border-radius: 5px;
    padding: 12px 25px;
    font-weight: bold;
    border: none;
    min-width: 200px;
}
QPushButton:hover {
    background-color: #4a8cdb;
}
QPushButton:pressed {
    background-color: #3a7acb;
}
QPushButton:disabled {
    background-color: #34495e;
    color: #7f8c8d;
}
QProgressBar {
    border: 2px solid #34495e;
    border-radius: 5px;
    text-align: center;
    color: #ecf0f1;
    background-color: #34495e;
}
QProgressBar::chunk {
    background-color: #2ecc71;
    width: 10px;
    margin: 0.5px;
}
QTextEdit {
    background-color: #34495e;
    color: #ecf0f1;
    border: 1px solid #2c3e50;
    border-radius: 4px;
    font-family: "Consolas", "Courier New", monospace;
}
QMessageBox {
    background-color: #34495e;
}
QMessageBox QLabel {
    color: #ecf0f1;
}
QDialog {
    background-color: #34495e;
}
QCalendarWidget QToolButton {
    color: white;
    background-color: #5d9cec;
}
QCalendarWidget QMenu {
    background-color: #34495e;
}
QCalendarWidget QSpinBox {
    color: white;
    background-color: #34495e;
}
QCalendarWidget QHeaderView {
    background-color: #34495e;
}
QCalendarWidget QTableView {
    background-color: #2c3e50;
    color: white;
    alternate-background-color: #34495e;
}
"""

class DateRangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date Range")
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("Select Start Date:"))
        self.start_cal = QCalendarWidget(self)
        self.start_cal.setSelectedDate(QDate.currentDate().addMonths(-1))
        self.layout.addWidget(self.start_cal)
        self.layout.addWidget(QLabel("Select End Date:"))
        self.end_cal = QCalendarWidget(self)
        self.end_cal.setSelectedDate(QDate.currentDate())
        self.layout.addWidget(self.end_cal)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_dates(self):
        start_date = self.start_cal.selectedDate().toPyDate()
        end_date = self.end_cal.selectedDate().toPyDate()
        return start_date, end_date

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    output = pyqtSignal(str)
    results = pyqtSignal(dict)

    def __init__(self, task_function, *args, **kwargs):
        super().__init__()
        self.task_function = task_function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            # The task function is now expected to handle the 'worker' object itself
            self.task_function(self, *self.args, **self.kwargs)
        except Exception as e:
            import traceback
            self.output.emit(f"\n--- TASK ERROR --- \n{str(e)}\n{traceback.format_exc()}\n------------------")
        finally:
            self.finished.emit()

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Upstream News Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        self.set_app_icon()
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        news_tab = self.create_tab_ui(
            "News Gathering Module",
            "Gather news from Upstream Online within a selected date range.",
            "Start News Gathering",
            QStyle.SP_ArrowDown,
            self.start_news_gathering_process
        )
        self.tabs.addTab(news_tab, "News Gathering")
        self.gather_btn = news_tab.findChild(QPushButton)
        self.gather_progress = news_tab.findChild(QProgressBar)
        self.gather_log = news_tab.findChild(QTextEdit)
        ai_tab = self.create_tab_ui(
            "AI Analysis Engine",
            "Analyze gathered news to extract structured data.",
            "Run AI Analyzer",
            QStyle.SP_MediaPlay,
            self.start_ai_analyzer_process
        )
        self.tabs.addTab(ai_tab, "AI Analyzer")
        self.ai_btn = ai_tab.findChild(QPushButton)
        self.ai_progress = ai_tab.findChild(QProgressBar)
        self.ai_log = ai_tab.findChild(QTextEdit)
        self.dashboard_tab = self.create_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.setTabEnabled(2, False)

    def set_app_icon(self):
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

    def create_tab_ui(self, title, description, button_text, button_icon, on_click_method):
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setAlignment(Qt.AlignCenter)
        title_label = QLabel(title)
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        desc_label = QLabel(description)
        desc_label.setObjectName("DescriptionLabel")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        action_btn = QPushButton(button_text)
        action_btn.setIcon(self.style().standardIcon(button_icon))
        action_btn.setMinimumSize(300, 60)
        action_btn.clicked.connect(on_click_method)
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.hide()
        log_area = QTextEdit()
        log_area.setReadOnly(True)
        log_area.hide()
        layout.addStretch(1)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addSpacing(20)
        layout.addWidget(action_btn, 0, Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(progress_bar)
        layout.addWidget(log_area)
        layout.addStretch(2)
        return tab_widget

    def create_dashboard_tab(self):
        dashboard_widget = QWidget()
        main_layout = QVBoxLayout(dashboard_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        title_label = QLabel("AI Analysis Dashboard")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        self.status_chart_canvas = self.setup_chart_canvas()
        self.location_chart_canvas = self.setup_chart_canvas()
        self.type_chart_canvas = self.setup_chart_canvas()
        chart_layout = QHBoxLayout()
        chart_layout.addWidget(self.status_chart_canvas)
        chart_layout.addWidget(self.location_chart_canvas)
        chart_layout.addWidget(self.type_chart_canvas)
        main_layout.addLayout(chart_layout)
        return dashboard_widget

    def setup_chart_canvas(self):
        fig = Figure(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor('#2c3e50')
        return FigureCanvas(fig)

    def _run_task_in_thread(self, task_function, button, progress_bar, log_area, on_finish_slot, processing_text, *args, **kwargs):
        class EmittingStream(io.TextIOBase):
            def __init__(self, signal_emitter):
                super().__init__()
                self.text_written = ""
                self.signal_emitter = signal_emitter
            def write(self, text):
                # Buffer the text and emit when a newline is encountered
                self.text_written += text
                if '\n' in self.text_written:
                    self.signal_emitter.emit(self.text_written.strip())
                    self.text_written = ""
                return len(text)
            def flush(self):
                if self.text_written.strip():
                    self.signal_emitter.emit(self.text_written.strip())
                    self.text_written = ""

        button.setEnabled(False)
        button.setText(processing_text)
        progress_bar.setValue(0)
        progress_bar.show()
        log_area.clear()
        log_area.show()
        
        self.thread = QThread()
        self.worker_obj = Worker(task_function, *args, **kwargs)
        self.worker_obj.moveToThread(self.thread)
        
        # Redirect stdout within the thread's scope by patching the worker's run method
        original_run = self.worker_obj.run
        def run_with_redirect():
            original_stdout = sys.stdout
            sys.stdout = EmittingStream(self.worker_obj.output)
            try:
                original_run()
            finally:
                sys.stdout.flush()
                sys.stdout = original_stdout
        
        self.worker_obj.run = run_with_redirect

        self.thread.started.connect(self.worker_obj.run)
        self.worker_obj.finished.connect(self.thread.quit)
        self.worker_obj.finished.connect(self.worker_obj.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker_obj.progress.connect(progress_bar.setValue)
        self.worker_obj.output.connect(log_area.append)
        
        # Special connection for AI analysis results
        if 'perform_ai_analysis' in task_function.__name__:
            self.worker_obj.results.connect(self.update_dashboard_charts)
            
        self.worker_obj.finished.connect(on_finish_slot)
        self.thread.start()

    def start_news_gathering_process(self):
        dialog = DateRangeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            start_date, end_date = dialog.get_dates()
            self._run_task_in_thread(
                self.perform_news_gathering,
                self.gather_btn,
                self.gather_progress,
                self.gather_log,
                self.on_news_gathering_complete,
                "Gathering News...",
                start_date=start_date,
                end_date=end_date
            )
        else:
            self.gather_log.show()
            self.gather_log.setText("News gathering cancelled by user.")


    def on_news_gathering_complete(self):
        self.gather_btn.setEnabled(True)
        self.gather_btn.setText("Start News Gathering")
        self.gather_progress.hide()
        QMessageBox.information(self, "Process Complete", "News gathering finished.")


    def start_ai_analyzer_process(self):
        self._run_task_in_thread(
            self.perform_ai_analysis,
            self.ai_btn,
            self.ai_progress,
            self.ai_log,
            self.on_ai_analysis_complete,
            "Analyzing..."
        )

    def on_ai_analysis_complete(self):
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("Run AI Analyzer")
        self.ai_progress.hide()
        QMessageBox.information(self, "Process Complete", "AI analysis finished.")
        self.tabs.setTabEnabled(2, True)
        self.tabs.setCurrentIndex(2)

    # 🔹 YOUR FULL, UNTOUCHED NEWS GATHERING SCRIPT, INDENTED AS A METHOD 🔹
    def perform_news_gathering(self, worker, start_date, end_date):
        # The 'worker' object is passed to allow emitting signals (progress, output)
        # The start_date and end_date are from the PyQt dialog, making the Tkinter one redundant but kept.

        # --- Configuration ---
        PROFILE_PATH = r"C:\Users\i60475\AppData\Local\Google\Chrome\User Data\Selenium"
        WAIT_TIMEOUT = 20
        IMPLICIT_WAIT = 5
        BASE_URL = "https://www.upstreamonline.com/latest"
        OUTPUT_DIR = "C:/Office work/Upstream SCRAP news"
        USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        # --- End Configuration ---

        # --- GUI Popup for Calendar Date Selection (Original, kept but should not be called in this context) ---
        def select_date_range():
            start_date_tk = None
            end_date_tk = None

            def on_select_dates():
                nonlocal start_date_tk, end_date_tk
                start_date_str = start_date_calendar.get_date()
                end_date_str = end_date_calendar.get_date()
                start_date_tk = datetime.strptime(start_date_str, "%m/%d/%y").date()
                end_date_tk = datetime.strptime(end_date_str, "%m/%d/%y").date()
                date_window.destroy()

            date_window = Tk()
            date_window.title("Select Date Range")
            date_window.geometry("400x300")

            Label(date_window, text="Select Start Date:", font=("Arial", 12)).pack(pady=10)
            start_date_calendar = Calendar(date_window, date_pattern="mm/dd/yy", selectmode='day')
            start_date_calendar.pack(pady=10)

            Label(date_window, text="Select End Date:", font=("Arial", 12)).pack(pady=10)
            end_date_calendar = Calendar(date_window, date_pattern="mm/dd/yy", selectmode='day')
            end_date_calendar.pack(pady=10)

            Button(date_window, text="Confirm", command=on_select_dates, font=("Arial", 12)).pack(pady=20)
            date_window.mainloop()

            return start_date_tk, end_date_tk

        # --- Extract Article Links and Titles ---
        def get_article_links_and_titles(soup):
            articles = []
            seen_hrefs = set()
            for link in soup.select("a.card-link"):
                href = link.get("href")
                title = link.get_text(strip=True)
                if href and title and href not in seen_hrefs and re.search(r'/2-1-\d+$', href):
                    full_link = href if href.startswith("https://") else f"https://www.upstreamonline.com{href}"
                    articles.append((full_link, title))
                    seen_hrefs.add(href)
                    print(f"Found article link: {title}")
                elif href and title and href not in seen_hrefs:
                    print(f"ℹ️ Skipping non-article link: {title} ({href})")
                    seen_hrefs.add(href)
            return articles

        # --- Extract Article Details ---
        def extract_article_details(driver, link):
            driver.get(link)

            WebDriverWait(driver, WAIT_TIMEOUT).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)

            article_soup = BeautifulSoup(driver.page_source, "html.parser")

            date_element = article_soup.find("span", class_="dn-date-time")
            date_published = "No Date Found"
            if date_element:
                date_text = date_element.get_text(strip=True).replace("Published", "").replace("GMT", "").strip()
                if date_text.lower().startswith("updated"):
                    date_text = date_text[len("updated"):].strip()
                
                print(f"Attempting to parse cleaned date string: '{date_text}' for URL: {link}")

                current_datetime = datetime.now()
                parsed_dt_obj = None

                relative_time_match = re.search(r'(\d+)\s+(minute|hour|day|week|month)s?\s+ago', date_text, re.IGNORECASE)
                if relative_time_match:
                    value = int(relative_time_match.group(1))
                    unit = relative_time_match.group(2).lower()
                    
                    if unit == 'minute': parsed_dt_obj = current_datetime - timedelta(minutes=value)
                    elif unit == 'hour': parsed_dt_obj = current_datetime - timedelta(hours=value)
                    elif unit == 'day': parsed_dt_obj = current_datetime - timedelta(days=value)
                    elif unit == 'week': parsed_dt_obj = current_datetime - timedelta(weeks=value)
                    elif unit == 'month': parsed_dt_obj = current_datetime - timedelta(days=value * 30)
                elif "yesterday" in date_text.lower(): parsed_dt_obj = current_datetime - timedelta(days=1)
                elif "today" in date_text.lower(): parsed_dt_obj = current_datetime
                elif dateutil_parse:
                    try:
                        datetime_object = dateutil_parse(date_text, fuzzy=False) 
                        parsed_dt_obj = datetime_object
                    except (ValueError, TypeError) as e:
                        print(f"❌ Date format not recognized by dateutil: '{date_text}' for URL: {link} - Error: {e}")
                else:
                    try:
                        datetime_object = datetime.strptime(date_text, '%d %B %Y, %H:%M')
                        parsed_dt_obj = datetime_object
                    except ValueError:
                        try:
                            datetime_object = datetime.strptime(date_text, '%d %B %Y')
                            parsed_dt_obj = datetime_object
                        except ValueError:
                            print(f"❌ Date format not recognized: '{date_text}' for URL: {link}")

                if parsed_dt_obj:
                    if parsed_dt_obj.date() > current_datetime.date() + timedelta(days=1):
                        temp_date_minus_year = parsed_dt_obj.replace(year=parsed_dt_obj.year - 1).date()
                        if temp_date_minus_year <= current_datetime.date():
                            date_published = temp_date_minus_year
                            print(f"💡 Adjusted future date {parsed_dt_obj.date()} to {date_published} (subtracted 1 year).")
                        else:
                            print(f"⚠️ Parsed date {parsed_dt_obj.date()} is significantly in the future. Treating as unparseable for now.")
                            date_published = "No Date Found"
                    else:
                        date_published = parsed_dt_obj.date()
                else:
                    date_published = "No Date Found"

            article_content = "No Content Found"
            main_content_container = None
            preferred_selectors = [ "div.article-body__content", "article[class*='article-body']", "div[class*='article-body']", "div[class*='story-content']", "div[class*='post-content']", "div[class*='main-content']", "div[class*='content-area']", "article[class*='content']", "section[class*='content']", "div[class*='content']" ]
            for selector in preferred_selectors:
                candidate_container = article_soup.select_one(selector)
                if candidate_container:
                    if len(candidate_container.find_all("p", recursive=False)) > 1:
                        main_content_container = candidate_container
                        break
                    elif len(candidate_container.find_all("p")) > 2:
                        main_content_container = candidate_container
                        break
            if not main_content_container:
                potential_containers = article_soup.find_all( ["div", "article", "section"], class_=re.compile(r"article-body|content|body|main|post|story", re.IGNORECASE) )
                if potential_containers:
                    main_content_container = max(potential_containers, key=lambda c: len(c.find_all("p")), default=None)
            
            collected_paragraphs_text = []
            if main_content_container:
                paragraphs = main_content_container.find_all("p")
                seen_texts = set()
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 30 and not re.search(r"^(advertisement|sponsored|related articles|read more|also read|subscribe now|follow us|share this article|photo:|image:|caption:)", text, re.IGNORECASE):
                        if text not in seen_texts:
                            collected_paragraphs_text.append(text)
                            seen_texts.add(text)
                if collected_paragraphs_text:
                    article_content = "\n\n".join(collected_paragraphs_text).strip()

            category = "No Category Found"
            try:
                category_element = article_soup.select_one("div.topic-holder a.dn-link.pill.tag")
                if category_element:
                    category = category_element.text.strip()
            except Exception:
                print(f"Category not found for {link}")

            container_classes_list = main_content_container.get("class", []) if main_content_container and main_content_container.has_attr("class") else []
            return date_published, article_content, container_classes_list, category

        # --- Verification Mechanism ---
        def verify_scraped_dates(scraped_data, start_date, end_date):
            print("\n--- Verification Step ---")
            if not scraped_data:
                print("⚠️ No data was scraped, so verification cannot be performed.")
                return
            scraped_dates = {item['Date'] for item in scraped_data if isinstance(item.get('Date'), date)}
            expected_dates = {start_date + timedelta(days=d) for d in range((end_date - start_date).days + 1)}
            missing_dates = sorted(list(expected_dates - scraped_dates))
            if not missing_dates:
                print("✅ Verification successful: At least one article was found for every calendar day in the selected range.")
            else:
                print(f"🟡 Verification warning: No articles were found for the following {len(missing_dates)} day(s) within your timeline:")
                for missing_date in missing_dates:
                    print(f"  - {missing_date.strftime('%Y-%m-%d')}")
                print("This could be because no articles were published on these days, or they were potentially missed by the scraper.")

        # --- Helper for System Clock Check ---
        def get_real_current_year_from_api():
            if not requests:
                print("ℹ️  Skipping online year verification because 'requests' library is not installed.")
                return None
            try:
                print("Verifying system clock against online time source...")
                response = requests.get("http://worldtimeapi.org/api/ip", timeout=5)
                response.raise_for_status()
                data = response.json()
                iso_datetime_str = data.get('datetime')
                if iso_datetime_str and len(iso_datetime_str) >= 4:
                    real_year = int(iso_datetime_str[:4])
                    print(f"✅ Online time source reports the year is {real_year}.")
                    return real_year
                return None
            except Exception as e:
                print(f"⚠️  Warning: Could not verify current year via online API. Error: {e}")
                return None

        # --- Main Scraping Logic (wrapped in a function to use the nested helpers) ---
        def main():
            system_year = date.today().year
            real_current_year = get_real_current_year_from_api()

            if real_current_year and system_year > real_current_year:
                print("="*80)
                print("❌ WARNING: Your computer's system clock appears to be set to the future.")
                print(f"    System Date Detected: {date.today().strftime('%Y-%m-%d')}")
                print(f"    Online Time Service Detected Year: {real_current_year}")
                print("    This will cause news articles to be filtered incorrectly and must be fixed.")
                print("    Please check and correct your system's date and time if needed.")
                print("    The script will continue, but date filtering might be inaccurate.")
                print("="*80)
                # Remove the 'return' statement so the script continues:
                # return 

            # Instead of calling the Tkinter popup, we use the dates passed into the method.
            # local_start_date, local_end_date = select_date_range() 
            local_start_date, local_end_date = start_date, end_date

            if not local_start_date or not local_end_date:
                print("Date selection cancelled or invalid. Exiting.")
                return
            print(f"\n📅 Scraping from {local_start_date} to {local_end_date}\n")
            worker.progress.emit(1)

            scraped_data = []
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument(f"user-data-dir={PROFILE_PATH}")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={USER_AGENT}")

            try:
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                print(f"❌ Could not start WebDriver: {e}")
                worker.output.emit(f"❌ Could not start WebDriver: {e}. Ensure chromedriver is installed and accessible in your PATH.")
                return

            driver.implicitly_wait(IMPLICIT_WAIT)
            page_number = 1
            stop_scraping = False

            while not stop_scraping:
                page_url = f"https://www.upstreamonline.com/latest?page={page_number}"
                print(f"\n🌐 Visiting: {page_url}")
                try:
                    driver.get(page_url)
                    WebDriverWait(driver, WAIT_TIMEOUT).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    articles = get_article_links_and_titles(soup)
                    if not articles:
                        print("⚠️ No more articles found on the site. Ending pagination.")
                        break
                    for i, (link, title) in enumerate(articles):
                        # Simple progress update for the UI
                        worker.progress.emit(int(((i + 1) / len(articles)) * 100))
                        try:
                            print(f"Processing article: {title} ({link})")
                            parsed_date, article_content, container_classes, category = extract_article_details(driver, link)
                            print(f"Parsed date for {title}: {parsed_date} (type: {type(parsed_date)})")
                            if isinstance(parsed_date, date):
                                if parsed_date < local_start_date:
                                    print(f"🛑 Article '{title}' date ({parsed_date}) is older than start date ({local_start_date}). Stopping all scraping.")
                                    stop_scraping = True
                                    break
                                if local_start_date <= parsed_date <= local_end_date:
                                    scraped_data.append({
                                        "Topic": title, "Link": link, "Date": parsed_date, "Content": article_content,
                                        "Content Classes": container_classes, "URL Content Class": category
                                    })
                                    print(f"✅ Added '{title}' to the dataset.")
                                else:
                                    print(f"ℹ️ Article '{title}' date ({parsed_date}) is not in the selected range. Skipping.")
                            else:
                                print(f"ℹ️ Could not parse date for '{title}'. Skipping.")
                        except Exception as e:
                            print(f"❌ Error processing article: {link} - {e}")
                    if stop_scraping:
                        break
                    page_number += 1
                    time.sleep(1)
                except Exception as e:
                    print(f"❌ Page error: {e}")
                    break
            driver.quit()
            verify_scraped_dates(scraped_data, local_start_date, local_end_date)
            today_str = date.today().strftime('%Y-%m-%d')
            filename = f"news_filtered_by_date_{today_str}.xlsx"
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            file_path = os.path.join(OUTPUT_DIR, filename)
            if scraped_data:
                df = pd.DataFrame(scraped_data)
                df["Serial Number"] = range(1, len(df) + 1)
                df = df[["Topic", "Link", "Date", "Content", "Content Classes", "Serial Number", "URL Content Class"]]
                df.to_excel(file_path, index=False)
                print(f"\n✅ Data saved to: {file_path}")
            else:
                print("\n⚠️ No data collected.")
            worker.progress.emit(100)

        # --- Entry Point of the original script ---
        main()

    # 🔹 YOUR FULL, UNTOUCHED AI ANALYSIS SCRIPT, INDENTED AS A METHOD 🔹
    def perform_ai_analysis(self, worker):
        # The 'worker' object is passed to allow emitting signals (progress, output)
        
        # --- Configuration ---
        SPACY_MODEL = 'en_core_web_trf'
        nlp = None
        try:
            retry_attempts = 3
            for attempt in range(retry_attempts):
                try:
                    nlp = spacy.load(SPACY_MODEL)
                    print(f"Successfully loaded SpaCy model: {SPACY_MODEL}")
                    break
                except OSError as e: 
                    if attempt < retry_attempts - 1:
                        print(f"Attempt {attempt + 1} failed to load SpaCy model '{SPACY_MODEL}'. Retrying...")
                        spacy.cli.download(SPACY_MODEL)
                    else:
                        print(f"Failed to load SpaCy model '{SPACY_MODEL}' after {retry_attempts} attempts. Error: {e}")
                        raise
        except OSError:
            print(f"Downloading SpaCy model '{SPACY_MODEL}'...")
            spacy.cli.download(SPACY_MODEL)
            nlp = spacy.load(SPACY_MODEL)
            print(f"Successfully downloaded and loaded SpaCy model: {SPACY_MODEL}")

        OUTPUT_PATH = r"C:\Office work\Upstream SCRAP news\Filter output.xlsx"

        # --- ALL YOUR ORIGINAL KEYWORD LISTS AND REGEX PATTERNS ARE PRESERVED HERE ---
        BUILD_PROCESS_OPTIONS = [ "Concept Engineering", "Concept", "Pre-FEED", "Pre Front End Engineering Design", "FEED", "Front End Engineering Design", "Detailed Engineering", "Detailed Design", "Engineering & Construction", "EPC", "Procurement & Construction", "P+C", "E+C", "Site Preparation", "Trenching", "Project Management", "Transport", "Transportation", "Installation", "Hook up and commissioning", "Commissioning", "Hook-up", "Lease", "Operation & Maintenance", "O&M", "Asset Integrity", "IRM", "Inspection, Repair & Maintenance", "Duty Holder", "Decommissioning", "Decommissioning (Onshore Disposal)", "Onshore Disposal", "Decommissioning (Offshore Removal)", "Offshore Removal", "Decommissioning (Engineering)", "Decommissioning Engineering", "General Information", "General Contract" ]
        BUILD_PARTS = { "Tree", "Christmas Tree", "Wellhead", "Manifold", "Subsea Manifold", "Subsea Unit", "Control Module", "Subsea Control Module", "Subsea Arch", "Boosting", "Subsea Boosting", "Compression", "Subsea Compression", "Injection", "Subsea Injection", "Separation", "Subsea Separation", "Controls", "Subsea Controls", "Pipelines", "Subsea Pipelines", "Flowlines", "Subsea Flowlines", "Templates", "Subsea Templates", "Subsea", "Subsea Systems", "SURF", "Subsea Umbilicals, Risers and Flowlines", "SURF Package", "Umbilical", "Umbilical Lines", "Riser", "Flowline", "Flexibles", "Flexible Risers", "Flexible Flowlines", "SURF", "SURF Package", "Topside", "Topsides", "Topsides Deck", "Topsides Units", "Accommodation", "Topsides Accommodation", "Compression", "Topsides Compression", "Drilling", "Topsides Drilling", "Power", "Topsides Power", "Process", "Topsides Process", "Carbon Capture", "Topsides Carbon Capture", "Rig", "Drilling Rig", "Living Quarters", "Helideck", "FPSO", "FSRU", "FLNG", "MOPU", "FSO", "Floater", "TLP", "Spar", "Jacket", "Hull", "Caisson", "Compliant Tower", "GBS", "Gravity Base Structure", "Mooring", "Mooring System", "Subsea Mooring Connectors", "Connectors", "Piles", "Anchors", "Anchor", "Turret", "SPM", "Single Point Mooring", "Integration", "Project", "Subsea", "SURF Contract", "Topsides Contract", "WHd Contract" }
        ALL_BUILD_KEYWORDS = sorted(list(set(BUILD_PROCESS_OPTIONS + list(BUILD_PARTS))))
        TARGET_BUILD_PARTS = [ "pipeline", "pipelines", "subsea pipeline", "subsea pipelines", "umbilical", "umbilicals", "umbilical line", "umbilical lines", "flowline", "flowlines", "subsea flowline", "subsea flowlines", "riser", "risers", "cable", "cables", "communication cable", "power cable", "export cable" ]
        LENGTH_UNITS = ["km", "kilometer", "kilometers", "m", "meter", "meters", "mile", "miles", "foot", "feet", "ft"]
        LENGTH_UNITS_SHORT_EXACT = ["km", "m", "ft"]
        SORTED_TARGET_BUILD_PARTS = sorted(TARGET_BUILD_PARTS, key=len, reverse=True)
        NUM_UNIT_REGEX_SPACED = re.compile(r"(\d+(?:\.\d+)?)\s*(" + "|".join(LENGTH_UNITS) + r")\b", re.IGNORECASE)
        NUM_UNIT_REGEX_NOSPACE = re.compile(r"(\d+(?:\.\d+)?)(" + "|".join(LENGTH_UNITS_SHORT_EXACT) + r")\b", re.IGNORECASE)
        NUM_DASH_UNIT_REGEX = re.compile(r"(\d+(?:\.\d+)?)\s*-\s*(" + "|".join(unit for unit in LENGTH_UNITS if unit not in LENGTH_UNITS_SHORT_EXACT) + r")\b", re.IGNORECASE)
        WEIGHT_TARGET_PARTS = [ "topside", "topsides", "jacket", "hull", "module", "modules", "manifold", "tree", "christmas tree", "wellhead", "template", "pile", "piles", "anchor", "anchors", "turret", "gbs", "gravity base structure", "platform", "fpso", "fsru", "flng", "mopu", "fso", "floater", "tlp", "spar" ]
        WEIGHT_UNITS = ['t', 'ton', 'tons', 'tonne', 'tonnes', 'te', 'kg', 'kilogram', 'kilograms', 'lb', 'lbs', 'pound', 'pounds']
        WEIGHT_UNITS_SHORT_EXACT = ['t', 'kg', 'lb', 'lbs']
        SORTED_WEIGHT_TARGET_PARTS = sorted(WEIGHT_TARGET_PARTS, key=len, reverse=True)
        NUM_WEIGHT_UNIT_REGEX_SPACED = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(WEIGHT_UNITS) + r")\b", re.IGNORECASE)
        NUM_WEIGHT_UNIT_REGEX_NOSPACE = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(WEIGHT_UNITS_SHORT_EXACT) + r")\b", re.IGNORECASE)
        DIAMETER_TARGET_PARTS = [ "pipeline", "pipelines", "subsea pipeline", "subsea pipelines", "umbilical", "umbilicals", "umbilical line", "umbilical lines", "flowline", "flowlines", "subsea flowline", "subsea flowlines", "riser", "risers", "pile", "piles", "caisson" ]
        DIAMETER_UNITS = ['inch', 'inches', 'in', '"', 'mm', 'millimeter', 'millimeters', 'cm', 'centimeter', 'centimeters', 'm', 'meter', 'meters', 'foot', 'feet', 'ft']
        DIAMETER_UNITS_SHORT_EXACT = ['in', '"', 'mm', 'cm', 'm', 'ft']
        SORTED_DIAMETER_TARGET_PARTS = sorted(DIAMETER_TARGET_PARTS, key=len, reverse=True)
        NUM_DIAMETER_UNIT_REGEX_SPACED = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(DIAMETER_UNITS) + r")\b", re.IGNORECASE)
        NUM_DIAMETER_UNIT_REGEX_NOSPACE = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(DIAMETER_UNITS_SHORT_EXACT) + r")\b", re.IGNORECASE)
        NUM_DASH_DIAMETER_UNIT_REGEX = re.compile(r"([\d,]+(?:\.\d+)?)\s*-\s*(" + "|".join(unit for unit in DIAMETER_UNITS if unit not in DIAMETER_UNITS_SHORT_EXACT) + r")\b", re.IGNORECASE)
        DIMENSION_TARGET_PARTS = [ "topside", "topsides", "hull", "module", "modules", "platform", "fpso", "jacket", "vessel" ]
        DIMENSION_UNITS = ['m', 'meter', 'meters', 'foot', 'feet', 'ft']
        SORTED_DIMENSION_TARGET_PARTS = sorted(DIMENSION_TARGET_PARTS, key=len, reverse=True)
        ACCOMMODATION_TARGET_PARTS = [ "fpso", "platform", "living quarters", "accommodation module", "flotel", "vessel" ]
        ACCOMMODATION_UNITS = ['person', 'people', 'personnel', 'pob', 'berths', 'beds']
        SORTED_ACCOMMODATION_TARGET_PARTS = sorted(ACCOMMODATION_TARGET_PARTS, key=len, reverse=True)
        STORAGE_TARGET_PARTS = [ "fpso", "fso", "flng", "hull", "tank", "tanks", "vessel" ]
        STORAGE_UNITS = ['barrels', 'bbl', 'bbls', 'cubic meters', 'm3', 'tonnes', 't']
        SORTED_STORAGE_TARGET_PARTS = sorted(STORAGE_TARGET_PARTS, key=len, reverse=True)
        POWER_TARGET_PARTS = [ "power module", "generator", "platform", "fpso", "facility" ]
        POWER_UNITS = ['megawatt', 'mw', 'kilowatt', 'kw', 'gigawatt', 'gw']
        SORTED_POWER_TARGET_PARTS = sorted(POWER_TARGET_PARTS, key=len, reverse=True)
        MOORING_TARGET_PARTS = [ "fpso", "flng", "fsru", "fso", "spar", "tlp", "vessel", "buoy", "platform", "floater" ]
        MOORING_TYPES = [ "turret", "spread", "catenary", "taut-leg", "single-point", "disconnectable", "internal", "external" ]
        SORTED_MOORING_TARGET_PARTS = sorted(MOORING_TARGET_PARTS, key=len, reverse=True)
        VESSEL_TYPES = [ "vessel", "ship", "drillship", "semi-submersible", "rig", "jack-up", "platform supply vessel", "psv", "anchor handling tug supply", "ahts", "aht", "construction vessel", "subsea construction vessel", "scv", "pipelay vessel", "heavy-lift vessel", "flotel", "accommodation vessel", "support vessel", "tug", "barge", "tanker", "carrier", "seismic vessel" ]
        SORTED_VESSEL_TYPES = sorted(VESSEL_TYPES, key=len, reverse=True)
        VESSEL_SCOPE_KEYWORDS = [ "support", "drilling", "installation", "construction", "pipelay", "decommissioning", "accommodation", "transport", "maintenance", "survey", "seismic", "towing", "anchor handling", "rov", "inspection", "repair", "irm" ]
        VESSEL_CHARTER_VERBS = [ "charter", "contract", "hire", "award", "secure", "fix", "book", "mobilise", "deploy", "take on" ]
        DEPTH_RATING_TARGET_PARTS = [ "wellhead", "wellheads", "christmas tree", "trees", "manifold", "manifolds", "bop", "blowout preventer", "valve", "valves", "riser", "risers", "pipeline", "pipelines", "pump", "pumps", "compressor", "compressors", "umbilical", "umbilicals", "flowline", "flowlines", "connector", "connectors", "sps", "subsea production system", "subsea system", "subsea equipment" ]
        DEPTH_RATING_UNITS = ['meter', 'meters', 'm', 'feet', 'ft']
        SORTED_DEPTH_RATING_TARGET_PARTS = sorted(DEPTH_RATING_TARGET_PARTS, key=len, reverse=True)
        NUM_DEPTH_RATING_UNIT_REGEX = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(DEPTH_RATING_UNITS) + r")\b", re.IGNORECASE)
        PRESSURE_TARGET_PARTS = [ "wellhead", "wellheads", "christmas tree", "trees", "manifold", "manifolds", "bop", "blowout preventer", "valve", "valves", "riser", "risers", "pipeline", "pipelines", "choke" ]
        PRESSURE_UNITS = ['psi', 'bar', 'pascal', 'pa', 'kpa', 'mpa']
        SORTED_PRESSURE_TARGET_PARTS = sorted(PRESSURE_TARGET_PARTS, key=len, reverse=True)
        NUM_PRESSURE_UNIT_REGEX = re.compile(r"([\d,]+(?:k|K)?)\s*(" + "|".join(PRESSURE_UNITS) + r")\b", re.IGNORECASE)
        FLOW_CAPACITY_TARGET_PARTS = [ "pipeline", "pipelines", "flowline", "flowlines", "pump", "pumps", "compressor", "compressors", "riser", "risers", "processing plant", "facility", "terminal", "separator", "separators" ]
        FLOW_CAPACITY_UNITS = [ 'bpd', 'bbl/d', 'boepd', 'm3/d', 'scfd', 'mcfd', 'mmscfd', 'bcfd', 'tph', 'kg/s', 'gj/d', 'tcf/d', 'mcm/d', 'barrels per day', 'cubic meters per day', 'tonnes per hour' ]
        SORTED_FLOW_CAPACITY_TARGET_PARTS = sorted(FLOW_CAPACITY_TARGET_PARTS, key=len, reverse=True)
        NUM_FLOW_CAPACITY_UNIT_REGEX = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(FLOW_CAPACITY_UNITS) + r")\b", re.IGNORECASE)
        TEMP_TARGET_PARTS = [ "pipeline", "pipelines", "vessel", "vessels", "reactor", "reactors", "storage tank", "tanks", "heater", "heaters", "cooler", "coolers", "exchanger", "exchangers" ]
        TEMP_UNITS = ['celsius', 'fahrenheit', 'kelvin', 'c', 'f', 'k', 'degrees', '°c', '°f']
        SORTED_TEMP_TARGET_PARTS = sorted(TEMP_TARGET_PARTS, key=len, reverse=True)
        NUM_TEMP_UNIT_REGEX = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:degrees)?\s*(" + "|".join(TEMP_UNITS) + r")\b", re.IGNORECASE)
        QUANTITY_TARGET_PARTS = list(BUILD_PARTS)
        NON_COUNTABLE_KEYWORDS = [ "integration", "project", "subsea", "surf contract", "topsides contract", "whd contract", "boosting", "compression", "injection", "separation", "controls", "engineering", "management", "transport", "installation", "maintenance", "decommissioning", "procurement" ]
        SORTED_QUANTITY_TARGET_PARTS = sorted([p for p in QUANTITY_TARGET_PARTS if p.lower() not in NON_COUNTABLE_KEYWORDS], key=len, reverse=True)
        ENTITY_KEYWORDS_FOR_CAPACITY = { "Well": ["well", "wells", "wellbore"], "Field": ["field", "oilfield", "gas field", "fields", "development", "reservoir"], "Cluster": ["cluster", "hub", "tie-back"], "Block": ["block", "blocks", "licence block", "license"], "Basin": ["basin", "basins"], "Floater": ["fpso", "flng", "fsru", "mopu", "fso", "floater", "floating production storage and offloading", "vessel"], "Plant": ["plant", "facility", "terminal", "refinery", "processing plant", "gas plant", "petrochemical plant", "onshore facility", "station"], "Platform": ["platform", "topsides", "jacket", "rig", "drilling rig", "spar", "tlp", "semisubmersible", "fixed platform"], "Pipeline": ["pipeline", "pipelines", "flowline", "flowlines", "umbilical", "riser", "export line"], "Subsea": ["subsea production system", "sps", "manifold", "subsea pump", "template", "subsea facility"], "Project": ["project", "package", "phase", "development project", "expansion"] }

        # --- ALL YOUR ORIGINAL HELPER FUNCTIONS ARE PRESERVED HERE ---
        def clean_text(text):
            if pd.isna(text):
                return ""
            return str(text).strip()

        def extract_project_profiles(text):
            text = clean_text(text)
            if not text: return ''
            doc = nlp(text)
            found_names = set()
            regex_patterns = re.findall( r'\b(?:[A-Z][a-z0-9\'-]*\s*){1,5}(?:Field|Project|Development|Oilfield|Area|Licence|Basin|Discovery)\b|' r'\bBlock\s+(?:[A-Z0-9-]+)\b|' r'\b(?:Phase \d+|Package \d+|EPCI \d+)\b', text, re.IGNORECASE )
            for match in regex_patterns:
                found_names.add(match.strip())
            matcher = Matcher(nlp.vocab)
            pattern_name_designator = [ {"POS": {"IN": ["PROPN", "NOUN", "ADJ"]}, "OP": "+"}, {"LOWER": {"IN": ["field", "project", "development", "oilfield", "block", "area", "licence", "basin", "phase", "package", "discovery"]}} ]
            matcher.add("FIELD_PROJECT_NAME", [pattern_name_designator])
            matches = matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                if not (span.text.lower().startswith("the ") and len(span.text.split()) <= 2):
                    found_names.add(span.text.strip())
            for ent in doc.ents:
                if ent.label_ in ['PRODUCT', 'FAC', 'WORK_OF_ART']:
                    if any(term in ent.text.lower() for term in ['project', 'field', 'development', 'phase', 'package']):
                        found_names.add(ent.text.strip())
                    elif len(ent.text.split()) > 1 and all(t.istitle() or t.isupper() for t in ent.text.split()):
                        found_names.add(ent.text.strip())
                elif ent.label_ in ['GPE', 'LOC']:
                    for token in doc[ent.end:min(len(doc), ent.end+2)]:
                        if token.lower_ in ['field', 'basin', 'block', 'area', 'discovery']:
                            found_names.add(f"{ent.text.strip()} {token.text.strip()}")
                            break
            for name in found_names:
                if len(name) < 4 and not re.search(r'\d', name) and name.lower() not in ['block', 'field', 'project', 'phase']:
                    continue
            candidate_names = set()
            names_list = sorted(list(found_names), key=len, reverse=True)
            for i, name1 in enumerate(names_list):
                is_substring = False
                for j, name2 in enumerate(names_list):
                    if i != j and name1.lower() in name2.lower():
                        is_substring = True
                        break
                if not is_substring:
                    candidate_names.add(name1)
            if not candidate_names:
                return ''
            profiles = {name: {} for name in candidate_names}
            for sent in doc.sents:
                sent_text_lower = sent.text.lower()
                for name in candidate_names:
                    if any(part.lower() in sent_text_lower for part in name.split() if len(part) > 3):
                        depth_match = re.search(r"in ([\d,]+(?:\.\d+)?)\s*(meters?|m|feet|ft)\s+of water", sent_text_lower)
                        if depth_match and 'Depth' not in profiles[name]:
                            unit = 'm' if 'm' in depth_match.group(2) else 'ft'
                            profiles[name]['Depth'] = f"{depth_match.group(1).replace(',', '')}{unit}"
                        dist_match = re.search(r"([\d,]+(?:\.\d+)?)\s*(km|kilometers?|miles?)\s*(offshore|from the coast)", sent_text_lower)
                        if dist_match and 'Distance' not in profiles[name]:
                            unit = 'km' if 'k' in dist_match.group(2) else 'miles'
                            profiles[name]['Distance'] = f"{dist_match.group(1).replace(',', '')}{unit} offshore"
                        if 'Timeline' not in profiles[name]:
                            timeline_keywords = { "Startup": ["first oil", "first gas", "start-up", "online", "operational by", "come onstream", "begin production"], "Shutdown": ["shut down", "cease production", "decommissioning in", "abandonment in", "plug and abandon"] }
                            timeline_found = None
                            for status, keywords in timeline_keywords.items():
                                for kw in keywords:
                                    if kw in sent_text_lower:
                                        for ent in sent.ents:
                                            if ent.label_ == 'DATE':
                                                timeline_found = f"{status} {ent.text}"
                                                break
                                        if timeline_found: break
                                if timeline_found: break
                            if timeline_found:
                                profiles[name]['Timeline'] = timeline_found
                        if 'Capacity' not in profiles[name]:
                            if not re.search(r'[\$€£]', sent.text):
                                CAPACITY_REGEX = r"([\d,.]+(?:\.\d+)?\s*(?:million|billion|thousand|mn|bn|k)?\s*(?:bpd|boe/d|boepd|mmscfd|scfd|tpd|mcfd|bbl/d|bcfd|mboed|tcf/d|mcm/d|tonnes/year|t/y|t/d|barrels|tonnes|cubic\s+feet|cubic\s+meters))"
                                cap_match = re.search(CAPACITY_REGEX, sent.text, re.IGNORECASE)
                                if cap_match:
                                    profiles[name]['Capacity'] = ' '.join(cap_match.group(1).split())
            output_parts = []
            for name in sorted(list(candidate_names)):
                details = profiles[name]
                if not details:
                    output_parts.append(name)
                else:
                    ordered_details = []
                    if 'Capacity' in details: ordered_details.append(f"Capacity: {details['Capacity']}")
                    if 'Timeline' in details: ordered_details.append(f"Timeline: {details['Timeline']}")
                    if 'Depth' in details: ordered_details.append(f"Depth: {details['Depth']}")
                    if 'Distance' in details: ordered_details.append(f"Distance: {details['Distance']}")
                    detail_str = ", ".join(ordered_details)
                    output_parts.append(f"{name} ({detail_str})")
            return "; ".join(output_parts)

        def extract_vessel_details(text):
            text = clean_text(text)
            if not text:
                return ''
            doc = nlp(text)
            vessel_profiles = {}
            potential_vessel_spans = []
            for ent in doc.ents:
                if ent.label_ in ["PRODUCT", "FAC", "ORG"]:
                    ent_text_lower = ent.text.lower()
                    if any(char.isdigit() for char in ent.text) or '-' in ent.text or any(v_type in ent_text_lower for v_type in VESSEL_TYPES):
                        potential_vessel_spans.append(ent)
            matcher = Matcher(nlp.vocab)
            pattern = [{"LOWER": {"IN": ["vessel", "ship", "rig", "drillship", "flotel"]}}, {"POS": "PROPN", "OP": "+"}]
            matcher.add("VESSEL_NAMED", [pattern])
            matches = matcher(doc)
            for _, start, end in matches:
                potential_vessel_spans.append(doc[start:end])
            for vessel_span in potential_vessel_spans:
                vessel_name = vessel_span.text
                for v_type in SORTED_VESSEL_TYPES:
                    if vessel_name.lower().endswith(f" {v_type}"):
                        vessel_name = vessel_name[:-(len(v_type)+1)].strip()
                        break
                if vessel_name.lower() in VESSEL_TYPES or len(vessel_name) < 4:
                    continue
                sent = vessel_span.sent
                sent_text_lower = sent.text.lower()
                if vessel_name not in vessel_profiles:
                    vessel_profiles[vessel_name] = {}
                profile = vessel_profiles[vessel_name]
                if 'Type' not in profile:
                    for v_type in SORTED_VESSEL_TYPES:
                        if v_type in sent_text_lower:
                            profile['Type'] = v_type.title()
                            break
                for ent in sent.ents:
                    if ent.label_ == 'ORG':
                        if f"{ent.text}'s".lower() in sent_text_lower and 'Owner' not in profile:
                            profile['Owner'] = ent.text
                        if any(verb in sent_text_lower for verb in VESSEL_CHARTER_VERBS) and 'Charterer' not in profile:
                            if 'Owner' not in profile or profile['Owner'] != ent.text:
                                profile['Charterer'] = ent.text
                day_rate_match = re.search(r"((?:[\$€£]|usd)\s?[\d,]+(?:\.\d+)?(?:k| thousand)?)\s*(?:per day|a day|dayrate)", sent_text_lower)
                if day_rate_match and 'Day Rate' not in profile:
                    profile['Day Rate'] = day_rate_match.group(1).replace(" thousand", "k")
                duration_match = re.search(r"(?:for|of)\s+((?:a firm period of\s+)?(?:up to\s+)?(?:\d+|[\w\s]+)\s(?:year|month|week|day)s?)", sent_text_lower)
                if duration_match and 'Duration' not in profile:
                    profile['Duration'] = duration_match.group(1).strip()
                scope_match = re.search(r"(?:to|for|perform|carry out)\s+((?:[\w\s-]+\s)?(?:{})(?:[\w\s-]+)?)".format("|".join(VESSEL_SCOPE_KEYWORDS)), sent_text_lower)
                if scope_match and 'Scope' not in profile:
                    scope_text = re.sub(r'\s+', ' ', scope_match.group(1)).strip(" .,").strip()
                    profile['Scope'] = scope_text
            output_parts = []
            for vessel_name, profile in sorted(vessel_profiles.items()):
                if not profile:
                    continue
                details = []
                if 'Type' in profile: details.append(f"Type: {profile['Type']}")
                if 'Owner' in profile: details.append(f"Owner: {profile['Owner']}")
                if 'Charterer' in profile: details.append(f"Charterer: {profile['Charterer']}")
                if 'Day Rate' in profile: details.append(f"Day Rate: {profile['Day Rate']}")
                if 'Duration' in profile: details.append(f"Duration: {profile['Duration']}")
                if 'Scope' in profile: details.append(f"Scope: {profile['Scope']}")
                detail_str = ", ".join(details)
                if detail_str:
                    output_parts.append(f"{vessel_name} ({detail_str})")
                else:
                    output_parts.append(vessel_name)
            return "; ".join(output_parts)

        def extract_build_part_specifications(text):
            text = clean_text(text)
            if not text:
                return ''
            doc = nlp(text)
            matcher = Matcher(nlp.vocab)
            parsed_specs_set = set()
            length_pattern1 = [ {"LIKE_NUM": True}, {"LOWER": {"IN": LENGTH_UNITS}}, {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"} ]
            length_pattern1a = [ {"TEXT": {"REGEX": r"(?i)^\d+(\.\d+)?(" + "|".join(LENGTH_UNITS_SHORT_EXACT) + r")$"}}, {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"} ]
            length_pattern2 = [ {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"}, {"LOWER": "of"}, {"LIKE_NUM": True}, {"LOWER": {"IN": LENGTH_UNITS}} ]
            length_pattern2a = [ {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"}, {"LOWER": "of"}, {"TEXT": {"REGEX": r"(?i)^\d+(\.\d+)?(" + "|".join(LENGTH_UNITS_SHORT_EXACT) + r")$"}} ]
            length_pattern3 = [ {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"}, {"LOWER": {"IN": ["measuring", "stretching", "spanning", "long"]}}, {"LIKE_NUM": True}, {"LOWER": {"IN": LENGTH_UNITS}} ]
            length_pattern4 = [ {"LIKE_NUM": True}, {"IS_PUNCT": True, "LOWER": "-"}, {"LOWER": {"IN": [unit for unit in LENGTH_UNITS if unit not in LENGTH_UNITS_SHORT_EXACT]}}, {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"} ]
            matcher.add("LENGTH_SPEC", [length_pattern1, length_pattern1a, length_pattern2, length_pattern2a, length_pattern3, length_pattern4])
            weight_pattern1 = [{"LIKE_NUM": True}, {"LOWER": {"IN": WEIGHT_UNITS}}, {"LOWER": {"IN": WEIGHT_TARGET_PARTS}, "OP": "+"}]
            weight_pattern2 = [{"LOWER": {"IN": WEIGHT_TARGET_PARTS}, "OP": "+"}, {"LOWER": "of"}, {"LIKE_NUM": True}, {"LOWER": {"IN": WEIGHT_UNITS}}]
            weight_pattern3 = [{"LOWER": {"IN": WEIGHT_TARGET_PARTS}, "OP": "+"}, {"LOWER": "weighing"}, {"LIKE_NUM": True}, {"LOWER": {"IN": WEIGHT_UNITS}}]
            weight_pattern4 = [{"LOWER": {"IN": WEIGHT_TARGET_PARTS}, "OP": "+"}, {"LOWER": "with"}, {"LOWER": "a", "OP": "?"}, {"LOWER": "weight"}, {"LOWER": "of"}, {"LIKE_NUM": True}, {"LOWER": {"IN": WEIGHT_UNITS}}]
            matcher.add("WEIGHT_SPEC", [weight_pattern1, weight_pattern2, weight_pattern3, weight_pattern4])
            diameter_pattern1 = [ {"LIKE_NUM": True}, {"IS_PUNCT": True, "LOWER": "-", "OP": "?"}, {"LOWER": {"IN": DIAMETER_UNITS}}, {"LOWER": "diameter", "OP": "?"}, {"LOWER": {"IN": DIAMETER_TARGET_PARTS}, "OP": "+"} ]
            diameter_pattern2 = [ {"LOWER": {"IN": DIAMETER_TARGET_PARTS}, "OP": "+"}, {"LOWER": "with"}, {"LOWER": {"IN": ["a", "an"]}, "OP": "?"}, {"LOWER": "diameter"}, {"LOWER": "of"}, {"LIKE_NUM": True}, {"LOWER": {"IN": DIAMETER_UNITS}} ]
            diameter_pattern3 = [ {"LOWER": {"IN": DIAMETER_TARGET_PARTS}, "OP": "+"}, {"LOWER": "of"}, {"LIKE_NUM": True}, {"LOWER": {"IN": DIAMETER_UNITS}}, {"LOWER": "in"}, {"LOWER": "diameter"} ]
            diameter_pattern4 = [ {"LIKE_NUM": True}, {"LOWER": {"IN": ["to", "-"]}}, {"LIKE_NUM": True}, {"LOWER": {"IN": DIAMETER_UNITS}}, {"LOWER": "diameter", "OP": "?"}, {"LOWER": {"IN": DIAMETER_TARGET_PARTS}, "OP": "+"} ]
            matcher.add("DIAMETER_SPEC", [diameter_pattern1, diameter_pattern2, diameter_pattern3, diameter_pattern4])
            depth_pattern1 = [ {"LOWER": {"IN": DEPTH_RATING_TARGET_PARTS}, "OP": "+"}, {"LOWER": {"IN": ["rated", "designed"]}}, {"LOWER": "for"}, {"LIKE_NUM": True}, {"LOWER": {"IN": DEPTH_RATING_UNITS}}, {"LOWER": {"IN": ["depth", "water", "water depth"]}, "OP": "?"} ]
            depth_pattern2 = [ {"LIKE_NUM": True}, {"LOWER": {"IN": DEPTH_RATING_UNITS}}, {"LOWER": {"IN": ["depth", "water", "water depth"]}}, {"LOWER": {"IN": DEPTH_RATING_TARGET_PARTS}, "OP": "+"} ]
            depth_pattern3 = [ {"LOWER": {"IN": DEPTH_RATING_TARGET_PARTS}, "OP": "+"}, {"LOWER": "for"}, {"LIKE_NUM": True}, {"LOWER": {"IN": DEPTH_RATING_UNITS}}, {"LOWER": "water", "OP": "?"} ]
            matcher.add("DEPTH_RATING_SPEC", [depth_pattern1, depth_pattern2, depth_pattern3])
            pressure_pattern1 = [ {"TEXT": {"REGEX": r"[\d,]+(?:k|K)?"}}, {"LOWER": {"IN": PRESSURE_UNITS}}, {"LOWER": {"IN": PRESSURE_TARGET_PARTS}, "OP": "+"} ]
            pressure_pattern2 = [ {"LOWER": {"IN": PRESSURE_TARGET_PARTS}, "OP": "+"}, {"LOWER": {"IN": ["rated", "designed"]}}, {"LOWER": "for", "OP": "?"}, {"TEXT": {"REGEX": r"[\d,]+(?:k|K)?"}}, {"LOWER": {"IN": PRESSURE_UNITS}} ]
            matcher.add("PRESSURE_SPEC", [pressure_pattern1, pressure_pattern2])
            quantity_pattern1 = [ {"LIKE_NUM": True}, {"LOWER": {"IN": SORTED_QUANTITY_TARGET_PARTS}, "OP": "+"} ]
            quantity_pattern2 = [ {"LEMMA": {"IN": ["supply", "install", "deliver", "provide", "order", "fabricate", "build", "construct"]}}, {"LOWER": "of", "OP": "?"}, {"LIKE_NUM": True}, {"LOWER": {"IN": SORTED_QUANTITY_TARGET_PARTS}, "OP": "+"} ]
            matcher.add("QUANTITY_SPEC", [quantity_pattern1, quantity_pattern2])
            flow_cap_pattern1 = [ {"LOWER": {"IN": FLOW_CAPACITY_TARGET_PARTS}, "OP": "+"}, {"LOWER": {"IN": ["with", "has"]}}, {"LOWER": "a", "OP": "?"}, {"LOWER": {"IN": ["capacity", "flow", "rate", "throughput", "output"]}}, {"LOWER": "of"}, {"LIKE_NUM": True}, {"LOWER": {"IN": FLOW_CAPACITY_UNITS}} ]
            flow_cap_pattern2 = [ {"LIKE_NUM": True}, {"LOWER": {"IN": FLOW_CAPACITY_UNITS}}, {"LOWER": {"IN": FLOW_CAPACITY_TARGET_PARTS}, "OP": "+"} ]
            matcher.add("FLOW_CAP_SPEC", [flow_cap_pattern1, flow_cap_pattern2])
            temp_pattern1 = [ {"LOWER": {"IN": TEMP_TARGET_PARTS}, "OP": "+"}, {"LOWER": {"IN": ["rated", "designed", "operating"]}}, {"LOWER": {"IN": ["to", "at", "for"]}, "OP": "?"}, {"TEXT": {"REGEX": r"-?\d+"}}, {"LOWER": {"IN": TEMP_UNITS}} ]
            matcher.add("TEMP_SPEC", [temp_pattern1])
            dimension_pattern1 = [ {"LOWER": {"IN": DIMENSION_TARGET_PARTS}, "OP": "+"}, {"LOWER": {"IN": ["with", "has", "measuring"]}, "OP": "?"}, {"LOWER": {"IN": ["dimensions", "a size"]}, "OP": "?"}, {"LOWER": "of", "OP": "?"}, {"LIKE_NUM": True}, {"LOWER": {"IN": ["by", "x"]}}, {"LIKE_NUM": True}, {"LOWER": {"IN": DIMENSION_UNITS}, "OP": "?"} ]
            matcher.add("DIMENSION_SPEC", [dimension_pattern1])
            accommodation_pattern1 = [ {"LOWER": {"IN": ["accommodation", "accommodate", "capacity"]}}, {"LOWER": "for", "OP": "?"}, {"LIKE_NUM": True}, {"LOWER": {"IN": ACCOMMODATION_UNITS}} ]
            accommodation_pattern2 = [ {"LIKE_NUM": True}, {"IS_PUNCT": True, "LOWER": "-", "OP": "?"}, {"LOWER": {"IN": ACCOMMODATION_UNITS}}, {"LOWER": {"IN": ACCOMMODATION_TARGET_PARTS}, "OP": "+"} ]
            matcher.add("ACCOMMODATION_SPEC", [accommodation_pattern1, accommodation_pattern2])
            storage_pattern1 = [ {"LOWER": {"IN": STORAGE_TARGET_PARTS}, "OP": "+"}, {"LOWER": {"IN": ["with", "has", "can"]}, "OP": "?"}, {"LOWER": "a", "OP": "?"}, {"LOWER": "storage"}, {"LOWER": "capacity"}, {"LOWER": "of"}, {"LIKE_NUM": True}, {"LOWER": {"IN": ["million", "billion", "thousand"]}, "OP": "?"}, {"LOWER": {"IN": STORAGE_UNITS}} ]
            storage_pattern2 = [ {"LEMMA": "store"}, {"LIKE_NUM": True}, {"LOWER": {"IN": ["million", "billion", "thousand"]}, "OP": "?"}, {"LOWER": {"IN": STORAGE_UNITS}} ]
            matcher.add("STORAGE_SPEC", [storage_pattern1, storage_pattern2])
            power_pattern1 = [ {"LIKE_NUM": True}, {"LOWER": {"IN": POWER_UNITS}}, {"LOWER": "power", "OP": "?"}, {"LOWER": {"IN": ["generation", "capacity", "output"]}, "OP": "?"}, {"LOWER": {"IN": POWER_TARGET_PARTS}, "OP": "+"} ]
            matcher.add("POWER_SPEC", [power_pattern1])
            mooring_pattern1 = [ {"LIKE_NUM": True}, {"IS_PUNCT": True, "LOWER": "-", "OP": "?"}, {"LOWER": "point"}, {"LOWER": {"IN": MOORING_TYPES}, "OP": "?"}, {"LOWER": "mooring"}, {"LOWER": "system", "OP": "?"} ]
            matches = matcher(doc)
            for match_id, start, end in matches:
                string_id = nlp.vocab.strings[match_id]
                span = doc[start:end]
                span_text = span.text
                span_text_lower = span_text.lower()
                identified_part_canonical = None
                identified_spec_str = None
                if string_id == "LENGTH_SPEC":
                    for part_kw in SORTED_TARGET_BUILD_PARTS:
                        if part_kw.lower() in span_text_lower:
                            identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                            break
                    num_match = NUM_UNIT_REGEX_SPACED.search(span_text) or NUM_UNIT_REGEX_NOSPACE.search(span_text) or NUM_DASH_UNIT_REGEX.search(span_text)
                    if num_match:
                        value, unit = num_match.groups()
                        if unit.lower() in ["kilometer", "kilometers"]: unit = "km"
                        elif unit.lower() in ["meter", "meters", "metres"]: unit = "m"
                        elif unit.lower() in ["mile", "miles"]: unit = "miles"
                        elif unit.lower() in ["foot", "feet"]: unit = "ft"
                        identified_spec_str = f"{value} {unit}"
                    else:
                        num_tok, unit_tok = None, None
                        for token in span:
                            if token.like_num: num_tok = token.text
                            if token.lower_ in LENGTH_UNITS: unit_tok = token.lower_
                        if num_tok and unit_tok:
                            identified_spec_str = f"{num_tok} {unit_tok}"
                elif string_id == "WEIGHT_SPEC":
                    for part_kw in SORTED_WEIGHT_TARGET_PARTS:
                        if part_kw.lower() in span_text_lower:
                            identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                            break
                    num_match = NUM_WEIGHT_UNIT_REGEX_SPACED.search(span_text) or NUM_WEIGHT_UNIT_REGEX_NOSPACE.search(span_text)
                    if num_match:
                        value, unit = num_match.groups()
                        value = value.replace(',', '')
                        if unit.lower() in ["tonne", "tonnes", "ton", "te"]: unit = "t"
                        elif unit.lower() in ["kilogram", "kilograms"]: unit = "kg"
                        elif unit.lower() in ["pound", "pounds"]: unit = "lbs"
                        identified_spec_str = f"{value} {unit}"
                    else:
                        num_tok, unit_tok = None, None
                        for token in span:
                            if token.like_num: num_tok = token.text
                            if token.lower_ in WEIGHT_UNITS: unit_tok = token.lower_
                        if num_tok and unit_tok:
                            identified_spec_str = f"{num_tok} {unit_tok}"
                elif string_id == "DIAMETER_SPEC":
                    for part_kw in SORTED_DIAMETER_TARGET_PARTS:
                        if part_kw.lower() in span_text_lower:
                            identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                            break
                    range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*(" + "|".join(DIAMETER_UNITS) + r")", span_text, re.IGNORECASE)
                    if range_match:
                        val1, val2, unit_str = range_match.groups()
                        val1 = val1.replace(',', '')
                        val2 = val2.replace(',', '')
                        if unit_str.lower() in ['inch', 'inches', '"']: unit = 'in'
                        elif unit_str.lower() in ['millimeter', 'millimeters']: unit = 'mm'
                        elif unit_str.lower() in ['centimeter', 'centimeters']: unit = 'cm'
                        elif unit_str.lower() in ['meter', 'meters']: unit = 'm'
                        elif unit_str.lower() in ['foot', 'feet']: unit = 'ft'
                        else: unit = unit_str.lower()
                        identified_spec_str = f"{val1}-{val2} {unit} diameter"
                    else:
                        num_match = NUM_DIAMETER_UNIT_REGEX_SPACED.search(span_text) or NUM_DASH_DIAMETER_UNIT_REGEX.search(span_text) or NUM_DIAMETER_UNIT_REGEX_NOSPACE.search(span_text)
                        if num_match:
                            value, unit = num_match.groups()
                            value = value.replace(',', '')
                            if unit.lower() in ['inch', 'inches', '"']: unit = 'in'
                            elif unit.lower() in ['millimeter', 'millimeters']: unit = 'mm'
                            elif unit.lower() in ['centimeter', 'centimeters']: unit = 'cm'
                            elif unit.lower() in ['foot', 'feet']: unit = 'ft'
                            identified_spec_str = f"{value} {unit} diameter"
                        else:
                            num_tok, unit_tok = None, None
                            for token in span:
                                if token.like_num: num_tok = token.text
                                if token.lower_ in DIAMETER_UNITS: unit_tok = token.lower_
                            if num_tok and unit_tok:
                                identified_spec_str = f"{num_tok} {unit_tok} diameter"
                elif string_id == "DEPTH_RATING_SPEC":
                    for part_kw in SORTED_DEPTH_RATING_TARGET_PARTS:
                        if part_kw.lower() in span_text_lower:
                            identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                            break
                    num_match = NUM_DEPTH_RATING_UNIT_REGEX.search(span_text)
                    if num_match:
                        value, unit = num_match.groups()
                        value = value.replace(',', '')
                        if unit.lower() in ['meter', 'meters']: unit = 'm'
                        elif unit.lower() in ['feet']: unit = 'ft'
                        identified_spec_str = f"{value} {unit} depth"
                    else:
                        num_tok, unit_tok = None, None
                        for token in span:
                            if token.like_num: num_tok = token.text
                            if token.lower_ in DEPTH_RATING_UNITS: unit_tok = token.lower_
                        if num_tok and unit_tok:
                            identified_spec_str = f"{num_tok} {unit_tok} depth"
                elif string_id == "PRESSURE_SPEC":
                    for part_kw in SORTED_PRESSURE_TARGET_PARTS:
                        if part_kw.lower() in span_text_lower:
                            identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                            break
                    num_match = NUM_PRESSURE_UNIT_REGEX.search(span_text)
                    if num_match:
                        value, unit = num_match.groups()
                        value = value.replace(',', '').lower()
                        if 'k' in value:
                            value = str(int(float(value.replace('k', '')) * 1000))
                        identified_spec_str = f"{value} {unit.lower()}"
                elif string_id == "QUANTITY_SPEC":
                    num_token, part_span = None, None
                    for token in span:
                        if token.like_num:
                            try:
                                num_val = float(token.text)
                                if 1950 < num_val < 2100: continue
                                num_token = token
                            except ValueError:
                                num_token = token
                    for part_kw in SORTED_QUANTITY_TARGET_PARTS:
                        if part_kw.lower() in span_text_lower:
                            identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                            break
                    if num_token and identified_part_canonical:
                        if not identified_part_canonical.endswith('s') and num_token.is_digit and float(num_token.text) > 100:
                            continue
                        identified_spec_str = f"{num_token.text} units"
                elif string_id == "FLOW_CAP_SPEC":
                    for part_kw in SORTED_FLOW_CAPACITY_TARGET_PARTS:
                        if part_kw.lower() in span_text_lower:
                            identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                            break
                    num_match = NUM_FLOW_CAPACITY_UNIT_REGEX.search(span_text)
                    if num_match:
                        value, unit = num_match.groups()
                        value = value.replace(',', '')
                        identified_spec_str = f"{value} {unit.lower()} capacity"
                elif string_id == "TEMP_SPEC":
                    part_found_in_span = False
                    for part_kw in SORTED_TEMP_TARGET_PARTS:
                        if part_kw.lower() in span_text_lower:
                            identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                            part_found_in_span = True
                            break
                    if not part_found_in_span:
                        sent_text_lower = span.sent.text.lower()
                        for part_kw in SORTED_TEMP_TARGET_PARTS:
                            if part_kw.lower() in sent_text_lower:
                                identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                                break
                    num_match = NUM_TEMP_UNIT_REGEX.search(span_text)
                    if num_match:
                        value, unit = num_match.groups()
                        unit = unit.replace('°', '').lower()
                        if unit == 'c': unit = 'Celsius'
                        if unit == 'f': unit = 'Fahrenheit'
                        identified_spec_str = f"{value} {unit} temperature"
                if identified_part_canonical and identified_spec_str:
                    parsed_specs_set.add(f"{identified_part_canonical}: {identified_spec_str}")
                else:
                    parsed_specs_set.add(span_text.strip())
            return ', '.join(sorted(list(parsed_specs_set))) if parsed_specs_set else ''

        def filter_companies(company_list, text):
            if not company_list:
                return []
            doc = nlp(text) 
            filtered = set()
            designators = ['co\\.', 'inc\\.', 'ltd\\.', 'gmbh', 'llc', 'corp\\.', 'plc', 'group', 'solutions', 'energy', 'oil & gas', 'international', 'holdings', 'corporation', 'industries', 'ventures', 'resources', 'services', 'systems']
            known_companies = ["Saudi Aramco", "Petronas", "Shell", "BP", "ExxonMobil", "TotalEnergies", "Equinor", "Chevron", "ConocoPhillips", "ENI", "Sinopec", "CNPC", "Gazprom", "Baker Hughes", "Schlumberger", "Halliburton", "TechnipFMC", "Subsea 7", "Saipem", "McDermott", "Wood", "Worley"]
            for company_name_str in company_list: 
                company_name = str(company_name_str).strip() 
                found = False
                for kc in known_companies:
                    if kc.lower() in company_name.lower() or company_name.lower() in kc.lower():
                        filtered.add(kc)
                        found = True
                        break
                if found: continue
                if any(re.search(r'\b' + d + r'\b', company_name.lower()) for d in designators):
                    filtered.add(company_name)
                    continue
                for ent in doc.ents:
                    if ent.label_ == 'ORG' and company_name in ent.text and len(ent.text.split()) > len(company_name.split()):
                        if any(re.search(r'\b' + d + r'\b', ent.text.lower()) for d in designators) or ent.text in known_companies:
                            filtered.add(ent.text)
                            found = True
                            break
                if found: continue
                if len(company_name.split()) == 1:
                    if company_name.lower() in ["technology", "industrial", "energy", "company", "group", "systems", "solutions"]:
                        continue
                    if re.search(r'\b' + re.escape(company_name) + r'\s+(?:' + '|'.join(designators) + r')\b', text, re.IGNORECASE) or \
                       re.search(r'\b(?:' + '|'.join(designators) + r')\s+' + re.escape(company_name) + r'\b', text, re.IGNORECASE) or \
                       company_name in ["Aramco", "Shell", "BP", "ExxonMobil", "TotalEnergies", "Equinor"]: 
                        filtered.add(company_name)
                        continue
                else:
                    filtered.add(company_name)
            return sorted(list(filtered))

        def extract_entities_by_label_refined(text, labels):
            text = clean_text(text)
            if not text: return ''
            doc = nlp(text)
            entities = [ent.text.strip() for ent in doc.ents if ent.label_ in labels]
            if 'ORG' in labels:
                entities = filter_companies(entities, text) 
            return ', '.join(sorted(set(entities)))

        def extract_scope_keywords(text):
            text = clean_text(text)
            if not text: return ''
            text_lower = text.lower()
            found_keywords = set()
            for kw in ALL_BUILD_KEYWORDS:
                if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower):
                    found_keywords.add(kw)
                elif len(kw.split()) > 1 and kw.lower() in text_lower:
                    found_keywords.add(kw)
            return ', '.join(sorted(found_keywords))

        def extract_delays_dates(text):
            text = clean_text(text)
            if not text: return ''
            doc = nlp(text)
            delay_keywords = ['delay', 'postpone', 'push back', 'reschedule', 'deadline', 'extension', 'setback', 'deferment']
            mentions_delay = any(kw in text.lower() for kw in delay_keywords)
            if mentions_delay:
                relevant_dates = []
                for date_ent in doc.ents:
                    if date_ent.label_ == 'DATE':
                        span_around_date = doc[max(0, date_ent.start - 10):min(len(doc), date_ent.end + 10)].text.lower()
                        if any(kw in span_around_date for kw in delay_keywords):
                            relevant_dates.append(date_ent.text)
                return ', '.join(sorted(set(relevant_dates)))
            return ''

        def extract_budget(text):
            text = clean_text(text)
            if not text: return ''
            doc = nlp(text)
            money_entities = [ent.text for ent in doc.ents if ent.label_ == 'MONEY']
            money_patterns = re.findall( r'\b(?:USD|EUR|GBP|A?\$|€|£)\s?\d+(?:\.\d+)?\s*(?:billion|million|bn|mn)?\b|\b\d+(?:\.\d+)?\s*(?:billion|million|bn|mn)\s*(?:USD|EUR|GBP|A?\$|€|£)?\b', text, re.IGNORECASE )
            all_money = list(set(money_entities + money_patterns))
            return ', '.join(sorted(all_money))

        def extract_quotes(text):
            text = clean_text(text)
            if not text: return ''
            return ' | '.join(re.findall(r'"(.*?)"', text))

        def extract_project_status(text):
            text = clean_text(text).lower()
            if not text: return ''
            doc = nlp(text)
            found_statuses = set()
            matcher = Matcher(nlp.vocab)
            decommissioning_patterns = [ [{"LOWER": "plug"}, {"LOWER": "and"}, {"LOWER": "abandon"}], [{"LOWER": "p&a"}], [{"LEMMA": "decommission"}] ]
            matcher.add("DECOMMISSIONING_STATUS", decommissioning_patterns)
            awarded_patterns = [ [{"LEMMA": "contract"}, {"LEMMA": "award"}], [{"LEMMA": "award"}, {"LEMMA": "contract"}], [{"LEMMA": "sign"}, {"LEMMA": "contract"}], [{"LEMMA": "contract"}, {"LEMMA": "sign"}], [{"LEMMA": "deal"}, {"LEMMA": "sign"}], [{"LEMMA": "agreement"}, {"LEMMA": "sign"}], [{"LEMMA": "award"}], [{"LEMMA": "secure"}], [{"LEMMA": "win"}], [{"LOWER": "letter"}, {"LOWER": "of"}, {"LOWER": "intent"}], [{"LOWER": "memorandum"}, {"LOWER": "of"}, {"LOWER": "understanding"}], [{"LOWER": "reach"}, {"LOWER": "agreement"}] ]
            matcher.add("AWARDED_STATUS", awarded_patterns)
            tendered_patterns = [ [{"LEMMA": "tender"}, {"LEMMA": "issue"}], [{"LOWER": "invitation"}, {"LOWER": "to"}, {"LOWER": "bid"}], [{"LOWER": "pre-qualification"}], [{"LEMMA": "bid"}, {"LEMMA": "process"}], [{"LOWER": "call"}, {"LOWER": "for"}, {"LOWER": "tenders"}], [{"LEMMA": "tender"}, {"LEMMA": "launch"}], [{"LEMMA": "request"}, {"LOWER": "for"}, {"LOWER": "proposal"}], [{"LOWER": "rfp"}], [{"LOWER": "expressions"}, {"LOWER": "of"}, {"LOWER": "interest"}], [{"LOWER": "inviting"}, {"LOWER": "bids"}] ]
            matcher.add("TENDERED_STATUS", tendered_patterns)
            planned_patterns = [ [{"LOWER": {"IN": ["project", "field", "development"]}}, {"LEMMA": "plan"}], [{"LEMMA": "plan"}, {"POS": "PART", "OP": "?"}, {"LEMMA": "to"}, {"LOWER": {"IN": ["develop", "build", "construct", "start", "proceed"]}}], [{"LOWER": "new"}, {"LOWER": {"IN": ["project", "development", "field"]}}, {"LEMMA": "propose"}], [{"LOWER": "feasibility"}, {"LOWER": "study"}], [{"LOWER": "concept"}, {"LOWER": "study"}], [{"LOWER": "pre-feed"}], [{"LOWER": "front-end"}, {"LOWER": "engineering"}, {"LOWER": "design"}], [{"LOWER": "conceptual"}, {"LOWER": "design"}], [{"LOWER": "environmental"}, {"LOWER": "impact"}, {"LOWER": "assessment"}], [{"LOWER": "considering"}, {"LOWER": "a"}, {"LOWER": {"IN": ["new", "potential"]}}, {"LOWER": "project"}], [{"LOWER": "exploring"}, {"LOWER": "options"}], [{"LOWER": "potential"}, {"LOWER": "development"}], [{"LOWER": "earmarked"}, {"LOWER": "for"}, {"LOWER": "development"}], [{"LOWER": "set"}, {"LOWER": "to"}, {"LOWER": "begin"}], [{"LOWER": "expected"}, {"LOWER": "to"}, {"LOWER": "start"}], ]
            matcher.add("PLANNED_STATUS", planned_patterns)
            under_construction_patterns = [ [{"LOWER": "under"}, {"LOWER": "construction"}], [{"LOWER": "being"}, {"LEMMA": "build"}], [{"LOWER": "ongoing"}, {"LEMMA": "develop"}], [{"LEMMA": "fabrication"}, {"LOWER": "underway"}], [{"LEMMA": "construction"}, {"LOWER": "ongoing"}], [{"LEMMA": "install"}], [{"LEMMA": "drilling"}, {"LOWER": "commence"}], [{"LOWER": "drilling"}, {"LOWER": "campaign"}], [{"LOWER": "work"}, {"LOWER": "begun"}], [{"LOWER": "construction"}, {"LEMMA": "progress"}], [{"LOWER": "hook-up"}, {"LOWER": "and"}, {"LOWER": "commissioning"}], [{"LOWER": "nearing"}, {"LOWER": "completion"}], ]
            matcher.add("UNDER_CONSTRUCTION_STATUS", under_construction_patterns)
            completed_patterns = [ [{"LEMMA": "complete"}], [{"LEMMA": "commission"}], [{"LOWER": "online"}], [{"LEMMA": "production"}, {"LEMMA": "start"}], [{"LOWER": "handed"}, {"LOWER": "over"}], [{"LEMMA": "deliver"}], [{"LEMMA": "achieve"}, {"LOWER": "first"}, {"LOWER": "oil"}], [{"LOWER": "first"}, {"LOWER": "gas"}], [{"LOWER": "brought"}, {"LOWER": "into"}, {"LOWER": "production"}], [{"LOWER": "commence"}, {"LOWER": "production"}], [{"LOWER": "fully"}, {"LOWER": "operational"}], [{"LOWER": "production"}, {"LOWER": "began"}] ]
            matcher.add("COMPLETED_STATUS", completed_patterns)
            delayed_patterns = [ [{"LEMMA": {"IN": ["delay", "postpone", "reschedule", "defer", "stall", "halt"]}}], [{"LOWER": "push"}, {"LOWER": "back"}], [{"LOWER": "pushed"}, {"LOWER": "out"}], [{"LEMMA": "setback"}], [{"LEMMA": "deferment"}], [{"LOWER": "on"}, {"LOWER": "hold"}], [{"LEMMA": "suspension"}], [{"LEMMA": "slippage"}], [{"LOWER": "behind"}, {"LOWER": "schedule"}], [{"LOWER": "timeline"}, {"LEMMA": "extension"}], [{"LEMMA": "late"}], [{"LOWER": "running"}, {"LOWER": "late"}], [{"LOWER": "experiencing"}, {"LEMMA": "delay", "OP": "+"}], [{"LEMMA": "face"}, {"LEMMA": "delay", "OP": "+"}] ]
            matcher.add("DELAYED_STATUS", delayed_patterns)
            cancelled_patterns = [ [{"LEMMA": {"IN": ["cancel", "scrap", "terminate", "shelve", "withdraw"]}}], [{"LEMMA": "abandon"}, {"LOWER": {"IN": ["project", "plan", "development", "effort", "initiative"]}}], [{"LEMMA": "halted"}], [{"LOWER": "not"}, {"LOWER": "proceed"}], [{"LOWER": "no"}, {"LOWER": "longer"}, {"LOWER": "planned"}], [{"LOWER": "no"}, {"LOWER": "longer"}, {"LEMMA": "pursue"}], [{"LOWER": "project"}, {"LOWER": "fail"}], [{"LOWER": {"IN": ["contract", "agreement"]}}, {"LEMMA": "terminate"}], [{"LOWER": "project"}, {"LEMMA": "terminate"}], [{"LOWER": "pull"}, {"LOWER": "the"}, {"LOWER": "plug"}], [{"LOWER": "put"}, {"LOWER": "on"}, {"LOWER": "ice"}], [{"LEMMA": "suspend"}, {"LOWER": "indefinitely"}] ]
            matcher.add("CANCELLED_STATUS", cancelled_patterns)
            fid_patterns = [ [{"LOWER": "final"}, {"LOWER": "investment"}, {"LOWER": "decision"}], [{"LOWER": "fid"}] ]
            matcher.add("FID_STATUS", fid_patterns)
            matches = matcher(doc)
            for match_id, start, end in matches:
                string_id = nlp.vocab.strings[match_id]
                status_map = { "AWARDED_STATUS": 'awarded', "TENDERED_STATUS": 'tendered', "PLANNED_STATUS": 'planned', "UNDER_CONSTRUCTION_STATUS": 'under construction', "COMPLETED_STATUS": 'completed', "DELAYED_STATUS": 'delayed', "CANCELLED_STATUS": 'cancelled', "FID_STATUS": 'FID', "DECOMMISSIONING_STATUS": 'decommissioning' }
                if string_id in status_map:
                    found_statuses.add(status_map[string_id])
            priority_order = ['cancelled', 'decommissioning', 'completed', 'delayed', 'FID', 'awarded', 'under construction', 'tendered', 'planned']
            for status in priority_order:
                if status in found_statuses:
                    return status
            return ''

        def find_capacity_subject(capacity_span, doc):
            verb = None
            for ancestor in capacity_span.root.ancestors:
                if ancestor.pos_ == "VERB":
                    verb = ancestor
                    break
            if verb:
                subjects = [child for child in verb.children if child.dep_ in ("nsubj", "nsubjpass")]
                if subjects:
                    subject_root = subjects[0]
                    for chunk in doc.noun_chunks:
                        if subject_root in chunk:
                            name = " ".join(tok.text for tok in chunk if tok.pos_ not in ['DET', 'PRON'])
                            return name.strip()
            if capacity_span.root.head.text.lower() in ['of', 'for']:
                owner = capacity_span.root.head.head
                for chunk in doc.noun_chunks:
                    if owner in chunk:
                        name = " ".join(tok.text for tok in chunk if tok.pos_ not in ['DET', 'PRON'])
                        if name.lower() not in ["capacity", "production", "output", "throughput"]:
                            return name.strip()
            window_start = max(0, capacity_span.start - 15)
            context_window_chunks = [chunk for chunk in doc.noun_chunks if chunk.end <= capacity_span.start and chunk.start >= window_start]
            for chunk in reversed(context_window_chunks):
                chunk_text_lower = chunk.text.lower()
                if any(kw in chunk_text_lower for keywords in ENTITY_KEYWORDS_FOR_CAPACITY.values() for kw in keywords):
                    name = " ".join(tok.text for tok in chunk if tok.pos_ not in ['DET', 'PRON'])
                    return name.strip()
            sent = capacity_span.sent
            for entity_type, keywords in ENTITY_KEYWORDS_FOR_CAPACITY.items():
                if any(kw in sent.text.lower() for kw in keywords):
                    return f"({entity_type})"
            return None

        def extract_production_capacity_refined(text):
            text = clean_text(text)
            if not text: return ''
            doc = nlp(text)
            extracted_capacities = set()
            CAPACITY_UNITS_REGEX = r"bpd|boe/d|boepd|mmscfd|scfd|tpd|mcfd|bbl/d|bcfd|mboed|tcf/d|mcm/d|gj/d|tonnes/year|t/y|t/d|barrels of oil equivalent per day|cubic feet per day|m3/d|tonne/day|barrels per day|cubic meters per day|tonnes per day"
            CAPACITY_NOUNS_REGEX = r"barrels|cubic|feet|meters|tonnes|bbl|cf|m3|boe"
            TIME_UNITS_REGEX = r"day|d|hour|hr|h|year|yr|y|annum"
            capacity_matcher = Matcher(nlp.vocab)
            pattern1 = [ {"LIKE_NUM": True}, {"LOWER": {"IN": ["million", "billion", "thousand", "mn", "bn", "k"]}, "OP": "?"}, {"LOWER": {"REGEX": CAPACITY_UNITS_REGEX}}, ]
            pattern2 = [ {"LIKE_NUM": True}, {"LOWER": {"IN": ["million", "billion", "thousand", "mn", "bn", "k"]}}, {"LOWER": {"REGEX": CAPACITY_NOUNS_REGEX}}, {"LOWER": "per"}, {"LOWER": {"REGEX": TIME_UNITS_REGEX}}, ]
            pattern3 = [ {"LIKE_NUM": True}, {"LOWER": {"REGEX": CAPACITY_NOUNS_REGEX}}, {"LOWER": "per", "OP": "?"}, {"LOWER": {"REGEX": TIME_UNITS_REGEX}, "OP": "?"}, ]
            capacity_matcher.add("PRODUCTION_CAPACITY", [pattern1, pattern2, pattern3])
            matches = capacity_matcher(doc)    
            spans = [doc[start:end] for _, start, end in matches]
            filtered_spans = spacy.util.filter_spans(spans)
            for span in filtered_spans:
                is_irrelevant = any(ent.label_ in ['DATE', 'MONEY'] for ent in span.sent.ents if ent.start < span.end and ent.end > span.start)
                if is_irrelevant: continue
                capacity_text = " ".join(span.text.split())
                subject = find_capacity_subject(span, doc)
                if subject:
                    if subject.startswith("(") and subject.endswith(")"):
                        extracted_capacities.add(f"{capacity_text} {subject}")
                    else:
                        extracted_capacities.add(f"{subject}: {capacity_text}")
                else:
                    extracted_capacities.add(capacity_text)
            return ', '.join(sorted(list(extracted_capacities)))

        def extract_contract_types(text):
            text = clean_text(text)
            if not text: return ''
            contract_keywords_list = [ 'EPC', 'EPCI', 'EPCC', 'FEED', 'LSTK', 'MOU', 'joint venture', 'framework agreement', 'EPMC', 'EPC-E', 'EPC-E/E', 'service agreement', 'subcontract', 'supply agreement', 'alliance agreement', 'lease agreement', 'charter agreement', 'drilling contract', 'construction contract', 'maintenance contract', 'operation and maintenance', 'O&M', 'engineering contract', 'procurement contract', 'turnkey contract', 'build-own-operate-transfer', 'BOOT', 'production sharing agreement', 'PSA', 'rig contract', 'vessel contract', 'consultancy contract' ]
            doc = nlp(text)
            found_contract_types = set()
            matcher = Matcher(nlp.vocab)
            pattern1 = [ {"LOWER": {"IN": [k.lower() for k in contract_keywords_list]}}, {"LEMMA": {"IN": ["contract", "agreement", "deal", "accord", "pact", "charter", "lease", "terms"]}} ]
            matcher.add("CONTRACT_TYPE_PHRASE_1", [pattern1])
            pattern2 = [ {"LEMMA": {"IN": ["contract", "agreement"]}}, {"LOWER": {"IN": ["for", "to"]}, "OP": "?"}, {"LOWER": {"IN": ["the", "provide"]}, "OP": "?"}, {"LOWER": "of", "OP": "?"}, {"LOWER": {"IN": [k.lower() for k in contract_keywords_list]}} ]
            matcher.add("CONTRACT_TYPE_PHRASE_2", [pattern2])
            pattern3 = [ {"LEMMA": {"IN": ["award", "sign", "secure", "win", "enter", "finalize", "negotiate", "issue", "grant", "land"]}}, {"LOWER": {"IN": ["a", "an", "the"]}, "OP": "?"}, {"LOWER": {"IN": [k.lower() for k in contract_keywords_list]}}, {"LEMMA": {"IN": ["contract", "agreement", "deal"]}, "OP": "?"} ]
            matcher.add("VERB_CONTRACT_TYPE", [pattern3])
            matches = matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                span_text_lower = span.text.lower()
                best_found_kw = ""
                for canonical_kw in contract_keywords_list:
                    if re.search(r'\b' + re.escape(canonical_kw.lower()) + r'\b', span_text_lower):
                        if len(canonical_kw) > len(best_found_kw):
                            best_found_kw = canonical_kw
                if best_found_kw:
                    found_contract_types.add(best_found_kw)
            if not found_contract_types:
                for ct in contract_keywords_list:
                    if re.search(r'\b' + re.escape(ct) + r'\b', text, re.IGNORECASE):
                        found_contract_types.add(ct)
            return ', '.join(sorted(list(found_contract_types)))

        def summarize_text_textrank(text, num_sentences=3, diversity_lambda=0.6):
            text = clean_text(text)
            if not text:
                return ''
            doc = nlp(text)
            sentences = [sent for sent in doc.sents if len(sent.text.strip()) > 5 and sent.vector_norm]
            if not sentences or len(sentences) <= num_sentences:
                original_sents = list(doc.sents)
                return ' '.join([s.text.replace('\n', ' ').strip() for s in original_sents[:num_sentences]])
            sentence_vectors = np.array([sent.vector for sent in sentences])
            similarity_matrix = cosine_similarity(sentence_vectors)
            initial_scores = np.ones(len(sentences))
            status_keywords = ['award', 'complete', 'delay', 'cancel', 'fid', 'tender', 'plan', 'construct', 'decommission', 'sign', 'secure']
            for i, sent in enumerate(sentences):
                if any(ent.label_ in ['ORG', 'PRODUCT', 'FAC', 'GPE', 'MONEY'] for ent in sent.ents):
                    initial_scores[i] += 0.3
                if any(keyword in sent.text.lower() for keyword in status_keywords):
                    initial_scores[i] += 0.4
                if i == 0:
                    initial_scores[i] += 0.5
            scores = np.copy(initial_scores)
            damping_factor = 0.85
            try:
                for _ in range(100):
                    prev_scores = np.copy(scores)
                    for i in range(len(sentences)):
                        rank_sum = sum( (similarity_matrix[j][i] * prev_scores[j]) / (np.sum(similarity_matrix[j]) or 1) for j in range(len(sentences)) if i != j )
                        scores[i] = (1 - damping_factor) * initial_scores[i] + damping_factor * rank_sum
                    if np.sum(np.abs(scores - prev_scores)) < 1e-5:
                        break
            except (ValueError, IndexError):
                pass
            selected_indices = []
            try:
                candidate_indices = list(range(len(sentences)))
                best_start_idx = np.argmax(scores)
                selected_indices.append(best_start_idx)
                candidate_indices.remove(best_start_idx)
                while len(selected_indices) < num_sentences and candidate_indices:
                    mmr_scores = []
                    for i in candidate_indices:
                        relevance_score = scores[i]
                        redundancy_score = max(similarity_matrix[i][j] for j in selected_indices)
                        mmr = diversity_lambda * relevance_score - (1 - diversity_lambda) * redundancy_score
                        mmr_scores.append((mmr, i))
                    if not mmr_scores: break
                    best_next_idx = max(mmr_scores)[1]
                    selected_indices.append(best_next_idx)
                    candidate_indices.remove(best_next_idx)
            except (ValueError, IndexError):
                selected_indices = []
            if not selected_indices:
                ranked_sentence_indices = scores.argsort()[-num_sentences:][::-1]
                selected_indices = list(ranked_sentence_indices)
            sorted_indices = sorted(selected_indices)
            summary_sentences = [sentences[i].text.replace('\n', ' ').strip() for i in sorted_indices]
            if not summary_sentences:
                original_sents = list(doc.sents)
                return ' '.join([s.text.replace('\n', ' ').strip() for s in original_sents[:num_sentences]])
            return ' '.join(summary_sentences)

        def classify_offshore_onshore(text):
            text = clean_text(text).lower()
            offshore_keywords = { 'offshore': 3, 'subsea': 3, 'fpso': 4, 'flng': 4, 'fsru': 4, 'floating': 2, 'deepwater': 2, 'mooring': 2, 'riser': 2, 'jack-up': 3, 'drillship': 3, 'spar': 3, 'tlp': 3, 'platform': 2, 'jacket': 2, 'hull': 1, 'caisson': 1, 'umbilical': 2, 'flowline': 2, 'topside': 2, 'topsides': 2, 'wellhead': 1, 'manifold': 1, 'christmas tree': 1, 'surf': 3, 'gbs': 2, 'sea bed': 2, 'marine': 2, 'vessel': 1, 'installation vessel': 3, 'anchor handling tug': 2, 'hook-up': 2, 'commissioning (offshore)': 3, 'offshore removal': 3, 'semisubmersible': 3, 'drilling rig': 2 }
            onshore_keywords = { 'onshore': 3, 'land-based': 3, 'refinery': 4, 'petrochemical': 4, 'gas plant': 3, 'pipeline terminal': 2, 'compressor station': 2, 'gas treatment': 2, 'processing plant': 3, 'storage tank': 1, 'industrial complex': 2, 'onshore disposal': 3, 'midstream': 1, 'downstream': 1, 'lng terminal': 3, 'storage facility': 2, 'gas processing plant': 3 }
            offshore_score = sum(score for kw, score in offshore_keywords.items() if kw in text)
            onshore_score = sum(score for kw, score in onshore_keywords.items() if kw in text)
            for keyword in BUILD_PARTS.union(BUILD_PROCESS_OPTIONS):
                kw_lower = keyword.lower()
                if kw_lower in text:
                    if "subsea" in kw_lower or "offshore" in kw_lower or kw_lower in ['fpso', 'flng', 'fsru', 'tlp', 'spar', 'jacket', 'hull']:
                        offshore_score += 1.5
                    elif "topsides" in kw_lower: offshore_score += 0.5 
                    elif "pipeline" in kw_lower:
                        if 'subsea pipeline' in text: offshore_score += 1.5
                        elif 'onshore pipeline' in text: onshore_score += 1.5
                    elif "offshore removal" in kw_lower: offshore_score += 2
                    elif "onshore disposal" in kw_lower: onshore_score += 2
                    elif "installation" in kw_lower:
                        if 'subsea installation' in text or 'offshore installation' in text: offshore_score += 1.5
                        elif 'onshore installation' in text: onshore_score += 1.5
                    elif "decommissioning" in kw_lower:
                        if 'offshore decommissioning' in text: offshore_score += 1.5
                        elif 'onshore decommissioning' in text: onshore_score += 1.5 
            if len(text.split()) < 20 and offshore_score > 0 and onshore_score > 0:
                if offshore_score == onshore_score: return 'Unclear'
                return 'Offshore' if offshore_score > onshore_score * 2 else ('Onshore' if onshore_score > onshore_score * 2 else 'Mixed')
            if offshore_score > onshore_score: return 'Offshore'
            if onshore_score > offshore_score: return 'Onshore'
            if offshore_score > 0 or onshore_score > 0: return 'Mixed'
            return 'Unclear'

        def generate_ai_opinion(row, _):
            project_names = row.get('Field/Project Names', '')
            companies = row.get('Operators/Companies', '')
            locations = row.get('Locations', '')
            project_status = row.get('Project Status', '')
            scope_details = row.get('Scope Details', '')
            offshore_onshore = row.get('Offshore/Onshore Classification', '')
            budget = row.get('Budget / Value', '')
            production_capacity = row.get('Production Capacity', '')
            contract_types = row.get('Contract Types', '')
            specifications = row.get('Build Part Specifications', '')
            vessel_info = row.get('Vessel Info', '')
            delays_dates = row.get('Delays / Dates', '')
            summary = row.get('Summary', '')
            main_subject = "An upstream energy project"
            company_subject = ""
            if project_names:
                project_list = project_names.split(', ')
                main_subject = f"The {project_list[0]} project"
                if len(project_list) > 1:
                    main_subject += " and related developments"
            elif companies:
                company_list = companies.split(', ')
                company_subject = f"{company_list[0]}"
                if len(company_list) > 1:
                    company_subject += " and its partners"
                main_subject = f"A project led by {company_subject}"
            lead_sentence = ""
            if project_status in ['cancelled', 'delayed']:
                status_verb = "been cancelled" if project_status == 'cancelled' else "is facing significant delays"
                date_info = f", with the timeline reportedly pushed to {delays_dates.split(', ')[0]}" if delays_dates else ""
                lead_sentence = f"In a critical update, {main_subject} has {status_verb}{date_info}."
            elif project_status in ['completed', 'FID']:
                milestone = "completion and has come online" if project_status == 'completed' else "reached a Final Investment Decision (FID)"
                lead_sentence = f"{main_subject} has achieved a major milestone, having reached {milestone}."
            elif project_status == 'awarded':
                contract_info = f"a key {contract_types.split(', ')[0]} contract" if contract_types else "a significant contract"
                company_info = f"{company_subject} has secured" if company_subject else "A contract has been secured for"
                vessel_subject = f" for the charter of the {vessel_info.split(' (')[0]}" if vessel_info else ""
                lead_sentence = f"Signaling a major step forward, {company_info} {contract_info}{vessel_subject} for the project."
            elif project_status in ['planned', 'tendered']:
                stage_phrase = "is in the tendering phase" if project_status == 'tendered' else "is in the early planning and design stages"
                lead_sentence = f"The {offshore_onshore.lower() if offshore_onshore not in ['Unclear', 'Mixed'] else 'energy'} sector sees new potential as {main_subject} {stage_phrase}."
            elif project_status == 'under construction':
                lead_sentence = f"Development is actively progressing for {main_subject}, which is now under construction."
            elif project_status == 'decommissioning':
                lead_sentence = f"At the end of its lifecycle, {main_subject} is now undergoing decommissioning."
            if not lead_sentence:
                if project_names and locations:
                    lead_sentence = f"An update has been provided on {main_subject}, located in {locations.split(', ')[0]}."
                elif companies and locations:
                    lead_sentence = f"{company_subject} is advancing an upstream project in {locations.split(', ')[0]}."
                else:
                    if summary: return summary.split('.')[0] + "."
                    if companies: return f"{companies.split(', ')[0]} is making an upstream move."
                    return "General upstream oil and gas news."
            supporting_details = []
            if vessel_info:
                if not (lead_sentence and vessel_info.split(' (')[0] in lead_sentence):
                    supporting_details.append(f"The agreement involves the vessel {vessel_info.split(' (')[0]}.")
            if locations and locations.split(', ')[0] not in lead_sentence:
                loc_text = f"located in {locations.split(', ')[0]}"
                type_text = f"as an {offshore_onshore.lower()} development" if offshore_onshore not in ['Unclear', 'Mixed'] else ""
                if type_text:
                    supporting_details.append(f"The project is {loc_text} and is classified {type_text}.")
                else:
                    supporting_details.append(f"The project is {loc_text}.")
            if scope_details:
                scope_list = [s.strip().lower() for s in scope_details.split(',')]
                scope_groups = { 'full-field development (EPCI)': ['epc', 'epci', 'epcc'], 'SURF package': ['surf', 'pipelines', 'flowlines', 'riser', 'umbilical'], 'subsea production systems': ['subsea systems', 'tree', 'manifold', 'wellhead'], 'floating facilities': ['fpso', 'flng', 'fsru', 'tlp', 'spar'], 'fixed structures': ['jacket', 'hull', 'topside', 'topsides'], 'decommissioning activities': ['decommissioning'] }
                found_groups = [group_name for group_name, keywords in scope_groups.items() if any(kw in scope_list for kw in keywords)]
                if found_groups:
                    scope_summary = " and ".join(found_groups)
                    supporting_details.append(f"Its scope is comprehensive, focusing on {scope_summary}.")
                elif scope_list:
                    supporting_details.append(f"The work includes {scope_list[0]} and other related activities.")
            financials = []
            if budget:
                financials.append(f"a reported budget of {budget.split(', ')[0]}")
            if production_capacity:
                cap_str = production_capacity.split(', ')[0]
                if ":" in cap_str: cap_str = cap_str.split(':')[1].strip()
                financials.append(f"a targeted production capacity of {cap_str}")
            if financials:
                supporting_details.append(f"This is a significant undertaking with {' and '.join(financials)}.")
            if specifications and not any("scope" in s or "SURF" in s or "subsea" in s for s in supporting_details):
                spec_summary = specifications.split(', ')[0]
                supporting_details.append(f"Key technical elements include a {spec_summary}.")
            opinion_parts = [lead_sentence] + supporting_details
            final_opinion = " ".join(opinion_parts)
            final_opinion = re.sub(r'\s+', ' ', final_opinion).strip()
            if len(final_opinion) > 250:
                doc = nlp(final_opinion)
                sents = list(doc.sents)
                truncated_opinion = ""
                for sent in sents:
                    if len(truncated_opinion) + len(sent.text) < 240:
                        truncated_opinion += sent.text + " "
                    else:
                        break
                final_opinion = truncated_opinion.strip()
            if not final_opinion.strip():
                if summary: return summary.split('.')[0] + "."
                if companies and locations: return f"{companies.split(', ')[0]} is active in {locations.split(', ')[0]}."
                if companies: return f"{companies.split(', ')[0]} is making an upstream move."
                return "General upstream oil and gas news."
            return final_opinion

        def extract_packages_phases_refined(text):
            text = clean_text(text)
            if not text:
                return ''
            doc = nlp(text)
            found_items = set()
            matcher = Matcher(nlp.vocab)
            pattern_standard = [ {"LOWER": {"IN": ["phase", "package", "epci"]}}, {"IS_ALPHA": True, "OP": "?"}, {"IS_DIGIT": True, "OP": "?"}, {"SHAPE": {"REGEX": "^(d|dd|X|XX|Xx)$"}, "OP": "?"} ]
            matcher.add("STANDARD_PKG_PHASE", [pattern_standard])
            pattern_phase_word_num = [ {"LOWER": "phase"}, {"LOWER": {"IN": ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "first", "second", "third", "fourth", "fifth", "final", "next", "initial", "main"]}} ]
            matcher.add("PHASE_WORD_NUM", [pattern_phase_word_num])
            pattern_package_letter = [{"LOWER": "package"}, {"IS_UPPER": True, "LENGTH": 1}]
            matcher.add("PACKAGE_LETTER", [pattern_package_letter])
            pattern_descriptive_package = [ {"LOWER": {"IN": ["work", "contract", "subsea", "topsides", "drilling", "pipeline"]}}, {"LOWER": "package"}, {"IS_ALPHA": True, "OP": "?"}, {"IS_DIGIT": True, "OP": "?"}, {"SHAPE": {"REGEX": "^(d|dd|X|XX|Xx)$"}, "OP": "?"} ]
            matcher.add("DESCRIPTIVE_PACKAGE", [pattern_descriptive_package])
            pattern_phase_roman = [{"LOWER": "phase"}, {"TEXT": {"REGEX": r"^[IVXLCDM]+$"}, "OP": "+"}]
            matcher.add("PHASE_ROMAN", [pattern_phase_roman])
            matches = matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                if 3 < len(span.text) <= 30 and len(span.text.split()) <= 4 :
                    found_items.add(span.text.strip())
            regex_fallback = re.findall( r'\b(Package\s*[A-Z0-9]+|EPCI\s*\d*|Phase\s*(?:\d+|[IVXLCDM]+(?:st|nd|rd|th)?|[Oo]ne|[Tt]wo|[Tt]hree|[Ff]irst|[Ss]econd|[Tt]hird|[Ff]inal))\b', text, re.IGNORECASE )
            for item_match_group in regex_fallback:
                item_match = item_match_group if isinstance(item_match_group, str) else item_match_group[0]
                cleaned_item = " ".join(item_match.split()) 
                if len(cleaned_item) > 3:
                    if cleaned_item.lower() not in ["phase", "package", "epci"]:
                        found_items.add(cleaned_item)
            final_items = {item for item in found_items if item.lower() not in ["phase", "package", "epci"] or len(item.split()) > 1}
            return ', '.join(sorted(list(final_items)))

        # --- Main Processing (wrapped in a function to use nested helpers) ---
        def main():
            tqdm.pandas(desc="Processing news articles")
            worker.progress.emit(1)
            
            # This is your original Tkinter file dialog logic. It is preserved.
            # It will likely cause a crash or freeze if called from this thread.
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename( title="Select Input Excel File", filetypes=(("Excel files", "*.xlsx *.xls"), ("All files", "*.*")) )
            if not file_path:
                print("No file selected. Exiting.")
                return
            print(f"Loading Excel file: {file_path}")
            worker.progress.emit(5)
            
            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                print(f"Error loading file '{file_path}': {e}")
                return

            news_col_name = None
            if "Content" in df.columns and not df["Content"].isnull().all():
                news_col_name = "Content"
            elif "News" in df.columns and not df["News"].isnull().all():
                news_col_name = "News"
            elif len(df.columns) >= 4 and not df.iloc[:, 3].isnull().all():
                news_col_name = df.columns[3]
                print(f"Warning: Using column '{news_col_name}' for news content.")
            elif len(df.columns) >= 1 and not df.iloc[:, 0].isnull().all():
                news_col_name = df.columns[0]
                print(f"Warning: Using column '{news_col_name}' for news content.")
            
            if news_col_name is None:
                print("Error: Could not find a suitable column for news content.")
                return

            print(f"Using column '{news_col_name}' for news content.")
            print("Starting structured data extraction...")
            df['Cleaned Text'] = df[news_col_name].apply(clean_text)

            extraction_pipeline = {
                'Field/Project Names': extract_project_profiles,
                'Operators/Companies': lambda x: extract_entities_by_label_refined(x, ['ORG']),
                'Locations': lambda x: extract_entities_by_label_refined(x, ['GPE', 'LOC']),
                'Packages/Phases': extract_packages_phases_refined,
                'Vessel Info': extract_vessel_details,
                'Build Part Specifications': extract_build_part_specifications,
                'Scope Details': extract_scope_keywords,
                'Delays / Dates': extract_delays_dates,
                'Budget / Value': extract_budget,
                'Quotes / Opinions': extract_quotes,
                'Project Status': extract_project_status,
                'Production Capacity': extract_production_capacity_refined,
                'Contract Types': extract_contract_types,
                'Offshore/Onshore Classification': classify_offshore_onshore,
                'Summary': lambda x: summarize_text_textrank(x, num_sentences=3)
            }
            
            total_steps = len(extraction_pipeline) + 2 # +1 for AI opinion, +1 for saving
            for i, (col_name, func) in enumerate(extraction_pipeline.items()):
                print(f"Analyzing: {col_name}...")
                df[col_name] = df['Cleaned Text'].progress_apply(func)
                progress = int(((i + 1) / total_steps) * 100)
                worker.progress.emit(progress)

            print("Generating AI Opinion...")
            df['AI Opinion'] = df.progress_apply(lambda row: generate_ai_opinion(row, row['Cleaned Text']), axis=1)
            worker.progress.emit(int(((total_steps - 1) / total_steps) * 100))
            df.drop(columns=['Cleaned Text'], inplace=True)
            
            try:
                df.to_excel(OUTPUT_PATH, index=False)
                print(f"✅ File saved to: {OUTPUT_PATH}")
            except Exception as e:
                print(f"An unexpected error occurred while saving the file: {e}")
            
            # Emit results for the dashboard
            status_counts = df['Project Status'].value_counts().to_dict()
            location_counts = df['Locations'].str.split(r',|;').explode().str.strip().value_counts().nlargest(10).to_dict()
            type_counts = df['Offshore/Onshore Classification'].value_counts().to_dict()
            worker.results.emit({
                "status_counts": status_counts,
                "location_counts": location_counts,
                "type_counts": type_counts
            })
            worker.progress.emit(100)

        # --- Entry Point of the original script ---
        main()


    def update_dashboard_charts(self, data: dict):
        self.status_chart_canvas.figure.clear()
        ax1 = self.status_chart_canvas.figure.add_subplot(111)
        status_data = data.get("status_counts", {})
        if status_data:
            ax1.pie(status_data.values(), labels=status_data.keys(), autopct='%1.1f%%', startangle=90, textprops={'color':"w"})
        ax1.set_title("Project Status Overview", color='white')
        self.status_chart_canvas.draw()

        self.location_chart_canvas.figure.clear()
        ax2 = self.location_chart_canvas.figure.add_subplot(111)
        location_data = data.get("location_counts", {})
        if location_data:
            labels = [loc.strip() for loc, count in location_data.items() if loc.strip()]
            values = [count for loc, count in location_data.items() if loc.strip()]
            ax2.barh(labels, values, color='#5d9cec')
            ax2.invert_yaxis()
        ax2.set_title("Top 10 Locations", color='white')
        ax2.set_facecolor('#34495e')
        ax2.tick_params(colors='white')
        self.location_chart_canvas.figure.tight_layout()
        self.location_chart_canvas.draw()

        self.type_chart_canvas.figure.clear()
        ax3 = self.type_chart_canvas.figure.add_subplot(111)
        type_data = data.get("type_counts", {})
        if type_data:
            ax3.bar(type_data.keys(), type_data.values(), color=['#2ecc71', '#e74c3c', '#f1c40f'])
        ax3.set_title("Onshore vs. Offshore", color='white')
        ax3.set_facecolor('#34495e')
        ax3.tick_params(colors='white')
        self.type_chart_canvas.draw()

def run_app():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
import os
import time
from datetime import date, datetime, timedelta
from tkinter import Tk, Label, Button
from tkcalendar import Calendar
from selenium import webdriver
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
try:
    from dateutil.parser import parse as dateutil_parse
except ImportError:
    print("Warning: 'python-dateutil' library not found. Date parsing will be less robust.")
    print("Install it using: pip install python-dateutil")
    dateutil_parse = None
try:
    import requests
except ImportError:
    print("Warning: 'requests' library not found. Online year verification is disabled.")
    print("Install it using: pip install requests")
    requests = None
import re

# --- Configuration ---
PROFILE_PATH = r"C:\Users\i60475\AppData\Local\Google\Chrome\User Data\Selenium"
WAIT_TIMEOUT = 20
IMPLICIT_WAIT = 5
BASE_URL = "https://www.upstreamonline.com/latest"
OUTPUT_DIR = "C:/Office work/Upstream SCRAP news"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
# --- End Configuration ---

# --- GUI Popup for Calendar Date Selection ---
def select_date_range():
    start_date = None
    end_date = None

    def on_select_dates():
        nonlocal start_date, end_date
        start_date_str = start_date_calendar.get_date()
        end_date_str = end_date_calendar.get_date()
        start_date = datetime.strptime(start_date_str, "%m/%d/%y").date()
        end_date = datetime.strptime(end_date_str, "%m/%d/%y").date()
        date_window.destroy()

    date_window = Tk()
    date_window.title("Select Date Range")
    date_window.geometry("400x300")

    Label(date_window, text="Select Start Date:", font=("Arial", 12)).pack(pady=10)
    start_date_calendar = Calendar(date_window, date_pattern="mm/dd/yy", selectmode='day')
    start_date_calendar.pack(pady=10)

    Label(date_window, text="Select End Date:", font=("Arial", 12)).pack(pady=10)
    end_date_calendar = Calendar(date_window, date_pattern="mm/dd/yy", selectmode='day')
    end_date_calendar.pack(pady=10)

    Button(date_window, text="Confirm", command=on_select_dates, font=("Arial", 12)).pack(pady=20)
    date_window.mainloop()

    return start_date, end_date

# --- Extract Article Links and Titles ---
def get_article_links_and_titles(soup):
    articles = []
    # Use a set to prevent adding duplicate links if they are found by multiple selectors or exist on the page twice.
    seen_hrefs = set()

    # The selector is broadened from "a.card-link.text-reset" to just "a.card-link".
    # This is more robust because it finds any article link in a card, even if its
    # other styling classes (like 'text-reset') are different. This prevents the
    # scraper from missing articles with slightly different HTML structures.
    for link in soup.select("a.card-link"):
        href = link.get("href")
        title = link.get_text(strip=True)

        # New check: Ensure the link looks like an article URL and not a category page.
        # Article URLs on Upstream typically contain a pattern like '/2-1-1234567'.
        if href and title and href not in seen_hrefs and re.search(r'/2-1-\d+$', href):
            full_link = href if href.startswith("https://") else f"https://www.upstreamonline.com{href}"
            articles.append((full_link, title))
            seen_hrefs.add(href)
            print(f"Found article link: {title}")
        elif href and title and href not in seen_hrefs:
            # This will log the links that are being skipped, making the output clearer.
            print(f"ℹ️ Skipping non-article link: {title} ({href})")
            seen_hrefs.add(href) # Add to seen even if skipped to avoid re-logging
    return articles

# --- Extract Article Details ---
def extract_article_details(driver, link):
    driver.get(link)

    WebDriverWait(driver, WAIT_TIMEOUT).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2) # Allow dynamic content to load

    article_soup = BeautifulSoup(driver.page_source, "html.parser")

    date_element = article_soup.find("span", class_="dn-date-time")
    date_published = "No Date Found"
    if date_element:
        date_text = date_element.get_text(strip=True).replace("Published", "").replace("GMT", "").strip()
        # New: Remove "Updated" prefix if present
        if date_text.lower().startswith("updated"):
            date_text = date_text[len("updated"):].strip()
        
        print(f"Attempting to parse cleaned date string: '{date_text}' for URL: {link}")

        current_datetime = datetime.now()
        parsed_dt_obj = None

        # 1. Handle relative time formats first (e.g., "X minutes ago", "today", "yesterday")
        relative_time_match = re.search(r'(\d+)\s+(minute|hour|day|week|month)s?\s+ago', date_text, re.IGNORECASE)
        if relative_time_match:
            value = int(relative_time_match.group(1))
            unit = relative_time_match.group(2).lower()
            
            if unit == 'minute':
                parsed_dt_obj = current_datetime - timedelta(minutes=value)
            elif unit == 'hour':
                parsed_dt_obj = current_datetime - timedelta(hours=value)
            elif unit == 'day':
                parsed_dt_obj = current_datetime - timedelta(days=value)
            elif unit == 'week':
                parsed_dt_obj = current_datetime - timedelta(weeks=value)
            elif unit == 'month':
                # timedelta doesn't have months, so approximate as 30 days
                parsed_dt_obj = current_datetime - timedelta(days=value * 30)
        elif "yesterday" in date_text.lower():
            parsed_dt_obj = current_datetime - timedelta(days=1)
        elif "today" in date_text.lower():
            parsed_dt_obj = current_datetime
        elif dateutil_parse:
            # 2. Use dateutil for other formats (e.g., "27 June 2024", "June 27")
            try:
                # The fuzzy=False argument is safer to avoid misinterpreting surrounding text.
                datetime_object = dateutil_parse(date_text, fuzzy=False) 
                parsed_dt_obj = datetime_object
            except (ValueError, TypeError) as e:
                print(f"❌ Date format not recognized by dateutil: '{date_text}' for URL: {link} - Error: {e}")
        else:
            # 3. Fallback to strptime if dateutil is not installed
            try:
                datetime_object = datetime.strptime(date_text, '%d %B %Y, %H:%M')
                parsed_dt_obj = datetime_object
            except ValueError:
                try:
                    datetime_object = datetime.strptime(date_text, '%d %B %Y')
                    parsed_dt_obj = datetime_object
                except ValueError:
                    print(f"❌ Date format not recognized: '{date_text}' for URL: {link}")

        if parsed_dt_obj:
            # Heuristic for year correction: If the parsed date is in the future,
            # it's likely from the previous year (e.g., "Dec 31" parsed in Jan as current year).
            # This handles cases where the system clock might be ahead or the website doesn't specify year for recent articles.
            if parsed_dt_obj.date() > current_datetime.date() + timedelta(days=1): # If more than 1 day in future
                # Try subtracting a year if it makes sense (i.e., brings it to current or past year)
                temp_date_minus_year = parsed_dt_obj.replace(year=parsed_dt_obj.year - 1).date()
                if temp_date_minus_year <= current_datetime.date():
                    date_published = temp_date_minus_year
                    print(f"💡 Adjusted future date {parsed_dt_obj.date()} to {date_published} (subtracted 1 year).")
                else:
                    # Still in future or doesn't make sense, treat as unparseable for now
                    print(f"⚠️ Parsed date {parsed_dt_obj.date()} is significantly in the future. Treating as unparseable for now.")
                    date_published = "No Date Found" # Treat as unparseable
            else:
                date_published = parsed_dt_obj.date()
        else:
            date_published = "No Date Found" # Ensure it's set if parsing failed

    article_content = "No Content Found"
    main_content_container = None

    # Try a list of preferred selectors, from most specific to more general
    preferred_selectors = [
        "div.article-body__content",  # Specific to Upstream
        "article[class*='article-body']",
        "div[class*='article-body']",
        "div[class*='story-content']", # Common general content class
        "div[class*='post-content']",
        "div[class*='main-content']",
        "div[class*='content-area']",
        "article[class*='content']", # General article tag with 'content' in class
        "section[class*='content']", # General section tag with 'content' in class
        "div[class*='content']", # General div with 'content' in class
    ]

    for selector in preferred_selectors:
        candidate_container = article_soup.select_one(selector)
        if candidate_container:
            # Basic check: does it have a few paragraphs? Avoid tiny, irrelevant containers.
            if len(candidate_container.find_all("p", recursive=False)) > 1:  # Check direct children first
                main_content_container = candidate_container
                break
            elif len(candidate_container.find_all("p")) > 2:  # Check all descendants
                main_content_container = candidate_container
                break

    # If no preferred container is found via specific selectors, fall back to a broader search
    if not main_content_container:
        potential_containers = article_soup.find_all(
            ["div", "article", "section"], # Common semantic tags for content
            class_=re.compile(r"article-body|content|body|main|post|story", re.IGNORECASE),
        )
        if potential_containers:
            # Heuristic: choose the container with the most paragraph tags
            main_content_container = max(potential_containers, key=lambda c: len(c.find_all("p")), default=None)

    collected_paragraphs_text = []
    if main_content_container:
        paragraphs = main_content_container.find_all("p")
        seen_texts = set() # To store text of paragraphs to ensure uniqueness
        for p in paragraphs:
            text = p.get_text(strip=True)
            # Filter out common non-content paragraphs (e.g., ads, share lines, very short text)
            if text and len(text) > 30 and not re.search(r"^(advertisement|sponsored|related articles|read more|also read|subscribe now|follow us|share this article|photo:|image:|caption:)", text, re.IGNORECASE):
                if text not in seen_texts:
                    collected_paragraphs_text.append(text)
                    seen_texts.add(text)
        
        if collected_paragraphs_text:
            article_content = "\n\n".join(collected_paragraphs_text).strip()

    # Extract category from the article page
    category = "No Category Found"
    try:
        category_element = article_soup.select_one("div.topic-holder a.dn-link.pill.tag")
        if category_element:
            category = category_element.text.strip()
    except Exception:
        print(f"Category not found for {link}")

    container_classes_list = main_content_container.get("class", []) if main_content_container and main_content_container.has_attr("class") else []
    return date_published, article_content, container_classes_list, category

# --- Verification Mechanism ---
def verify_scraped_dates(scraped_data, start_date, end_date):
    """
    After scraping, this function re-checks the collected data against the requested
    date range and reports any calendar days for which no articles were found.
    """
    print("\n--- Verification Step ---")
    if not scraped_data:
        print("⚠️ No data was scraped, so verification cannot be performed.")
        return

    # Create a set of all unique dates for which articles were successfully scraped
    scraped_dates = {item['Date'] for item in scraped_data if isinstance(item.get('Date'), date)}

    # Create a set of all calendar dates within the user-selected range
    expected_dates = {start_date + timedelta(days=d) for d in range((end_date - start_date).days + 1)}

    # Find which dates from the expected range are not in our scraped set
    missing_dates = sorted(list(expected_dates - scraped_dates))

    if not missing_dates:
        print("✅ Verification successful: At least one article was found for every calendar day in the selected range.")
    else:
        print(f"🟡 Verification warning: No articles were found for the following {len(missing_dates)} day(s) within your timeline:")
        for missing_date in missing_dates:
            print(f"  - {missing_date.strftime('%Y-%m-%d')}")
        print("This could be because no articles were published on these days, or they were potentially missed by the scraper.")

# --- Helper for System Clock Check ---
def get_real_current_year_from_api():
    """
    Fetches the current year from a reliable online source to perform a sanity check
    on the system clock. Returns None if the check fails (e.g., no internet).
    """
    if not requests:  # Check if the import of the 'requests' library succeeded
        print("ℹ️  Skipping online year verification because 'requests' library is not installed.")
        return None
    try:
        # worldtimeapi.org is a simple, free, and reliable service.
        print("Verifying system clock against online time source...")
        response = requests.get("http://worldtimeapi.org/api/ip", timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        # The datetime string is in ISO 8601 format, e.g., "2024-07-05T10:30:00.123456+01:00"
        iso_datetime_str = data.get('datetime')
        if iso_datetime_str and len(iso_datetime_str) >= 4:
            real_year = int(iso_datetime_str[:4])
            print(f"✅ Online time source reports the year is {real_year}.")
            return real_year
        return None
    except Exception as e:
        print(f"⚠️  Warning: Could not verify current year via online API. Error: {e}")
        return None

# --- Main Scraping Logic ---
def main():
    # --- System Clock Sanity Check ---
    # This check prevents issues if the computer's clock is set to the future.
    # It compares the system's year to a reliable online source.
    system_year = date.today().year
    real_current_year = get_real_current_year_from_api()

    if real_current_year and system_year > real_current_year:
        print("="*80)
        print("❌ CRITICAL ERROR: Your computer's system clock is set to the future.")
        print(f"    System Date Detected: {date.today().strftime('%Y-%m-%d')}")
        print(f"    Online Time Service Detected Year: {real_current_year}")
        print("    This will cause news articles to be filtered incorrectly and must be fixed.")
        print("    Please correct your system's date and time before running the script again.")
        print("="*80)
        return  # Stop execution to prevent incorrect data scraping.

    start_date, end_date = select_date_range()
    if not start_date or not end_date:
        print("Date selection cancelled or invalid. Exiting.")
        return
    print(f"\n📅 Scraping from {start_date} to {end_date}\n")

    scraped_data = []

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"user-data-dir={PROFILE_PATH}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(IMPLICIT_WAIT)

    page_number = 1
    stop_scraping = False

    while not stop_scraping:
        page_url = f"https://www.upstreamonline.com/latest?page={page_number}"
        print(f"\n🌐 Visiting: {page_url}")

        try:
            driver.get(page_url)
            WebDriverWait(driver, WAIT_TIMEOUT).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            articles = get_article_links_and_titles(soup)

            if not articles:
                print("⚠️ No more articles found on the site. Ending pagination.")
                break

            for link, title in articles:
                try:
                    print(f"Processing article: {title} ({link})")
                    parsed_date, article_content, container_classes, category = extract_article_details(driver, link)
                    print(f"Parsed date for {title}: {parsed_date} (type: {type(parsed_date)})")
 
                    if isinstance(parsed_date, date):
                        # Stop condition: if we find an article older than our start date, we assume
                        # all subsequent articles are also older and stop paginating.
                        if parsed_date < start_date:
                            print(f"🛑 Article '{title}' date ({parsed_date}) is older than start date ({start_date}). Stopping all scraping.")
                            stop_scraping = True
                            break # Exit the loop for this page
 
                        # Process article if it's within the desired date range
                        if start_date <= parsed_date <= end_date:
                            scraped_data.append({
                                "Topic": title,
                                "Link": link,
                                "Date": parsed_date,
                                "Content": article_content,
                                "Content Classes": container_classes,
                                "URL Content Class": category
                            })
                            print(f"✅ Added '{title}' to the dataset.")
                        else:
                            # This case handles articles that are newer than the end_date
                            print(f"ℹ️ Article '{title}' date ({parsed_date}) is newer than end date ({end_date}). Skipping.")
                    else:
                        print(f"ℹ️ Could not parse date for '{title}'. Skipping.")
 
                except Exception as e:
                    print(f"❌ Error processing article: {link} - {e}")

            page_number += 1
            time.sleep(1)

        except Exception as e:
            print(f"❌ Page error: {e}")
            break

    driver.quit()

    # Call the verification function to check for missing dates before saving
    verify_scraped_dates(scraped_data, start_date, end_date)

    today = date.today()
    filename = f"news_filtered_by_date_{today.strftime('%Y-%m-%d')}.xlsx"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_path = os.path.join(OUTPUT_DIR, filename)

    if scraped_data:
        df = pd.DataFrame(scraped_data)
        df["Serial Number"] = range(1, len(df) + 1)
        # Reorder columns to match original intent
        df = df[["Topic", "Link", "Date", "Content", "Content Classes", "Serial Number", "URL Content Class"]]
        df.to_excel(file_path, index=False)
        print(f"\n✅ Data saved to: {file_path}")
    else:
        print("\n⚠️ No data collected.")

# --- Entry Point ---
if __name__ == '__main__':
    main()

import spacy
import pandas as pd
import re
import numpy as np
from collections import Counter
from string import punctuation
import heapq
from sklearn.metrics.pairwise import cosine_similarity
from spacy.matcher import Matcher
import tkinter as tk
from tkinter import filedialog
from tqdm import tqdm
import spacy.cli  # Ensure spacy.cli is imported for model download

# --- Configuration ---
SPACY_MODEL = 'en_core_web_trf'
nlp = None # Initialize nlp
try:
    retry_attempts = 3
    for attempt in range(retry_attempts):
        try:
            nlp = spacy.load(SPACY_MODEL)
            print(f"Successfully loaded SpaCy model: {SPACY_MODEL}")
            break
        except OSError as e: 
            if attempt < retry_attempts - 1:
                print(f"Attempt {attempt + 1} failed to load SpaCy model '{SPACY_MODEL}'. Retrying...")
                spacy.cli.download(SPACY_MODEL)
            else:
                print(f"Failed to load SpaCy model '{SPACY_MODEL}' after {retry_attempts} attempts. Error: {e}")
                raise
except OSError: # Fallback if retries fail
    print(f"Downloading SpaCy model '{SPACY_MODEL}'...")
    spacy.cli.download(SPACY_MODEL)
    nlp = spacy.load(SPACY_MODEL)
    print(f"Successfully downloaded and loaded SpaCy model: {SPACY_MODEL}")


# Define file paths
# FILE_PATH = r"C:\Office work\Upstream SCRAP news\news_filtered_by_date_2025-06-13.xlsx" # Will be selected via dialog
OUTPUT_PATH = r"C:\Office work\Upstream SCRAP news\Filter output.xlsx" # Output path can remain or also be made dynamic

# --- Global Lists for Scope Mapping ---
BUILD_PROCESS_OPTIONS = [
    "Concept Engineering", "Concept",
    "Pre-FEED", "Pre Front End Engineering Design",
    "FEED", "Front End Engineering Design",
    "Detailed Engineering", "Detailed Design",
    "Engineering & Construction", "EPC",
    "Procurement & Construction", "P+C",
    "E+C",
    "Site Preparation", "Trenching",
    "Project Management",
    "Transport", "Transportation",
    "Installation",
    "Hook up and commissioning", "Commissioning", "Hook-up",
    "Lease",
    "Operation & Maintenance", "O&M",
    "Asset Integrity",
    "IRM", "Inspection, Repair & Maintenance",
    "Duty Holder",
    "Decommissioning",
    "Decommissioning (Onshore Disposal)", "Onshore Disposal",
    "Decommissioning (Offshore Removal)", "Offshore Removal",
    "Decommissioning (Engineering)", "Decommissioning Engineering",
    "General Information", "General Contract"
]

BUILD_PARTS = {
    "Tree", "Christmas Tree", "Wellhead", "Manifold", "Subsea Manifold", "Subsea Unit",
    "Control Module", "Subsea Control Module", "Subsea Arch", "Boosting", "Subsea Boosting",
    "Compression", "Subsea Compression", "Injection", "Subsea Injection", "Separation",
    "Subsea Separation", "Controls", "Subsea Controls", "Pipelines", "Subsea Pipelines",
    "Flowlines", "Subsea Flowlines", "Templates", "Subsea Templates", "Subsea", "Subsea Systems",
    "SURF", "Subsea Umbilicals, Risers and Flowlines", "SURF Package",
    "Umbilical", "Umbilical Lines", "Riser", "Flowline", "Flexibles", "Flexible Risers",
    "Flexible Flowlines", "SURF", "SURF Package",
    "Topside", "Topsides", "Topsides Deck", "Topsides Units", "Accommodation",
    "Topsides Accommodation", "Compression", "Topsides Compression", "Drilling",
    "Topsides Drilling", "Power", "Topsides Power", "Process", "Topsides Process",
    "Carbon Capture", "Topsides Carbon Capture", "Rig", "Drilling Rig", "Living Quarters",
    "Helideck",
    "FPSO", "FSRU", "FLNG", "MOPU", "FSO", "Floater", "TLP", "Spar",
    "Jacket", "Hull", "Caisson", "Compliant Tower", "GBS", "Gravity Base Structure",
    "Mooring", "Mooring System", "Subsea Mooring Connectors", "Connectors",
    "Piles", "Anchors", "Anchor",
    "Turret", "SPM", "Single Point Mooring", "Integration",
    "Project", "Subsea", "SURF Contract", "Topsides Contract", "WHd Contract"
}

ALL_BUILD_KEYWORDS = sorted(list(set(BUILD_PROCESS_OPTIONS + list(BUILD_PARTS))))

# --- Keywords for Build Part Length Extraction ---
# Keywords for build parts where length is relevant
TARGET_BUILD_PARTS = [
    "pipeline", "pipelines", "subsea pipeline", "subsea pipelines",
    "umbilical", "umbilicals", "umbilical line", "umbilical lines",
    "flowline", "flowlines", "subsea flowline", "subsea flowlines",
    "riser", "risers",
    "cable", "cables", "communication cable", "power cable", "export cable"
]
# Keywords for units of length
LENGTH_UNITS = ["km", "kilometer", "kilometers", "m", "meter", "meters", "mile", "miles", "foot", "feet", "ft"]
LENGTH_UNITS_SHORT_EXACT = ["km", "m", "ft"] # For regex like \d+km

# Pre-sort target_build_parts for efficient matching of the most specific part first
SORTED_TARGET_BUILD_PARTS = sorted(TARGET_BUILD_PARTS, key=len, reverse=True)

# Compile regex patterns for efficiency (moved outside the function)
# Pattern for "10 km", "10 kilometers" (allows space between number and unit)
NUM_UNIT_REGEX_SPACED = re.compile(r"(\d+(?:\.\d+)?)\s*(" + "|".join(LENGTH_UNITS) + r")\b", re.IGNORECASE)
# Pattern for "10km" (no space, short units only, case-insensitive unit)
NUM_UNIT_REGEX_NOSPACE = re.compile(r"(\d+(?:\.\d+)?)(" + "|".join(LENGTH_UNITS_SHORT_EXACT) + r")\b", re.IGNORECASE)
# Pattern for "10-kilometer"
NUM_DASH_UNIT_REGEX = re.compile(r"(\d+(?:\.\d+)?)\s*-\s*(" + "|".join(unit for unit in LENGTH_UNITS if unit not in LENGTH_UNITS_SHORT_EXACT) + r")\b", re.IGNORECASE)

# --- Keywords for Build Part Weight Extraction ---
WEIGHT_TARGET_PARTS = [
    "topside", "topsides", "jacket", "hull", "module", "modules", "manifold", "tree",
    "christmas tree", "wellhead", "template", "pile", "piles", "anchor", "anchors",
    "turret", "gbs", "gravity base structure", "platform",
    # Added floater types for weight extraction, addressing user feedback
    "fpso", "fsru", "flng", "mopu", "fso", "floater", "tlp", "spar"
]
WEIGHT_UNITS = ['t', 'ton', 'tons', 'tonne', 'tonnes', 'te', 'kg', 'kilogram', 'kilograms', 'lb', 'lbs', 'pound', 'pounds']
WEIGHT_UNITS_SHORT_EXACT = ['t', 'kg', 'lb', 'lbs']

SORTED_WEIGHT_TARGET_PARTS = sorted(WEIGHT_TARGET_PARTS, key=len, reverse=True)

# Compile regex for weight, allowing for commas in numbers (e.g., 5,000)
# Pattern for "5,000 tonnes"
NUM_WEIGHT_UNIT_REGEX_SPACED = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(WEIGHT_UNITS) + r")\b", re.IGNORECASE)
# Pattern for "5000t"
NUM_WEIGHT_UNIT_REGEX_NOSPACE = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(WEIGHT_UNITS_SHORT_EXACT) + r")\b", re.IGNORECASE)

# --- Keywords for Build Part Diameter Extraction ---
DIAMETER_TARGET_PARTS = [
    "pipeline", "pipelines", "subsea pipeline", "subsea pipelines",
    "umbilical", "umbilicals", "umbilical line", "umbilical lines",
    "flowline", "flowlines", "subsea flowline", "subsea flowlines",
    "riser", "risers", "pile", "piles", "caisson"
]

# Added 'meter' and 'meters' for large diameter items like caissons or tunnels, per user feedback
DIAMETER_UNITS = ['inch', 'inches', 'in', '"', 'mm', 'millimeter', 'millimeters', 'cm', 'centimeter', 'centimeters', 'm', 'meter', 'meters', 'foot', 'feet', 'ft']
DIAMETER_UNITS_SHORT_EXACT = ['in', '"', 'mm', 'cm', 'm', 'ft']

SORTED_DIAMETER_TARGET_PARTS = sorted(DIAMETER_TARGET_PARTS, key=len, reverse=True)

# Compile regex for diameter
NUM_DIAMETER_UNIT_REGEX_SPACED = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(DIAMETER_UNITS) + r")\b", re.IGNORECASE)
NUM_DIAMETER_UNIT_REGEX_NOSPACE = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(DIAMETER_UNITS_SHORT_EXACT) + r")\b", re.IGNORECASE)
NUM_DASH_DIAMETER_UNIT_REGEX = re.compile(r"([\d,]+(?:\.\d+)?)\s*-\s*(" + "|".join(unit for unit in DIAMETER_UNITS if unit not in DIAMETER_UNITS_SHORT_EXACT) + r")\b", re.IGNORECASE)

# --- Keywords for Dimensions (LxWxH) ---
DIMENSION_TARGET_PARTS = [
    "topside", "topsides", "hull", "module", "modules", "platform", "fpso", "jacket", "vessel"
]
DIMENSION_UNITS = ['m', 'meter', 'meters', 'foot', 'feet', 'ft']
SORTED_DIMENSION_TARGET_PARTS = sorted(DIMENSION_TARGET_PARTS, key=len, reverse=True)

# --- Keywords for Accommodation Capacity ---
ACCOMMODATION_TARGET_PARTS = [
    "fpso", "platform", "living quarters", "accommodation module", "flotel", "vessel"
]
ACCOMMODATION_UNITS = ['person', 'people', 'personnel', 'pob', 'berths', 'beds']
SORTED_ACCOMMODATION_TARGET_PARTS = sorted(ACCOMMODATION_TARGET_PARTS, key=len, reverse=True)

# --- Keywords for Storage Capacity ---
STORAGE_TARGET_PARTS = [
    "fpso", "fso", "flng", "hull", "tank", "tanks", "vessel"
]
STORAGE_UNITS = ['barrels', 'bbl', 'bbls', 'cubic meters', 'm3', 'tonnes', 't']
SORTED_STORAGE_TARGET_PARTS = sorted(STORAGE_TARGET_PARTS, key=len, reverse=True)

# --- Keywords for Power Generation ---
POWER_TARGET_PARTS = [
    "power module", "generator", "platform", "fpso", "facility"
]
POWER_UNITS = ['megawatt', 'mw', 'kilowatt', 'kw', 'gigawatt', 'gw']
SORTED_POWER_TARGET_PARTS = sorted(POWER_TARGET_PARTS, key=len, reverse=True)

# --- Keywords for Mooring Systems ---
MOORING_TARGET_PARTS = [
    "fpso", "flng", "fsru", "fso", "spar", "tlp", "vessel", "buoy", "platform", "floater"
]
MOORING_TYPES = [
    "turret", "spread", "catenary", "taut-leg", "single-point", "disconnectable", "internal", "external"
]
SORTED_MOORING_TARGET_PARTS = sorted(MOORING_TARGET_PARTS, key=len, reverse=True)

# --- Keywords for Vessel Details Extraction (New) ---
VESSEL_TYPES = [
    "vessel", "ship", "drillship", "semi-submersible", "rig", "jack-up", "platform supply vessel", "psv",
    "anchor handling tug supply", "ahts", "aht", "construction vessel", "subsea construction vessel", "scv",
    "pipelay vessel", "heavy-lift vessel", "flotel", "accommodation vessel", "support vessel", "tug",
    "barge", "tanker", "carrier", "seismic vessel"
]
SORTED_VESSEL_TYPES = sorted(VESSEL_TYPES, key=len, reverse=True)

VESSEL_SCOPE_KEYWORDS = [
    "support", "drilling", "installation", "construction", "pipelay", "decommissioning", "accommodation",
    "transport", "maintenance", "survey", "seismic", "towing", "anchor handling", "rov", "inspection",
    "repair", "irm"
]

VESSEL_CHARTER_VERBS = [
    "charter", "contract", "hire", "award", "secure", "fix", "book", "mobilise", "deploy", "take on"
]

# --- Keywords for Depth Rating Extraction ---
DEPTH_RATING_TARGET_PARTS = [
    "wellhead", "wellheads", "christmas tree", "trees", "manifold", "manifolds",
    "bop", "blowout preventer", "valve", "valves", "riser", "risers", "pipeline", "pipelines",
    "pump", "pumps", "compressor", "compressors", "umbilical", "umbilicals", "flowline", "flowlines",
    "connector", "connectors", "sps", "subsea production system", "subsea system", "subsea equipment"
]
DEPTH_RATING_UNITS = ['meter', 'meters', 'm', 'feet', 'ft']
SORTED_DEPTH_RATING_TARGET_PARTS = sorted(DEPTH_RATING_TARGET_PARTS, key=len, reverse=True)
NUM_DEPTH_RATING_UNIT_REGEX = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(DEPTH_RATING_UNITS) + r")\b", re.IGNORECASE)




# --- Keywords for Pressure Rating Extraction ---
PRESSURE_TARGET_PARTS = [
    "wellhead", "wellheads", "christmas tree", "trees", "manifold", "manifolds",
    "bop", "blowout preventer", "valve", "valves", "riser", "risers", "pipeline", "pipelines", "choke"
]
PRESSURE_UNITS = ['psi', 'bar', 'pascal', 'pa', 'kpa', 'mpa']
SORTED_PRESSURE_TARGET_PARTS = sorted(PRESSURE_TARGET_PARTS, key=len, reverse=True)
NUM_PRESSURE_UNIT_REGEX = re.compile(r"([\d,]+(?:k|K)?)\s*(" + "|".join(PRESSURE_UNITS) + r")\b", re.IGNORECASE)

# --- Keywords for Flow Capacity Extraction ---
FLOW_CAPACITY_TARGET_PARTS = [
    "pipeline", "pipelines", "flowline", "flowlines", "pump", "pumps", "compressor", "compressors",
    "riser", "risers", "processing plant", "facility", "terminal", "separator", "separators"
]
FLOW_CAPACITY_UNITS = [
    'bpd', 'bbl/d', 'boepd', 'm3/d', 'scfd', 'mcfd', 'mmscfd', 'bcfd', 'tph', 'kg/s', 'gj/d', 'tcf/d', 'mcm/d',
    'barrels per day', 'cubic meters per day', 'tonnes per hour'
]
SORTED_FLOW_CAPACITY_TARGET_PARTS = sorted(FLOW_CAPACITY_TARGET_PARTS, key=len, reverse=True)
NUM_FLOW_CAPACITY_UNIT_REGEX = re.compile(r"([\d,]+(?:\.\d+)?)\s*(" + "|".join(FLOW_CAPACITY_UNITS) + r")\b", re.IGNORECASE)

# --- Keywords for Temperature Rating Extraction ---
TEMP_TARGET_PARTS = [
    "pipeline", "pipelines", "vessel", "vessels", "reactor", "reactors", "storage tank", "tanks",
    "heater", "heaters", "cooler", "coolers", "exchanger", "exchangers"
]
TEMP_UNITS = ['celsius', 'fahrenheit', 'kelvin', 'c', 'f', 'k', 'degrees', '°c', '°f']
SORTED_TEMP_TARGET_PARTS = sorted(TEMP_TARGET_PARTS, key=len, reverse=True)
NUM_TEMP_UNIT_REGEX = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:degrees)?\s*(" + "|".join(TEMP_UNITS) + r")\b", re.IGNORECASE)


# --- Keywords for Quantity Extraction ---
QUANTITY_TARGET_PARTS = list(BUILD_PARTS)
# Remove abstract/non-countable items to improve accuracy
NON_COUNTABLE_KEYWORDS = [
    "integration", "project", "subsea", "surf contract", "topsides contract", "whd contract",
    "boosting", "compression", "injection", "separation", "controls", "engineering", "management",
    "transport", "installation", "maintenance", "decommissioning", "procurement"
]
SORTED_QUANTITY_TARGET_PARTS = sorted([p for p in QUANTITY_TARGET_PARTS if p.lower() not in NON_COUNTABLE_KEYWORDS], key=len, reverse=True)

# --- Entity Keywords for Capacity ---
ENTITY_KEYWORDS_FOR_CAPACITY = {
    "Well": ["well", "wells", "wellbore"],
    "Field": ["field", "oilfield", "gas field", "fields", "development", "reservoir"],
    "Cluster": ["cluster", "hub", "tie-back"],
    "Block": ["block", "blocks", "licence block", "license"],
    "Basin": ["basin", "basins"],
    "Floater": ["fpso", "flng", "fsru", "mopu", "fso", "floater", "floating production storage and offloading", "vessel"],
    "Plant": ["plant", "facility", "terminal", "refinery", "processing plant", "gas plant", "petrochemical plant", "onshore facility", "station"],
    "Platform": ["platform", "topsides", "jacket", "rig", "drilling rig", "spar", "tlp", "semisubmersible", "fixed platform"],
    "Pipeline": ["pipeline", "pipelines", "flowline", "flowlines", "umbilical", "riser", "export line"],
    "Subsea": ["subsea production system", "sps", "manifold", "subsea pump", "template", "subsea facility"],
    "Project": ["project", "package", "phase", "development project", "expansion"]
}


# --- Helper functions ---

def clean_text(text):
    """Converts input to string and handles NaN values."""
    if pd.isna(text):
        return ""
    return str(text).strip()

def extract_project_profiles(text):
    """
    Identifies project/field names and builds a detailed profile for each,
    extracting capacity, timeline, water depth, and distance from the surrounding text.
    """
    text = clean_text(text)
    if not text: return ''
    doc = nlp(text)
    
    # --- Step 1: Enhanced Field/Project Name Identification ---
    found_names = set()
    
    # Regex for simple patterns like "Project Name Field", "Block-XYZ"
    regex_patterns = re.findall(
        r'\b(?:[A-Z][a-z0-9\'-]*\s*){1,5}(?:Field|Project|Development|Oilfield|Area|Licence|Basin|Discovery)\b|'
        r'\bBlock\s+(?:[A-Z0-9-]+)\b|' 
        r'\b(?:Phase \d+|Package \d+|EPCI \d+)\b', 
        text, re.IGNORECASE
    )
    for match in regex_patterns:
        found_names.add(match.strip())

    # Matcher for grammatical patterns
    matcher = Matcher(nlp.vocab)
    pattern_name_designator = [
        {"POS": {"IN": ["PROPN", "NOUN", "ADJ"]}, "OP": "+"}, 
        {"LOWER": {"IN": ["field", "project", "development", "oilfield", "block", "area", "licence", "basin", "phase", "package", "discovery"]}}
    ]
    matcher.add("FIELD_PROJECT_NAME", [pattern_name_designator])
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        # Avoid matching generic phrases like "the project"
        if not (span.text.lower().startswith("the ") and len(span.text.split()) <= 2):
            found_names.add(span.text.strip())

    # NER-based identification
    for ent in doc.ents:
        if ent.label_ in ['PRODUCT', 'FAC', 'WORK_OF_ART']: # WORK_OF_ART can sometimes catch project names
            if any(term in ent.text.lower() for term in ['project', 'field', 'development', 'phase', 'package']):
                found_names.add(ent.text.strip())
            # Add proper nouns that are likely project names
            elif len(ent.text.split()) > 1 and all(t.istitle() or t.isupper() for t in ent.text.split()):
                 found_names.add(ent.text.strip())
        elif ent.label_ in ['GPE', 'LOC']:
             # Check if a designator follows the location name
            for token in doc[ent.end:min(len(doc), ent.end+2)]:
                if token.lower_ in ['field', 'basin', 'block', 'area', 'discovery']:
                    found_names.add(f"{ent.text.strip()} {token.text.strip()}")
                    break

    # Post-processing to remove junk and substrings
    for name in found_names:
        # Filter out very short, non-numeric names and generic terms
        if len(name) < 4 and not re.search(r'\d', name) and name.lower() not in ['block', 'field', 'project', 'phase']:
            continue

    candidate_names = set()
    names_list = sorted(list(found_names), key=len, reverse=True)
    for i, name1 in enumerate(names_list):
        is_substring = False
        for j, name2 in enumerate(names_list):
            if i != j and name1.lower() in name2.lower():
                is_substring = True
                break
        if not is_substring:
            candidate_names.add(name1)
    
    if not candidate_names:
        return ''

    # --- Step 2: Build Profiles for Each Identified Name ---
    profiles = {name: {} for name in candidate_names}
    
    for sent in doc.sents:
        sent_text_lower = sent.text.lower()
        
        for name in candidate_names:
            # Check if the name (or a significant part of it) is in the sentence
            # This handles cases like "the Johan Sverdrup development" when name is "Johan Sverdrup"
            if any(part.lower() in sent_text_lower for part in name.split() if len(part) > 3):
                
                # Extract Water Depth
                depth_match = re.search(r"in ([\d,]+(?:\.\d+)?)\s*(meters?|m|feet|ft)\s+of water", sent_text_lower)
                if depth_match and 'Depth' not in profiles[name]:
                    unit = 'm' if 'm' in depth_match.group(2) else 'ft'
                    profiles[name]['Depth'] = f"{depth_match.group(1).replace(',', '')}{unit}"
                
                # Extract Distance
                dist_match = re.search(r"([\d,]+(?:\.\d+)?)\s*(km|kilometers?|miles?)\s*(offshore|from the coast)", sent_text_lower)
                if dist_match and 'Distance' not in profiles[name]:
                    unit = 'km' if 'k' in dist_match.group(2) else 'miles'
                    profiles[name]['Distance'] = f"{dist_match.group(1).replace(',', '')}{unit} offshore"
                    
                # Extract Timeline/Status
                if 'Timeline' not in profiles[name]:
                    timeline_keywords = {
                        "Startup": ["first oil", "first gas", "start-up", "online", "operational by", "come onstream", "begin production"],
                        "Shutdown": ["shut down", "cease production", "decommissioning in", "abandonment in", "plug and abandon"]
                    }
                    timeline_found = None
                    for status, keywords in timeline_keywords.items():
                        for kw in keywords:
                            if kw in sent_text_lower:
                                for ent in sent.ents:
                                    if ent.label_ == 'DATE':
                                        timeline_found = f"{status} {ent.text}"
                                        break
                                if timeline_found: break
                        if timeline_found: break
                    if timeline_found:
                        profiles[name]['Timeline'] = timeline_found

                # Extract Capacity
                if 'Capacity' not in profiles[name]:
                    if not re.search(r'[\$€£]', sent.text): # Avoid matching money
                        CAPACITY_REGEX = r"([\d,.]+(?:\.\d+)?\s*(?:million|billion|thousand|mn|bn|k)?\s*(?:bpd|boe/d|boepd|mmscfd|scfd|tpd|mcfd|bbl/d|bcfd|mboed|tcf/d|mcm/d|tonnes/year|t/y|t/d|barrels|tonnes|cubic\s+feet|cubic\s+meters))"
                        cap_match = re.search(CAPACITY_REGEX, sent.text, re.IGNORECASE)
                        if cap_match:
                            profiles[name]['Capacity'] = ' '.join(cap_match.group(1).split())

    # --- Step 3: Format the Output String ---
    output_parts = []
    for name in sorted(list(candidate_names)):
        details = profiles[name]
        if not details:
            output_parts.append(name)
        else:
            ordered_details = []
            if 'Capacity' in details: ordered_details.append(f"Capacity: {details['Capacity']}")
            if 'Timeline' in details: ordered_details.append(f"Timeline: {details['Timeline']}")
            if 'Depth' in details: ordered_details.append(f"Depth: {details['Depth']}")
            if 'Distance' in details: ordered_details.append(f"Distance: {details['Distance']}")
            detail_str = ", ".join(ordered_details)
            output_parts.append(f"{name} ({detail_str})")
            
    return "; ".join(output_parts)


def extract_vessel_details(text):
    """
    Identifies vessels mentioned in the text and extracts key details like
    type, owner, charterer, day rate, work scope, and contract duration.
    """
    text = clean_text(text)
    if not text:
        return ''
    doc = nlp(text)
    vessel_profiles = {}

    # --- Step 1: Identify potential vessel names ---
    potential_vessel_spans = []
    for ent in doc.ents:
        if ent.label_ in ["PRODUCT", "FAC", "ORG"]:
            ent_text_lower = ent.text.lower()
            if any(char.isdigit() for char in ent.text) or '-' in ent.text or any(v_type in ent_text_lower for v_type in VESSEL_TYPES):
                potential_vessel_spans.append(ent)

    matcher = Matcher(nlp.vocab)
    pattern = [{"LOWER": {"IN": ["vessel", "ship", "rig", "drillship", "flotel"]}}, {"POS": "PROPN", "OP": "+"}]
    matcher.add("VESSEL_NAMED", [pattern])
    matches = matcher(doc)
    for _, start, end in matches:
        potential_vessel_spans.append(doc[start:end])

    # --- Step 2: Build profile for each potential vessel ---
    for vessel_span in potential_vessel_spans:
        vessel_name = vessel_span.text
        for v_type in SORTED_VESSEL_TYPES:
            if vessel_name.lower().endswith(f" {v_type}"):
                vessel_name = vessel_name[:-(len(v_type)+1)].strip()
                break
        
        if vessel_name.lower() in VESSEL_TYPES or len(vessel_name) < 4:
            continue

        sent = vessel_span.sent
        sent_text_lower = sent.text.lower()

        if vessel_name not in vessel_profiles:
            vessel_profiles[vessel_name] = {}
        profile = vessel_profiles[vessel_name]

        # Extract Type
        if 'Type' not in profile:
            for v_type in SORTED_VESSEL_TYPES:
                if v_type in sent_text_lower:
                    profile['Type'] = v_type.title()
                    break

        # Extract Owner and Charterer
        for ent in sent.ents:
            if ent.label_ == 'ORG':
                if f"{ent.text}'s".lower() in sent_text_lower and 'Owner' not in profile:
                    profile['Owner'] = ent.text
                if any(verb in sent_text_lower for verb in VESSEL_CHARTER_VERBS) and 'Charterer' not in profile:
                    if 'Owner' not in profile or profile['Owner'] != ent.text:
                        profile['Charterer'] = ent.text

        # Extract Day Rate
        day_rate_match = re.search(r"((?:[\$€£]|usd)\s?[\d,]+(?:\.\d+)?(?:k| thousand)?)\s*(?:per day|a day|dayrate)", sent_text_lower)
        if day_rate_match and 'Day Rate' not in profile:
            profile['Day Rate'] = day_rate_match.group(1).replace(" thousand", "k")

        # Extract Duration
        duration_match = re.search(r"(?:for|of)\s+((?:a firm period of\s+)?(?:up to\s+)?(?:\d+|[\w\s]+)\s(?:year|month|week|day)s?)", sent_text_lower)
        if duration_match and 'Duration' not in profile:
            profile['Duration'] = duration_match.group(1).strip()

        # Extract Work Scope
        scope_match = re.search(r"(?:to|for|perform|carry out)\s+((?:[\w\s-]+\s)?(?:{})(?:[\w\s-]+)?)".format("|".join(VESSEL_SCOPE_KEYWORDS)), sent_text_lower)
        if scope_match and 'Scope' not in profile:
            scope_text = re.sub(r'\s+', ' ', scope_match.group(1)).strip(" .,").strip()
            profile['Scope'] = scope_text

    # --- Step 3: Format Output ---
    output_parts = []
    for vessel_name, profile in sorted(vessel_profiles.items()):
        if not profile:
            continue # Don't add vessels for which we found no details

        details = []
        if 'Type' in profile: details.append(f"Type: {profile['Type']}")
        if 'Owner' in profile: details.append(f"Owner: {profile['Owner']}")
        if 'Charterer' in profile: details.append(f"Charterer: {profile['Charterer']}")
        if 'Day Rate' in profile: details.append(f"Day Rate: {profile['Day Rate']}")
        if 'Duration' in profile: details.append(f"Duration: {profile['Duration']}")
        if 'Scope' in profile: details.append(f"Scope: {profile['Scope']}")

        detail_str = ", ".join(details)
        if detail_str:
            output_parts.append(f"{vessel_name} ({detail_str})")
        else:
            output_parts.append(vessel_name)

    return "; ".join(output_parts)


def extract_build_part_specifications(text):
    """
    Extracts specifications for build parts, including length and weight.
    Detects build part names and associated parameters (e.g., "10 km pipeline", "5,000-tonne jacket").
    """
    text = clean_text(text)
    if not text:
        return ''
    doc = nlp(text)
    matcher = Matcher(nlp.vocab)
    parsed_specs_set = set()

    # --- LENGTH PATTERNS ---
    # Pattern 1: NUMBER UNIT BUILD_PART (e.g., "10 km pipeline")
    length_pattern1 = [
        {"LIKE_NUM": True},
        {"LOWER": {"IN": LENGTH_UNITS}},
        {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"}
    ]
    # Pattern 1a: NUMBERUNIT BUILD_PART (e.g. "10km pipeline")
    length_pattern1a = [
        {"TEXT": {"REGEX": r"(?i)^\d+(\.\d+)?(" + "|".join(LENGTH_UNITS_SHORT_EXACT) + r")$"}},
        {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"}
    ]
    # Pattern 2: BUILD_PART of NUMBER UNIT (e.g., "pipeline of 10 km")
    length_pattern2 = [
        {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"},
        {"LOWER": "of"},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": LENGTH_UNITS}}
    ]
    # Pattern 2a: BUILD_PART of NUMBERUNIT (e.g. "pipeline of 10km")
    length_pattern2a = [
        {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"},
        {"LOWER": "of"},
        {"TEXT": {"REGEX": r"(?i)^\d+(\.\d+)?(" + "|".join(LENGTH_UNITS_SHORT_EXACT) + r")$"}}
    ]
    # Pattern 3: BUILD_PART measuring/stretching/long NUMBER UNIT
    length_pattern3 = [
        {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"},
        {"LOWER": {"IN": ["measuring", "stretching", "spanning", "long"]}},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": LENGTH_UNITS}}
    ]
    # Pattern 4: NUMBER-UNIT BUILD_PART (e.g. "10-kilometer pipeline")
    length_pattern4 = [
        {"LIKE_NUM": True},
        {"IS_PUNCT": True, "LOWER": "-"},
        {"LOWER": {"IN": [unit for unit in LENGTH_UNITS if unit not in LENGTH_UNITS_SHORT_EXACT]}},
        {"LOWER": {"IN": TARGET_BUILD_PARTS}, "OP": "+"}
    ]
    matcher.add("LENGTH_SPEC", [length_pattern1, length_pattern1a, length_pattern2, length_pattern2a, length_pattern3, length_pattern4])

    # --- WEIGHT PATTERNS ---
    # Pattern 1: NUMBER UNIT BUILD_PART (e.g., "5000 tonne jacket")
    weight_pattern1 = [{"LIKE_NUM": True}, {"LOWER": {"IN": WEIGHT_UNITS}}, {"LOWER": {"IN": WEIGHT_TARGET_PARTS}, "OP": "+"}]
    # Pattern 2: BUILD_PART of NUMBER UNIT (e.g., "jacket of 5000 tonnes")
    weight_pattern2 = [{"LOWER": {"IN": WEIGHT_TARGET_PARTS}, "OP": "+"}, {"LOWER": "of"}, {"LIKE_NUM": True}, {"LOWER": {"IN": WEIGHT_UNITS}}]
    # Pattern 3: BUILD_PART weighing NUMBER UNIT
    weight_pattern3 = [{"LOWER": {"IN": WEIGHT_TARGET_PARTS}, "OP": "+"}, {"LOWER": "weighing"}, {"LIKE_NUM": True}, {"LOWER": {"IN": WEIGHT_UNITS}}]
    # Pattern 4: BUILD_PART with a weight of NUMBER UNIT
    weight_pattern4 = [{"LOWER": {"IN": WEIGHT_TARGET_PARTS}, "OP": "+"}, {"LOWER": "with"}, {"LOWER": "a", "OP": "?"}, {"LOWER": "weight"}, {"LOWER": "of"}, {"LIKE_NUM": True}, {"LOWER": {"IN": WEIGHT_UNITS}}]
    matcher.add("WEIGHT_SPEC", [weight_pattern1, weight_pattern2, weight_pattern3, weight_pattern4])

    # --- DIAMETER PATTERNS ---
    # Pattern 1: 12-inch diameter pipeline
    diameter_pattern1 = [
        {"LIKE_NUM": True},
        {"IS_PUNCT": True, "LOWER": "-", "OP": "?"},
        {"LOWER": {"IN": DIAMETER_UNITS}},
        {"LOWER": "diameter", "OP": "?"},
        {"LOWER": {"IN": DIAMETER_TARGET_PARTS}, "OP": "+"}
    ]
    # Pattern 2: pipeline with a diameter of 12 inches
    diameter_pattern2 = [
        {"LOWER": {"IN": DIAMETER_TARGET_PARTS}, "OP": "+"},
        {"LOWER": "with"}, {"LOWER": {"IN": ["a", "an"]}, "OP": "?"},
        {"LOWER": "diameter"}, {"LOWER": "of"},
        {"LIKE_NUM": True}, {"LOWER": {"IN": DIAMETER_UNITS}}
    ]
    # Pattern 3: pipeline of 12 inches in diameter
    diameter_pattern3 = [
        {"LOWER": {"IN": DIAMETER_TARGET_PARTS}, "OP": "+"},
        {"LOWER": "of"}, {"LIKE_NUM": True},
        {"LOWER": {"IN": DIAMETER_UNITS}},
        {"LOWER": "in"}, {"LOWER": "diameter"}
    ]
    matcher.add("DIAMETER_SPEC", [diameter_pattern1, diameter_pattern2, diameter_pattern3])
    # Pattern 4 for Diameter: [NUM] to [NUM] [UNIT] [PART]
    diameter_pattern4 = [
        {"LIKE_NUM": True},
        {"LOWER": {"IN": ["to", "-"]}},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": DIAMETER_UNITS}},
        {"LOWER": "diameter", "OP": "?"},
        {"LOWER": {"IN": DIAMETER_TARGET_PARTS}, "OP": "+"}
    ]
    matcher.add("DIAMETER_SPEC", [diameter_pattern1, diameter_pattern2, diameter_pattern3, diameter_pattern4])
    # --- DEPTH RATING PATTERNS ---
    # Pattern 1: [PART] rated for [NUMBER] [UNIT] depth (e.g., "wellhead rated for 3000 meters depth")
    depth_pattern1 = [
        {"LOWER": {"IN": DEPTH_RATING_TARGET_PARTS}, "OP": "+"},
        {"LOWER": {"IN": ["rated", "designed"]}},
        {"LOWER": "for"},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": DEPTH_RATING_UNITS}},
        {"LOWER": {"IN": ["depth", "water", "water depth"]}, "OP": "?"}
    ]
    # Pattern 2: [NUMBER] [UNIT] water depth [PART] (e.g., "3000 meters water depth manifold")
    depth_pattern2 = [
        {"LIKE_NUM": True},
        {"LOWER": {"IN": DEPTH_RATING_UNITS}},
        {"LOWER": {"IN": ["depth", "water", "water depth"]}},
        {"LOWER": {"IN": DEPTH_RATING_TARGET_PARTS}, "OP": "+"}
    ]
    # Pattern 3: [PART] for [NUMBER] [UNIT] water (e.g., "subsea tree for 2500m water")
    depth_pattern3 = [
        {"LOWER": {"IN": DEPTH_RATING_TARGET_PARTS}, "OP": "+"},
        {"LOWER": "for"}, {"LIKE_NUM": True}, {"LOWER": {"IN": DEPTH_RATING_UNITS}}, {"LOWER": "water", "OP": "?"}
    ]
    matcher.add("DEPTH_RATING_SPEC", [depth_pattern1, depth_pattern2, depth_pattern3])

    # --- PRESSURE PATTERNS ---
    # Pattern 1: 15,000 psi wellhead
    pressure_pattern1 = [
        {"TEXT": {"REGEX": r"[\d,]+(?:k|K)?"}},
        {"LOWER": {"IN": PRESSURE_UNITS}},
        {"LOWER": {"IN": PRESSURE_TARGET_PARTS}, "OP": "+"}
    ]
    # Pattern 2: wellhead rated for 15k psi
    pressure_pattern2 = [
        {"LOWER": {"IN": PRESSURE_TARGET_PARTS}, "OP": "+"},
        {"LOWER": {"IN": ["rated", "designed"]}},
        {"LOWER": "for", "OP": "?"},
        {"TEXT": {"REGEX": r"[\d,]+(?:k|K)?"}},
        {"LOWER": {"IN": PRESSURE_UNITS}}
    ]
    matcher.add("PRESSURE_SPEC", [pressure_pattern1, pressure_pattern2])

    # --- QUANTITY PATTERNS ---
    # Pattern 1: three manifolds, two subsea trees
    quantity_pattern1 = [
        {"LIKE_NUM": True},
        {"LOWER": {"IN": SORTED_QUANTITY_TARGET_PARTS}, "OP": "+"}
    ]
    # Pattern 2: supply of 10 wellheads
    quantity_pattern2 = [
        {"LEMMA": {"IN": ["supply", "install", "deliver", "provide", "order", "fabricate", "build", "construct"]}},
        {"LOWER": "of", "OP": "?"},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": SORTED_QUANTITY_TARGET_PARTS}, "OP": "+"}
    ]
    matcher.add("QUANTITY_SPEC", [quantity_pattern1, quantity_pattern2])

    # --- FLOW CAPACITY PATTERNS ---
    # Pattern 1: [PART] with a capacity of [NUM] [UNIT]
    flow_cap_pattern1 = [
        {"LOWER": {"IN": FLOW_CAPACITY_TARGET_PARTS}, "OP": "+"},
        {"LOWER": {"IN": ["with", "has"]}},
        {"LOWER": "a", "OP": "?"},
        {"LOWER": {"IN": ["capacity", "flow", "rate", "throughput", "output"]}},
        {"LOWER": "of"},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": FLOW_CAPACITY_UNITS}}
    ]
    # Pattern 2: [NUM] [UNIT] [PART]
    flow_cap_pattern2 = [
        {"LIKE_NUM": True},
        {"LOWER": {"IN": FLOW_CAPACITY_UNITS}},
        {"LOWER": {"IN": FLOW_CAPACITY_TARGET_PARTS}, "OP": "+"}
    ]
    matcher.add("FLOW_CAP_SPEC", [flow_cap_pattern1, flow_cap_pattern2])

    # --- TEMPERATURE RATING PATTERNS ---
    # Pattern 1: [PART] rated to [NUM] [UNIT]
    temp_pattern1 = [
        {"LOWER": {"IN": TEMP_TARGET_PARTS}, "OP": "+"},
        {"LOWER": {"IN": ["rated", "designed", "operating"]}},
        {"LOWER": {"IN": ["to", "at", "for"]}, "OP": "?"},
        {"TEXT": {"REGEX": r"-?\d+"}},
        {"LOWER": {"IN": TEMP_UNITS}}
    ]
    # Pattern 2: [NUM] [UNIT] operating temperature
    matcher.add("TEMP_SPEC", [temp_pattern1])

    # --- DIMENSION PATTERNS (LxWxH) ---
    # e.g., "dimensions of 80 by 40 metres", "80m x 40m"
    dimension_pattern1 = [
        {"LOWER": {"IN": DIMENSION_TARGET_PARTS}, "OP": "+"},
        {"LOWER": {"IN": ["with", "has", "measuring"]}, "OP": "?"},
        {"LOWER": {"IN": ["dimensions", "a size"]}, "OP": "?"},
        {"LOWER": "of", "OP": "?"},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": ["by", "x"]}},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": DIMENSION_UNITS}, "OP": "?"}
    ]
    matcher.add("DIMENSION_SPEC", [dimension_pattern1])

    # --- ACCOMMODATION CAPACITY PATTERNS ---
    # e.g., "accommodation for 120 people", "120-person living quarters"
    accommodation_pattern1 = [
        {"LOWER": {"IN": ["accommodation", "accommodate", "capacity"]}},
        {"LOWER": "for", "OP": "?"},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": ACCOMMODATION_UNITS}}
    ]
    accommodation_pattern2 = [
        {"LIKE_NUM": True},
        {"IS_PUNCT": True, "LOWER": "-", "OP": "?"},
        {"LOWER": {"IN": ACCOMMODATION_UNITS}},
        {"LOWER": {"IN": ACCOMMODATION_TARGET_PARTS}, "OP": "+"}
    ]
    matcher.add("ACCOMMODATION_SPEC", [accommodation_pattern1, accommodation_pattern2])

    # --- STORAGE CAPACITY PATTERNS ---
    # e.g., "storage capacity of 1.2 million barrels", "can store 2 million bbls"
    storage_pattern1 = [
        {"LOWER": {"IN": STORAGE_TARGET_PARTS}, "OP": "+"},
        {"LOWER": {"IN": ["with", "has", "can"]}, "OP": "?"},
        {"LOWER": "a", "OP": "?"},
        {"LOWER": "storage"},
        {"LOWER": "capacity"},
        {"LOWER": "of"},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": ["million", "billion", "thousand"]}, "OP": "?"},
        {"LOWER": {"IN": STORAGE_UNITS}}
    ]
    storage_pattern2 = [
        {"LEMMA": "store"},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": ["million", "billion", "thousand"]}, "OP": "?"},
        {"LOWER": {"IN": STORAGE_UNITS}}
    ]
    matcher.add("STORAGE_SPEC", [storage_pattern1, storage_pattern2])

    # --- POWER GENERATION PATTERNS ---
    # e.g., "100 MW power generation module"
    power_pattern1 = [
        {"LIKE_NUM": True},
        {"LOWER": {"IN": POWER_UNITS}},
        {"LOWER": "power", "OP": "?"},
        {"LOWER": {"IN": ["generation", "capacity", "output"]}, "OP": "?"},
        {"LOWER": {"IN": POWER_TARGET_PARTS}, "OP": "+"}
    ]
    matcher.add("POWER_SPEC", [power_pattern1])

    # --- MOORING SYSTEM PATTERNS ---
    # e.g., "a 12-point spread mooring system", "internal turret mooring"
    mooring_pattern1 = [
        {"LIKE_NUM": True},
        {"IS_PUNCT": True, "LOWER": "-", "OP": "?"},
        {"LOWER": "point"},
        {"LOWER": {"IN": MOORING_TYPES}, "OP": "?"},
        {"LOWER": "mooring"},
        {"LOWER": "system", "OP": "?"}
    ]

    matches = matcher(doc)

    for match_id, start, end in matches:
        string_id = nlp.vocab.strings[match_id]
        span = doc[start:end]
        span_text = span.text
        span_text_lower = span_text.lower()
        
        identified_part_canonical = None
        identified_spec_str = None

        if string_id == "LENGTH_SPEC":
            for part_kw in SORTED_TARGET_BUILD_PARTS:
                if part_kw.lower() in span_text_lower:
                    identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                    break
            num_match = NUM_UNIT_REGEX_SPACED.search(span_text) or NUM_UNIT_REGEX_NOSPACE.search(span_text) or NUM_DASH_UNIT_REGEX.search(span_text)
            if num_match:
                value, unit = num_match.groups()
                if unit.lower() in ["kilometer", "kilometers"]: unit = "km"
                elif unit.lower() in ["meter", "meters", "metres"]: unit = "m"
                elif unit.lower() in ["mile", "miles"]: unit = "miles"
                elif unit.lower() in ["foot", "feet"]: unit = "ft"
                identified_spec_str = f"{value} {unit}"
            else: # Fallback for number words like "ten kilometers"
                num_tok, unit_tok = None, None
                for token in span:
                    if token.like_num: num_tok = token.text
                    if token.lower_ in LENGTH_UNITS: unit_tok = token.lower_
                if num_tok and unit_tok:
                    identified_spec_str = f"{num_tok} {unit_tok}"

        elif string_id == "WEIGHT_SPEC":
            for part_kw in SORTED_WEIGHT_TARGET_PARTS:
                if part_kw.lower() in span_text_lower:
                    identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                    break
            num_match = NUM_WEIGHT_UNIT_REGEX_SPACED.search(span_text) or NUM_WEIGHT_UNIT_REGEX_NOSPACE.search(span_text)
            if num_match:
                value, unit = num_match.groups()
                value = value.replace(',', '') # remove commas from numbers
                if unit.lower() in ["tonne", "tonnes", "ton", "te"]: unit = "t"
                elif unit.lower() in ["kilogram", "kilograms"]: unit = "kg"
                elif unit.lower() in ["pound", "pounds"]: unit = "lbs"
                identified_spec_str = f"{value} {unit}"
            else: # Fallback for number words
                num_tok, unit_tok = None, None
                for token in span:
                    if token.like_num: num_tok = token.text
                    if token.lower_ in WEIGHT_UNITS: unit_tok = token.lower_
                if num_tok and unit_tok:
                    identified_spec_str = f"{num_tok} {unit_tok}"

        elif string_id == "DIAMETER_SPEC":
            for part_kw in SORTED_DIAMETER_TARGET_PARTS:
                if part_kw.lower() in span_text_lower:
                    identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                    break
            
            range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*(" + "|".join(DIAMETER_UNITS) + r")", span_text, re.IGNORECASE)
            if range_match:
                val1, val2, unit_str = range_match.groups()
                val1 = val1.replace(',', '')
                val2 = val2.replace(',', '')
                if unit_str.lower() in ['inch', 'inches', '"']: unit = 'in'
                elif unit_str.lower() in ['millimeter', 'millimeters']: unit = 'mm'
                elif unit_str.lower() in ['centimeter', 'centimeters']: unit = 'cm'
                elif unit_str.lower() in ['meter', 'meters']: unit = 'm'
                elif unit_str.lower() in ['foot', 'feet']: unit = 'ft'
                else: unit = unit_str.lower()
                identified_spec_str = f"{val1}-{val2} {unit} diameter"
            else:
                num_match = NUM_DIAMETER_UNIT_REGEX_SPACED.search(span_text) or NUM_DASH_DIAMETER_UNIT_REGEX.search(span_text) or NUM_DIAMETER_UNIT_REGEX_NOSPACE.search(span_text)
                if num_match:
                    value, unit = num_match.groups()
                    value = value.replace(',', '') # remove commas from numbers
                    if unit.lower() in ['inch', 'inches', '"']: unit = 'in'
                    elif unit.lower() in ['millimeter', 'millimeters']: unit = 'mm'
                    elif unit.lower() in ['centimeter', 'centimeters']: unit = 'cm'
                    elif unit.lower() in ['foot', 'feet']: unit = 'ft'
                    identified_spec_str = f"{value} {unit} diameter"
                else: # Fallback for number words
                    num_tok, unit_tok = None, None
                    for token in span:
                        if token.like_num: num_tok = token.text
                        if token.lower_ in DIAMETER_UNITS: unit_tok = token.lower_
                    if num_tok and unit_tok:
                        identified_spec_str = f"{num_tok} {unit_tok} diameter"

        elif string_id == "DEPTH_RATING_SPEC":
            for part_kw in SORTED_DEPTH_RATING_TARGET_PARTS:
                if part_kw.lower() in span_text_lower:
                    identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                    break
            num_match = NUM_DEPTH_RATING_UNIT_REGEX.search(span_text)
            if num_match:
                value, unit = num_match.groups()
                value = value.replace(',', '')
                if unit.lower() in ['meter', 'meters']: unit = 'm'
                elif unit.lower() in ['feet']: unit = 'ft'
                identified_spec_str = f"{value} {unit} depth"
            else: # Fallback for number words
                num_tok, unit_tok = None, None
                for token in span:
                    if token.like_num: num_tok = token.text
                    if token.lower_ in DEPTH_RATING_UNITS: unit_tok = token.lower_
                if num_tok and unit_tok:
                    identified_spec_str = f"{num_tok} {unit_tok} depth"

        elif string_id == "PRESSURE_SPEC":
            for part_kw in SORTED_PRESSURE_TARGET_PARTS:
                if part_kw.lower() in span_text_lower:
                    identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                    break
            num_match = NUM_PRESSURE_UNIT_REGEX.search(span_text)
            if num_match:
                value, unit = num_match.groups()
                value = value.replace(',', '').lower()
                if 'k' in value:
                    value = str(int(float(value.replace('k', '')) * 1000))
                identified_spec_str = f"{value} {unit.lower()}"

        elif string_id == "QUANTITY_SPEC":
            num_token, part_span = None, None
            for token in span:
                if token.like_num:
                    try: # Avoid matching years
                        num_val = float(token.text)
                        if 1950 < num_val < 2100: continue
                        num_token = token
                    except ValueError: # For number words like "three"
                        num_token = token
            
            # Find the part name within the matched span
            for part_kw in SORTED_QUANTITY_TARGET_PARTS:
                if part_kw.lower() in span_text_lower:
                    identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                    break
            
            if num_token and identified_part_canonical:
                # Heuristic: if the part is singular and number is large, it might be a model number.
                # This is a simple check; more complex logic could be added.
                if not identified_part_canonical.endswith('s') and num_token.is_digit and float(num_token.text) > 100:
                    continue
                identified_spec_str = f"{num_token.text} units"

        elif string_id == "FLOW_CAP_SPEC":
            for part_kw in SORTED_FLOW_CAPACITY_TARGET_PARTS:
                if part_kw.lower() in span_text_lower:
                    identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                    break
            num_match = NUM_FLOW_CAPACITY_UNIT_REGEX.search(span_text)
            if num_match:
                value, unit = num_match.groups()
                value = value.replace(',', '')
                identified_spec_str = f"{value} {unit.lower()} capacity"

        elif string_id == "TEMP_SPEC":
            part_found_in_span = False
            for part_kw in SORTED_TEMP_TARGET_PARTS:
                if part_kw.lower() in span_text_lower:
                    identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                    part_found_in_span = True
                    break
            # If no part in span (e.g. "100 C operating temperature"), look in sentence
            if not part_found_in_span:
                sent_text_lower = span.sent.text.lower()
                for part_kw in SORTED_TEMP_TARGET_PARTS:
                    if part_kw.lower() in sent_text_lower:
                        identified_part_canonical = part_kw.title() if ' ' in part_kw else part_kw.capitalize()
                        break

            num_match = NUM_TEMP_UNIT_REGEX.search(span_text)
            if num_match:
                value, unit = num_match.groups()
                unit = unit.replace('°', '').lower()
                if unit == 'c': unit = 'Celsius'
                if unit == 'f': unit = 'Fahrenheit'
                identified_spec_str = f"{value} {unit} temperature"

        if identified_part_canonical and identified_spec_str:
            parsed_specs_set.add(f"{identified_part_canonical}: {identified_spec_str}")
        else:
            parsed_specs_set.add(span_text.strip())

    return ', '.join(sorted(list(parsed_specs_set))) if parsed_specs_set else ''


def filter_companies(company_list, text):
    if not company_list:
        return []
    doc = nlp(text) 
    filtered = set()
    designators = ['co\\.', 'inc\\.', 'ltd\\.', 'gmbh', 'llc', 'corp\\.', 'plc', 'group', 'solutions', 'energy', 'oil & gas', 'international', 'holdings', 'corporation', 'industries', 'ventures', 'resources', 'services', 'systems']
    known_companies = ["Saudi Aramco", "Petronas", "Shell", "BP", "ExxonMobil", "TotalEnergies", "Equinor", "Chevron", "ConocoPhillips", "ENI", "Sinopec", "CNPC", "Gazprom", "Baker Hughes", "Schlumberger", "Halliburton", "TechnipFMC", "Subsea 7", "Saipem", "McDermott", "Wood", "Worley"]

    for company_name_str in company_list: 
        company_name = str(company_name_str).strip() 
        found = False
        for kc in known_companies:
            if kc.lower() in company_name.lower() or company_name.lower() in kc.lower():
                filtered.add(kc)
                found = True
                break
        if found: continue

        if any(re.search(r'\b' + d + r'\b', company_name.lower()) for d in designators):
            filtered.add(company_name)
            continue
        
        for ent in doc.ents:
            if ent.label_ == 'ORG' and company_name in ent.text and len(ent.text.split()) > len(company_name.split()):
                if any(re.search(r'\b' + d + r'\b', ent.text.lower()) for d in designators) or ent.text in known_companies:
                    filtered.add(ent.text)
                    found = True
                    break
        if found: continue

        if len(company_name.split()) == 1:
            if company_name.lower() in ["technology", "industrial", "energy", "company", "group", "systems", "solutions"]:
                continue
            if re.search(r'\b' + re.escape(company_name) + r'\s+(?:' + '|'.join(designators) + r')\b', text, re.IGNORECASE) or \
               re.search(r'\b(?:' + '|'.join(designators) + r')\s+' + re.escape(company_name) + r'\b', text, re.IGNORECASE) or \
               company_name in ["Aramco", "Shell", "BP", "ExxonMobil", "TotalEnergies", "Equinor"]: 
                filtered.add(company_name)
                continue
        else:
            filtered.add(company_name)
    return sorted(list(filtered))

def extract_entities_by_label_refined(text, labels):
    text = clean_text(text)
    if not text: return ''
    doc = nlp(text)
    entities = [ent.text.strip() for ent in doc.ents if ent.label_ in labels]
    
    if 'ORG' in labels:
        entities = filter_companies(entities, text) 
        
    return ', '.join(sorted(set(entities)))

def extract_scope_keywords(text):
    text = clean_text(text)
    if not text: return ''
    text_lower = text.lower()
    found_keywords = set()
    for kw in ALL_BUILD_KEYWORDS:
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower):
            found_keywords.add(kw)
        elif len(kw.split()) > 1 and kw.lower() in text_lower:
            found_keywords.add(kw)
    return ', '.join(sorted(found_keywords))

def extract_delays_dates(text):
    text = clean_text(text)
    if not text: return ''
    doc = nlp(text)
    delay_keywords = ['delay', 'postpone', 'push back', 'reschedule', 'deadline', 'extension', 'setback', 'deferment']
    mentions_delay = any(kw in text.lower() for kw in delay_keywords)
    if mentions_delay:
        relevant_dates = []
        for date_ent in doc.ents:
            if date_ent.label_ == 'DATE':
                span_around_date = doc[max(0, date_ent.start - 10):min(len(doc), date_ent.end + 10)].text.lower()
                if any(kw in span_around_date for kw in delay_keywords):
                    relevant_dates.append(date_ent.text)
        return ', '.join(sorted(set(relevant_dates)))
    return ''

def extract_budget(text):
    text = clean_text(text)
    if not text: return ''
    doc = nlp(text)
    money_entities = [ent.text for ent in doc.ents if ent.label_ == 'MONEY']
    money_patterns = re.findall(
        r'\b(?:USD|EUR|GBP|A?\$|€|£)\s?\d+(?:\.\d+)?\s*(?:billion|million|bn|mn)?\b|\b\d+(?:\.\d+)?\s*(?:billion|million|bn|mn)\s*(?:USD|EUR|GBP|A?\$|€|£)?\b',
        text, re.IGNORECASE
    )
    all_money = list(set(money_entities + money_patterns))
    return ', '.join(sorted(all_money))

def extract_quotes(text):
    text = clean_text(text)
    if not text: return ''
    return ' | '.join(re.findall(r'"(.*?)"', text))

def extract_project_status(text):
    text = clean_text(text).lower()
    if not text: return ''
    doc = nlp(text)
    found_statuses = set()
    matcher = Matcher(nlp.vocab)

    decommissioning_patterns = [
        [{"LOWER": "plug"}, {"LOWER": "and"}, {"LOWER": "abandon"}], [{"LOWER": "p&a"}],
        [{"LEMMA": "decommission"}]
    ]
    matcher.add("DECOMMISSIONING_STATUS", decommissioning_patterns)

    awarded_patterns = [
        [{"LEMMA": "contract"}, {"LEMMA": "award"}], [{"LEMMA": "award"}, {"LEMMA": "contract"}],
        [{"LEMMA": "sign"}, {"LEMMA": "contract"}], [{"LEMMA": "contract"}, {"LEMMA": "sign"}],
        [{"LEMMA": "deal"}, {"LEMMA": "sign"}], [{"LEMMA": "agreement"}, {"LEMMA": "sign"}],
        [{"LEMMA": "award"}], [{"LEMMA": "secure"}], [{"LEMMA": "win"}],
        [{"LOWER": "letter"}, {"LOWER": "of"}, {"LOWER": "intent"}], 
        [{"LOWER": "memorandum"}, {"LOWER": "of"}, {"LOWER": "understanding"}],
        [{"LOWER": "reach"}, {"LOWER": "agreement"}]
    ]
    matcher.add("AWARDED_STATUS", awarded_patterns)

    tendered_patterns = [
        [{"LEMMA": "tender"}, {"LEMMA": "issue"}], [{"LOWER": "invitation"}, {"LOWER": "to"}, {"LOWER": "bid"}],
        [{"LOWER": "pre-qualification"}], [{"LEMMA": "bid"}, {"LEMMA": "process"}],
        [{"LOWER": "call"}, {"LOWER": "for"}, {"LOWER": "tenders"}], [{"LEMMA": "tender"}, {"LEMMA": "launch"}],
        [{"LEMMA": "request"}, {"LOWER": "for"}, {"LOWER": "proposal"}], [{"LOWER": "rfp"}],
        [{"LOWER": "expressions"}, {"LOWER": "of"}, {"LOWER": "interest"}], 
        [{"LOWER": "inviting"}, {"LOWER": "bids"}]
    ]
    matcher.add("TENDERED_STATUS", tendered_patterns)
    
    planned_patterns = [
        [{"LOWER": {"IN": ["project", "field", "development"]}}, {"LEMMA": "plan"}], 
        [{"LEMMA": "plan"}, {"POS": "PART", "OP": "?"}, {"LEMMA": "to"}, {"LOWER": {"IN": ["develop", "build", "construct", "start", "proceed"]}}],
        [{"LOWER": "new"}, {"LOWER": {"IN": ["project", "development", "field"]}}, {"LEMMA": "propose"}],
        [{"LOWER": "feasibility"}, {"LOWER": "study"}], [{"LOWER": "concept"}, {"LOWER": "study"}],
        [{"LOWER": "pre-feed"}], [{"LOWER": "front-end"}, {"LOWER": "engineering"}, {"LOWER": "design"}],
        [{"LOWER": "conceptual"}, {"LOWER": "design"}], [{"LOWER": "environmental"}, {"LOWER": "impact"}, {"LOWER": "assessment"}],
        [{"LOWER": "considering"}, {"LOWER": "a"}, {"LOWER": {"IN": ["new", "potential"]}}, {"LOWER": "project"}],
        [{"LOWER": "exploring"}, {"LOWER": "options"}], [{"LOWER": "potential"}, {"LOWER": "development"}],
        [{"LOWER": "earmarked"}, {"LOWER": "for"}, {"LOWER": "development"}],
        [{"LOWER": "set"}, {"LOWER": "to"}, {"LOWER": "begin"}], 
        [{"LOWER": "expected"}, {"LOWER": "to"}, {"LOWER": "start"}],
    ]
    matcher.add("PLANNED_STATUS", planned_patterns)

    under_construction_patterns = [
        [{"LOWER": "under"}, {"LOWER": "construction"}], [{"LOWER": "being"}, {"LEMMA": "build"}],
        [{"LOWER": "ongoing"}, {"LEMMA": "develop"}], [{"LEMMA": "fabrication"}, {"LOWER": "underway"}],
        [{"LEMMA": "construction"}, {"LOWER": "ongoing"}], [{"LEMMA": "install"}], 
        [{"LEMMA": "drilling"}, {"LOWER": "commence"}], [{"LOWER": "drilling"}, {"LOWER": "campaign"}],
        [{"LOWER": "work"}, {"LOWER": "begun"}], [{"LOWER": "construction"}, {"LEMMA": "progress"}],
        [{"LOWER": "hook-up"}, {"LOWER": "and"}, {"LOWER": "commissioning"}],
        [{"LOWER": "nearing"}, {"LOWER": "completion"}],
    ]
    matcher.add("UNDER_CONSTRUCTION_STATUS", under_construction_patterns)

    completed_patterns = [
        [{"LEMMA": "complete"}], [{"LEMMA": "commission"}], [{"LOWER": "online"}],
        [{"LEMMA": "production"}, {"LEMMA": "start"}], [{"LOWER": "handed"}, {"LOWER": "over"}],
        [{"LEMMA": "deliver"}], [{"LEMMA": "achieve"}, {"LOWER": "first"}, {"LOWER": "oil"}],
        [{"LOWER": "first"}, {"LOWER": "gas"}], [{"LOWER": "brought"}, {"LOWER": "into"}, {"LOWER": "production"}],
        [{"LOWER": "commence"}, {"LOWER": "production"}], 
        [{"LOWER": "fully"}, {"LOWER": "operational"}],
        [{"LOWER": "production"}, {"LOWER": "began"}]
    ]
    matcher.add("COMPLETED_STATUS", completed_patterns)

    delayed_patterns = [
        [{"LEMMA": {"IN": ["delay", "postpone", "reschedule", "defer", "stall", "halt"]}}],
        [{"LOWER": "push"}, {"LOWER": "back"}],
        [{"LOWER": "pushed"}, {"LOWER": "out"}],
        [{"LEMMA": "setback"}], [{"LEMMA": "deferment"}],
        [{"LOWER": "on"}, {"LOWER": "hold"}], [{"LEMMA": "suspension"}],
        [{"LEMMA": "slippage"}], [{"LOWER": "behind"}, {"LOWER": "schedule"}],
        [{"LOWER": "timeline"}, {"LEMMA": "extension"}],
        [{"LEMMA": "late"}], [{"LOWER": "running"}, {"LOWER": "late"}],
        [{"LOWER": "experiencing"}, {"LEMMA": "delay", "OP": "+"}],
        [{"LEMMA": "face"}, {"LEMMA": "delay", "OP": "+"}]
    ]
    matcher.add("DELAYED_STATUS", delayed_patterns)

    cancelled_patterns = [
        [{"LEMMA": {"IN": ["cancel", "scrap", "terminate", "shelve", "withdraw"]}}], 
        [{"LEMMA": "abandon"}, {"LOWER": {"IN": ["project", "plan", "development", "effort", "initiative"]}}], 
        [{"LEMMA": "halted"}],
        [{"LOWER": "not"}, {"LOWER": "proceed"}],
        [{"LOWER": "no"}, {"LOWER": "longer"}, {"LOWER": "planned"}],
        [{"LOWER": "no"}, {"LOWER": "longer"}, {"LEMMA": "pursue"}],
        [{"LOWER": "project"}, {"LOWER": "fail"}],
        [{"LOWER": {"IN": ["contract", "agreement"]}}, {"LEMMA": "terminate"}], 
        [{"LOWER": "project"}, {"LEMMA": "terminate"}], 
        [{"LOWER": "pull"}, {"LOWER": "the"}, {"LOWER": "plug"}],
        [{"LOWER": "put"}, {"LOWER": "on"}, {"LOWER": "ice"}],
        [{"LEMMA": "suspend"}, {"LOWER": "indefinitely"}]
    ]
    matcher.add("CANCELLED_STATUS", cancelled_patterns)
    
    fid_patterns = [
        [{"LOWER": "final"}, {"LOWER": "investment"}, {"LOWER": "decision"}], [{"LOWER": "fid"}]
    ]
    matcher.add("FID_STATUS", fid_patterns)

    matches = matcher(doc)
    for match_id, start, end in matches:
        string_id = nlp.vocab.strings[match_id]
        status_map = {
            "AWARDED_STATUS": 'awarded', "TENDERED_STATUS": 'tendered',
            "PLANNED_STATUS": 'planned', "UNDER_CONSTRUCTION_STATUS": 'under construction',
            "COMPLETED_STATUS": 'completed', "DELAYED_STATUS": 'delayed',
            "CANCELLED_STATUS": 'cancelled', "FID_STATUS": 'FID',
            "DECOMMISSIONING_STATUS": 'decommissioning' 
        }
        if string_id in status_map:
            found_statuses.add(status_map[string_id])

    priority_order = ['cancelled', 'decommissioning', 'completed', 'delayed', 'FID', 'awarded', 'under construction', 'tendered', 'planned']
    for status in priority_order:
        if status in found_statuses:
            return status
    return ''

def find_capacity_subject(capacity_span, doc):
    """
    Finds the subject of a capacity measurement using dependency parsing and noun chunk analysis.
    Returns the subject text or a generic type.
    """
    # --- Strategy 1: Find the subject of the verb governing the capacity ---
    # e.g., "[The field] will produce [100,000 bpd]"
    # e.g., "[The FPSO] has a capacity of [100,000 bpd]"
    verb = None
    # Traverse up the dependency tree to find the main verb
    for ancestor in capacity_span.root.ancestors:
        if ancestor.pos_ == "VERB":
            verb = ancestor
            break
    
    if verb:
        subjects = [child for child in verb.children if child.dep_ in ("nsubj", "nsubjpass")]
        if subjects:
            subject_root = subjects[0]
            for chunk in doc.noun_chunks:
                if subject_root in chunk:
                    name = " ".join(tok.text for tok in chunk if tok.pos_ not in ['DET', 'PRON'])
                    return name.strip()

    # --- Strategy 2: Check for prepositional attachment (e.g., "capacity of [the field]") ---
    if capacity_span.root.head.text.lower() in ['of', 'for']:
        owner = capacity_span.root.head.head
        for chunk in doc.noun_chunks:
            if owner in chunk:
                name = " ".join(tok.text for tok in chunk if tok.pos_ not in ['DET', 'PRON'])
                if name.lower() not in ["capacity", "production", "output", "throughput"]:
                    return name.strip()

    # --- Strategy 3: Proximity search for a relevant noun chunk (less precise, but a good fallback) ---
    window_start = max(0, capacity_span.start - 15)
    context_window_chunks = [chunk for chunk in doc.noun_chunks if chunk.end <= capacity_span.start and chunk.start >= window_start]
    
    for chunk in reversed(context_window_chunks):
        chunk_text_lower = chunk.text.lower()
        if any(kw in chunk_text_lower for keywords in ENTITY_KEYWORDS_FOR_CAPACITY.values() for kw in keywords):
            name = " ".join(tok.text for tok in chunk if tok.pos_ not in ['DET', 'PRON'])
            return name.strip()
            
    # --- Strategy 4: Fallback to a generic entity type from the sentence ---
    sent = capacity_span.sent
    for entity_type, keywords in ENTITY_KEYWORDS_FOR_CAPACITY.items():
        if any(kw in sent.text.lower() for kw in keywords):
            return f"({entity_type})"
            
    return None

def extract_production_capacity_refined(text):
    """
    Extracts all mentions of production, storage, or throughput capacity and intelligently
    links them to the corresponding entity (field, platform, pipeline, etc.).
    """
    text = clean_text(text)
    if not text: return ''
    doc = nlp(text)
    extracted_capacities = set()

    # Expanded and more specific regex for units
    CAPACITY_UNITS_REGEX = r"bpd|boe/d|boepd|mmscfd|scfd|tpd|mcfd|bbl/d|bcfd|mboed|tcf/d|mcm/d|gj/d|tonnes/year|t/y|t/d|barrels of oil equivalent per day|cubic feet per day|m3/d|tonne/day|barrels per day|cubic meters per day|tonnes per day"
    CAPACITY_NOUNS_REGEX = r"barrels|cubic|feet|meters|tonnes|bbl|cf|m3|boe"
    TIME_UNITS_REGEX = r"day|d|hour|hr|h|year|yr|y|annum"

    capacity_matcher = Matcher(nlp.vocab)
    
    # Pattern 1: Standard units like 100,000 bpd
    pattern1 = [
        {"LIKE_NUM": True},
        {"LOWER": {"IN": ["million", "billion", "thousand", "mn", "bn", "k"]}, "OP": "?"},
        {"LOWER": {"REGEX": CAPACITY_UNITS_REGEX}},
    ]
    # Pattern 2: Descriptive units like 2.5 million tonnes per annum
    pattern2 = [
        {"LIKE_NUM": True},
        {"LOWER": {"IN": ["million", "billion", "thousand", "mn", "bn", "k"]}},
        {"LOWER": {"REGEX": CAPACITY_NOUNS_REGEX}},
        {"LOWER": "per"},
        {"LOWER": {"REGEX": TIME_UNITS_REGEX}},
    ]
    # Pattern 3: Simpler version like 100,000 barrels
    pattern3 = [
        {"LIKE_NUM": True},
        {"LOWER": {"REGEX": CAPACITY_NOUNS_REGEX}},
        {"LOWER": "per", "OP": "?"},
        {"LOWER": {"REGEX": TIME_UNITS_REGEX}, "OP": "?"},
    ]
    
    capacity_matcher.add("PRODUCTION_CAPACITY", [pattern1, pattern2, pattern3])
    matches = capacity_matcher(doc)    

    # Filter out overlapping matches, preferring the longest one
    spans = [doc[start:end] for _, start, end in matches]
    filtered_spans = spacy.util.filter_spans(spans)

    for span in filtered_spans:
        # Skip if the number is part of a date or money entity in the same sentence
        is_irrelevant = any(ent.label_ in ['DATE', 'MONEY'] for ent in span.sent.ents if ent.start < span.end and ent.end > span.start)
        if is_irrelevant: continue
        
        capacity_text = " ".join(span.text.split()) # Normalize whitespace
        
        # Find the subject/owner of this capacity
        subject = find_capacity_subject(span, doc)
        
        if subject:
            # Clean up subject if it's just a generic type
            if subject.startswith("(") and subject.endswith(")"):
                extracted_capacities.add(f"{capacity_text} {subject}")
            else:
                extracted_capacities.add(f"{subject}: {capacity_text}")
        else:
            # If no subject is found, just add the capacity.
            extracted_capacities.add(capacity_text)
            
    return ', '.join(sorted(list(extracted_capacities)))

def extract_contract_types(text):
    text = clean_text(text)
    if not text: return ''
    contract_keywords_list = [ 
        'EPC', 'EPCI', 'EPCC', 'FEED', 'LSTK', 'MOU', 'joint venture', 'framework agreement', 'EPMC', 'EPC-E', 'EPC-E/E',
        'service agreement', 'subcontract', 'supply agreement', 'alliance agreement',
        'lease agreement', 'charter agreement', 'drilling contract', 'construction contract',
        'maintenance contract', 'operation and maintenance', 'O&M', 'engineering contract',
        'procurement contract', 'turnkey contract', 'build-own-operate-transfer', 'BOOT',
        'production sharing agreement', 'PSA', 'rig contract', 'vessel contract', 'consultancy contract'
    ]
    doc = nlp(text)
    found_contract_types = set()
    matcher = Matcher(nlp.vocab)

    pattern1 = [
        {"LOWER": {"IN": [k.lower() for k in contract_keywords_list]}},
        {"LEMMA": {"IN": ["contract", "agreement", "deal", "accord", "pact", "charter", "lease", "terms"]}}
    ]
    matcher.add("CONTRACT_TYPE_PHRASE_1", [pattern1])

    pattern2 = [
        {"LEMMA": {"IN": ["contract", "agreement"]}},
        {"LOWER": {"IN": ["for", "to"]}, "OP": "?"},
        {"LOWER": {"IN": ["the", "provide"]}, "OP": "?"},
        {"LOWER": "of", "OP": "?"},
        {"LOWER": {"IN": [k.lower() for k in contract_keywords_list]}}
    ]
    matcher.add("CONTRACT_TYPE_PHRASE_2", [pattern2])
    
    pattern3 = [
        {"LEMMA": {"IN": ["award", "sign", "secure", "win", "enter", "finalize", "negotiate", "issue", "grant", "land"]}},
        {"LOWER": {"IN": ["a", "an", "the"]}, "OP": "?"},
        {"LOWER": {"IN": [k.lower() for k in contract_keywords_list]}},
        {"LEMMA": {"IN": ["contract", "agreement", "deal"]}, "OP": "?"} 
    ]
    matcher.add("VERB_CONTRACT_TYPE", [pattern3])

    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        span_text_lower = span.text.lower()
        best_found_kw = ""
        for canonical_kw in contract_keywords_list:
            if re.search(r'\b' + re.escape(canonical_kw.lower()) + r'\b', span_text_lower):
                if len(canonical_kw) > len(best_found_kw):
                    best_found_kw = canonical_kw
        if best_found_kw:
            found_contract_types.add(best_found_kw)

    if not found_contract_types:
        for ct in contract_keywords_list:
            if re.search(r'\b' + re.escape(ct) + r'\b', text, re.IGNORECASE):
                found_contract_types.add(ct)

    return ', '.join(sorted(list(found_contract_types)))

def summarize_text_textrank(text, num_sentences=3, diversity_lambda=0.6):
    """
    Generates a robust, high-quality summary using a hybrid of TextRank and Maximal Marginal Relevance (MMR).
    It prioritizes sentences with key information and ensures diversity to cover multiple aspects of the news.
    Includes multiple fallbacks to prevent returning an empty summary.
    """
    text = clean_text(text)
    if not text:
        return ''

    doc = nlp(text)
    # Filter out sentences that are too short or don't have a vector representation.
    sentences = [sent for sent in doc.sents if len(sent.text.strip()) > 5 and sent.vector_norm]

    # --- Fallback 1: If text is too short or no valid sentences are found, return the beginning of the text.
    if not sentences or len(sentences) <= num_sentences:
        original_sents = list(doc.sents)
        return ' '.join([s.text.replace('\n', ' ').strip() for s in original_sents[:num_sentences]])

    sentence_vectors = np.array([sent.vector for sent in sentences])
    similarity_matrix = cosine_similarity(sentence_vectors)

    # --- Heuristic Scoring for initial weights ---
    initial_scores = np.ones(len(sentences))
    status_keywords = ['award', 'complete', 'delay', 'cancel', 'fid', 'tender', 'plan', 'construct', 'decommission', 'sign', 'secure']
    for i, sent in enumerate(sentences):
        if any(ent.label_ in ['ORG', 'PRODUCT', 'FAC', 'GPE', 'MONEY'] for ent in sent.ents):
            initial_scores[i] += 0.3 # Boost for important entities
        if any(keyword in sent.text.lower() for keyword in status_keywords):
            initial_scores[i] += 0.4 # Higher boost for status keywords
        if i == 0: # Boost the first sentence
            initial_scores[i] += 0.5

    # --- TextRank with initial scores ---
    scores = np.copy(initial_scores)
    damping_factor = 0.85
    try:
        for _ in range(100):
            prev_scores = np.copy(scores)
            for i in range(len(sentences)):
                rank_sum = sum(
                    (similarity_matrix[j][i] * prev_scores[j]) / (np.sum(similarity_matrix[j]) or 1)
                    for j in range(len(sentences)) if i != j
                )
                scores[i] = (1 - damping_factor) * initial_scores[i] + damping_factor * rank_sum
            if np.sum(np.abs(scores - prev_scores)) < 1e-5:
                break
    except (ValueError, IndexError):
        # If TextRank fails for some reason, scores will just be the initial_scores
        pass
    
    # --- MMR for diverse sentence selection ---
    selected_indices = []
    try:
        candidate_indices = list(range(len(sentences)))
        best_start_idx = np.argmax(scores)
        selected_indices.append(best_start_idx)
        candidate_indices.remove(best_start_idx)

        while len(selected_indices) < num_sentences and candidate_indices:
            mmr_scores = []
            for i in candidate_indices:
                relevance_score = scores[i]
                redundancy_score = max(similarity_matrix[i][j] for j in selected_indices)
                mmr = diversity_lambda * relevance_score - (1 - diversity_lambda) * redundancy_score
                mmr_scores.append((mmr, i))
            
            if not mmr_scores: break
            best_next_idx = max(mmr_scores)[1]
            selected_indices.append(best_next_idx)
            candidate_indices.remove(best_next_idx)
    except (ValueError, IndexError):
        selected_indices = [] # Reset on error to trigger fallback

    # --- Fallback 2: If MMR fails, use top N from scores (TextRank or heuristic) ---
    if not selected_indices:
        ranked_sentence_indices = scores.argsort()[-num_sentences:][::-1]
        selected_indices = list(ranked_sentence_indices)

    # --- Final Output Construction ---
    sorted_indices = sorted(selected_indices)
    summary_sentences = [sentences[i].text.replace('\n', ' ').strip() for i in sorted_indices]
    
    # --- Fallback 3: Final sanity check to ensure output is never empty if text exists.
    if not summary_sentences:
        original_sents = list(doc.sents)
        return ' '.join([s.text.replace('\n', ' ').strip() for s in original_sents[:num_sentences]])

    return ' '.join(summary_sentences)

def classify_offshore_onshore(text):
    text = clean_text(text).lower()
    offshore_keywords = {
        'offshore': 3, 'subsea': 3, 'fpso': 4, 'flng': 4, 'fsru': 4, 'floating': 2,
        'deepwater': 2, 'mooring': 2, 'riser': 2, 'jack-up': 3, 'drillship': 3,
        'spar': 3, 'tlp': 3, 'platform': 2, 'jacket': 2, 'hull': 1, 'caisson': 1,
        'umbilical': 2, 'flowline': 2, 'topside': 2, 'topsides': 2, 'wellhead': 1,
        'manifold': 1, 'christmas tree': 1, 'surf': 3, 'gbs': 2, 'sea bed': 2,
        'marine': 2, 'vessel': 1, 'installation vessel': 3, 'anchor handling tug': 2,
        'hook-up': 2, 'commissioning (offshore)': 3, 'offshore removal': 3, 'semisubmersible': 3,
        'drilling rig': 2
    }
    onshore_keywords = {
        'onshore': 3, 'land-based': 3, 'refinery': 4, 'petrochemical': 4,
        'gas plant': 3, 'pipeline terminal': 2, 'compressor station': 2,
        'gas treatment': 2, 'processing plant': 3, 'storage tank': 1,
        'industrial complex': 2, 'onshore disposal': 3, 'midstream': 1, 'downstream': 1,
        'lng terminal': 3, 'storage facility': 2, 'gas processing plant': 3
    }
    offshore_score = sum(score for kw, score in offshore_keywords.items() if kw in text)
    onshore_score = sum(score for kw, score in onshore_keywords.items() if kw in text)

    for keyword in BUILD_PARTS.union(BUILD_PROCESS_OPTIONS):
        kw_lower = keyword.lower()
        if kw_lower in text:
            if "subsea" in kw_lower or "offshore" in kw_lower or kw_lower in ['fpso', 'flng', 'fsru', 'tlp', 'spar', 'jacket', 'hull']:
                offshore_score += 1.5
            elif "topsides" in kw_lower: offshore_score += 0.5 
            elif "pipeline" in kw_lower:
                if 'subsea pipeline' in text: offshore_score += 1.5
                elif 'onshore pipeline' in text: onshore_score += 1.5
            elif "offshore removal" in kw_lower: offshore_score += 2
            elif "onshore disposal" in kw_lower: onshore_score += 2
            elif "installation" in kw_lower:
                if 'subsea installation' in text or 'offshore installation' in text: offshore_score += 1.5
                elif 'onshore installation' in text: onshore_score += 1.5
            elif "decommissioning" in kw_lower:
                if 'offshore decommissioning' in text: offshore_score += 1.5
                elif 'onshore decommissioning' in text: onshore_score += 1.5 

    if len(text.split()) < 20 and offshore_score > 0 and onshore_score > 0:
        if offshore_score == onshore_score: return 'Unclear'
        return 'Offshore' if offshore_score > onshore_score * 2 else ('Onshore' if onshore_score > onshore_score * 2 else 'Mixed')
    if offshore_score > onshore_score: return 'Offshore'
    if onshore_score > offshore_score: return 'Onshore'
    if offshore_score > 0 or onshore_score > 0: return 'Mixed'
    return 'Unclear'

def generate_ai_opinion(row, _): # Keep signature for compatibility
    """
    Generates a more insightful, narrative-style AI opinion by synthesizing 
    extracted data, prioritizing key events, and creating a logical flow.
    """
    # 1. Data Gathering from the row - using .get() for safety
    project_names = row.get('Field/Project Names', '')
    companies = row.get('Operators/Companies', '')
    locations = row.get('Locations', '')
    project_status = row.get('Project Status', '')
    scope_details = row.get('Scope Details', '')
    offshore_onshore = row.get('Offshore/Onshore Classification', '')
    budget = row.get('Budget / Value', '')
    production_capacity = row.get('Production Capacity', '')
    contract_types = row.get('Contract Types', '')
    specifications = row.get('Build Part Specifications', '')
    vessel_info = row.get('Vessel Info', '')
    delays_dates = row.get('Delays / Dates', '')
    summary = row.get('Summary', '')

    # 2. Identify Core Subject with more nuance
    main_subject = "An upstream energy project"
    company_subject = ""
    if project_names:
        project_list = project_names.split(', ')
        main_subject = f"The {project_list[0]} project"
        if len(project_list) > 1:
            main_subject += " and related developments"
    elif companies:
        company_list = companies.split(', ')
        company_subject = f"{company_list[0]}"
        if len(company_list) > 1:
            company_subject += " and its partners"
        main_subject = f"A project led by {company_subject}"

    # 3. Determine the Main "Event" and construct lead sentence
    lead_sentence = ""
    
    # Priority 1: Critical Status Changes
    if project_status in ['cancelled', 'delayed']:
        status_verb = "been cancelled" if project_status == 'cancelled' else "is facing significant delays"
        date_info = f", with the timeline reportedly pushed to {delays_dates.split(', ')[0]}" if delays_dates else ""
        lead_sentence = f"In a critical update, {main_subject} has {status_verb}{date_info}."
    elif project_status in ['completed', 'FID']:
        milestone = "completion and has come online" if project_status == 'completed' else "reached a Final Investment Decision (FID)"
        lead_sentence = f"{main_subject} has achieved a major milestone, having reached {milestone}."
    # Priority 2: Contract Award
    elif project_status == 'awarded':
        contract_info = f"a key {contract_types.split(', ')[0]} contract" if contract_types else "a significant contract"
        company_info = f"{company_subject} has secured" if company_subject else "A contract has been secured for"
        vessel_subject = f" for the charter of the {vessel_info.split(' (')[0]}" if vessel_info else ""
        lead_sentence = f"Signaling a major step forward, {company_info} {contract_info}{vessel_subject} for the project."
    # Priority 3: Early Stages
    elif project_status in ['planned', 'tendered']:
        stage_phrase = "is in the tendering phase" if project_status == 'tendered' else "is in the early planning and design stages"
        lead_sentence = f"The {offshore_onshore.lower() if offshore_onshore not in ['Unclear', 'Mixed'] else 'energy'} sector sees new potential as {main_subject} {stage_phrase}."
    # Priority 4: Construction
    elif project_status == 'under construction':
        lead_sentence = f"Development is actively progressing for {main_subject}, which is now under construction."
    # Priority 5: Decommissioning
    elif project_status == 'decommissioning':
        lead_sentence = f"At the end of its lifecycle, {main_subject} is now undergoing decommissioning."
    
    # If no lead sentence from status, create a generic one
    if not lead_sentence:
        if project_names and locations:
             lead_sentence = f"An update has been provided on {main_subject}, located in {locations.split(', ')[0]}."
        elif companies and locations:
             lead_sentence = f"{company_subject} is advancing an upstream project in {locations.split(', ')[0]}."
        else:
            # Fallback to summary or generic statement if no lead can be formed
            if summary: return summary.split('.')[0] + "."
            if companies: return f"{companies.split(', ')[0]} is making an upstream move."
            return "General upstream oil and gas news."

    # 4. Add Supporting Details
    supporting_details = []
    
    # Vessel Info (if not already in lead sentence)
    if vessel_info:
        if not (lead_sentence and vessel_info.split(' (')[0] in lead_sentence):
            supporting_details.append(f"The agreement involves the vessel {vessel_info.split(' (')[0]}.")

    # Location and Type (if not already in lead)
    if locations and locations.split(', ')[0] not in lead_sentence:
        loc_text = f"located in {locations.split(', ')[0]}"
        type_text = f"as an {offshore_onshore.lower()} development" if offshore_onshore not in ['Unclear', 'Mixed'] else ""
        if type_text:
            supporting_details.append(f"The project is {loc_text} and is classified {type_text}.")
        else:
            supporting_details.append(f"The project is {loc_text}.")

    # Scope
    if scope_details:
        scope_list = [s.strip().lower() for s in scope_details.split(',')]
        scope_groups = {
            'full-field development (EPCI)': ['epc', 'epci', 'epcc'],
            'SURF package': ['surf', 'pipelines', 'flowlines', 'riser', 'umbilical'],
            'subsea production systems': ['subsea systems', 'tree', 'manifold', 'wellhead'],
            'floating facilities': ['fpso', 'flng', 'fsru', 'tlp', 'spar'],
            'fixed structures': ['jacket', 'hull', 'topside', 'topsides'],
            'decommissioning activities': ['decommissioning']
        }
        found_groups = [group_name for group_name, keywords in scope_groups.items() if any(kw in scope_list for kw in keywords)]
        
        if found_groups:
            scope_summary = " and ".join(found_groups)
            supporting_details.append(f"Its scope is comprehensive, focusing on {scope_summary}.")
        elif scope_list:
            supporting_details.append(f"The work includes {scope_list[0]} and other related activities.")

    # Financials and Capacity
    financials = []
    if budget:
        financials.append(f"a reported budget of {budget.split(', ')[0]}")
    if production_capacity:
        cap_str = production_capacity.split(', ')[0]
        if ":" in cap_str: cap_str = cap_str.split(':')[1].strip()
        financials.append(f"a targeted production capacity of {cap_str}")
    
    if financials:
        supporting_details.append(f"This is a significant undertaking with {' and '.join(financials)}.")

    # Technical Specs
    if specifications and not any("scope" in s or "SURF" in s or "subsea" in s for s in supporting_details):
        spec_summary = specifications.split(', ')[0]
        supporting_details.append(f"Key technical elements include a {spec_summary}.")

    # 5. Construct Final Opinion
    opinion_parts = [lead_sentence] + supporting_details
    final_opinion = " ".join(opinion_parts)

    # 6. Final Polish and Truncation
    final_opinion = re.sub(r'\s+', ' ', final_opinion).strip() # Normalize whitespace
    
    # Truncate if too long, but try to keep full sentences
    if len(final_opinion) > 250:
        doc = nlp(final_opinion)
        sents = list(doc.sents)
        truncated_opinion = ""
        for sent in sents:
            if len(truncated_opinion) + len(sent.text) < 240:
                truncated_opinion += sent.text + " "
            else:
                break
        final_opinion = truncated_opinion.strip()
    
    if not final_opinion.strip():
        if summary: return summary.split('.')[0] + "."
        if companies and locations: return f"{companies.split(', ')[0]} is active in {locations.split(', ')[0]}."
        if companies: return f"{companies.split(', ')[0]} is making an upstream move."
        return "General upstream oil and gas news."

    return final_opinion

def extract_packages_phases_refined(text):
    text = clean_text(text)
    if not text:
        return ''
    doc = nlp(text)
    found_items = set()
    matcher = Matcher(nlp.vocab)

    pattern_standard = [
        {"LOWER": {"IN": ["phase", "package", "epci"]}},
        {"IS_ALPHA": True, "OP": "?"}, 
        {"IS_DIGIT": True, "OP": "?"}, 
        {"SHAPE": {"REGEX": "^(d|dd|X|XX|Xx)$"}, "OP": "?"} 
    ]
    matcher.add("STANDARD_PKG_PHASE", [pattern_standard])

    pattern_phase_word_num = [
        {"LOWER": "phase"},
        {"LOWER": {"IN": ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", 
                           "first", "second", "third", "fourth", "fifth", "final", "next", "initial", "main"]}}
    ]
    matcher.add("PHASE_WORD_NUM", [pattern_phase_word_num])

    pattern_package_letter = [{"LOWER": "package"}, {"IS_UPPER": True, "LENGTH": 1}]
    matcher.add("PACKAGE_LETTER", [pattern_package_letter])
    
    pattern_descriptive_package = [
        {"LOWER": {"IN": ["work", "contract", "subsea", "topsides", "drilling", "pipeline"]}}, 
        {"LOWER": "package"},
        {"IS_ALPHA": True, "OP": "?"}, {"IS_DIGIT": True, "OP": "?"},
        {"SHAPE": {"REGEX": "^(d|dd|X|XX|Xx)$"}, "OP": "?"}
    ]
    matcher.add("DESCRIPTIVE_PACKAGE", [pattern_descriptive_package])

    pattern_phase_roman = [{"LOWER": "phase"}, {"TEXT": {"REGEX": r"^[IVXLCDM]+$"}, "OP": "+"}]
    matcher.add("PHASE_ROMAN", [pattern_phase_roman])

    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        if 3 < len(span.text) <= 30 and len(span.text.split()) <= 4 :
            found_items.add(span.text.strip())

    regex_fallback = re.findall(
        r'\b(Package\s*[A-Z0-9]+|EPCI\s*\d*|Phase\s*(?:\d+|[IVXLCDM]+(?:st|nd|rd|th)?|[Oo]ne|[Tt]wo|[Tt]hree|[Ff]irst|[Ss]econd|[Tt]hird|[Ff]inal))\b',
        text, re.IGNORECASE
    )
    for item_match_group in regex_fallback:
        item_match = item_match_group if isinstance(item_match_group, str) else item_match_group[0]
        cleaned_item = " ".join(item_match.split()) 
        if len(cleaned_item) > 3:
            if cleaned_item.lower() not in ["phase", "package", "epci"]:
                 found_items.add(cleaned_item)
            
    final_items = {item for item in found_items if item.lower() not in ["phase", "package", "epci"] or len(item.split()) > 1}
    return ', '.join(sorted(list(final_items)))

# --- Main Processing ---
def main():
    # Initialize tqdm for pandas
    tqdm.pandas(desc="Processing news articles")

    # --- File Dialog for Input ---
    root = tk.Tk()
    root.withdraw() # Hide the main tkinter window

    file_path = filedialog.askopenfilename(
        title="Select Input Excel File",
        filetypes=(("Excel files", "*.xlsx *.xls"), ("All files", "*.*"))
    )

    if not file_path:
        print("No file selected. Exiting.")
        return
    
    print(f"Loading Excel file: {file_path}")
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error loading file '{file_path}': {e}")
        return

    news_col_name = None
    if "News" in df.columns and not df["News"].isnull().all():
        news_col_name = "News"
    elif len(df.columns) >= 4 and not df.iloc[:, 3].isnull().all():
        news_col_name = df.columns[3]
        print(f"Warning: Column 'News' not found or is empty. Using the fourth column ('{news_col_name}') for news content.")
    elif len(df.columns) >= 1 and not df.iloc[:, 0].isnull().all():
        news_col_name = df.columns[0]
        print(f"Warning: Column 'News' and the fourth column not found or are empty. Using the first column ('{news_col_name}') for news content.")
    
    if news_col_name is None:
        print("Error: Could not find a suitable column for news content. Please ensure your Excel file has a column named 'News',")
        print("or that the news content is in the first or fourth column and is not empty.")
        return

    print(f"Using column '{news_col_name}' for news content.")
    print("Starting structured data extraction...")

    # Create the cleaned text column first, which will be used by all other functions
    df['Cleaned Text'] = df[news_col_name].apply(clean_text)

    # Define the extraction pipeline for clarity and easier management
    extraction_pipeline = {
        'Field/Project Names': extract_project_profiles,
        'Operators/Companies': lambda x: extract_entities_by_label_refined(x, ['ORG']),
        'Locations': lambda x: extract_entities_by_label_refined(x, ['GPE', 'LOC']),
        'Packages/Phases': extract_packages_phases_refined,
        'Vessel Info': extract_vessel_details,
        'Build Part Specifications': extract_build_part_specifications,
        'Scope Details': extract_scope_keywords,
        'Delays / Dates': extract_delays_dates,
        'Budget / Value': extract_budget,
        'Quotes / Opinions': extract_quotes,
        'Project Status': extract_project_status,
        'Production Capacity': extract_production_capacity_refined,
        'Contract Types': extract_contract_types,
        'Offshore/Onshore Classification': classify_offshore_onshore,
        'Summary': lambda x: summarize_text_textrank(x, num_sentences=3)
    }

    # Apply each function to the 'Cleaned Text' column with a progress bar
    for col_name, func in extraction_pipeline.items():
        df[col_name] = df['Cleaned Text'].progress_apply(func)

    # Generate AI Opinion based on the newly created columns
    df['AI Opinion'] = df.progress_apply(lambda row: generate_ai_opinion(row, row['Cleaned Text']), axis=1)

    # Drop the intermediate 'Cleaned Text' column before saving to the final output
    df.drop(columns=['Cleaned Text'], inplace=True)
    
    try:
        df.to_excel(OUTPUT_PATH, index=False)
        print(f"✅ File saved to: {OUTPUT_PATH}")
    except FileNotFoundError:
        print(f"Error: The specified output path '{OUTPUT_PATH}' does not exist.")
    except PermissionError:
        print(f"Error: Permission denied when trying to save to '{OUTPUT_PATH}'. Check file permissions.")
    except Exception as e:
        print(f"An unexpected error occurred while saving the file: {e}")

if __name__ == "__main__":
    main()