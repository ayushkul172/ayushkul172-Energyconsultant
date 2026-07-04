# Import necessary libraries
import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QLabel, QComboBox,
    QSplitter, QTextEdit, QHBoxLayout, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Import advanced data science libraries
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

# A custom class for the Matplotlib canvas widget
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Create a figure and axes for the plot
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        # Set the figure background color to a dark gray
        self.fig.patch.set_facecolor('#282c34')
        # Set the axes background and text colors to a dark gray and white
        self.axes.set_facecolor('#2c303a')
        self.axes.tick_params(colors='white')
        self.axes.title.set_color('white')
        self.axes.xaxis.label.set_color('white')
        self.axes.yaxis.label.set_color('white')
        super(MplCanvas, self).__init__(self.fig)

# The main application window class
class DataExplorerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sophisticated Data Explorer Dashboard")
        self.setGeometry(100, 100, 1200, 800)

        # Apply a dark theme using Qt Style Sheets (QSS)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1c1e22;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3e4452;
                border: 1px solid #5a6270;
                color: #ffffff;
                padding: 10px;
                font-size: 14px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #4a5160;
            }
            QComboBox {
                background-color: #2c303a;
                border: 1px solid #5a6270;
                color: #ffffff;
                padding: 5px;
                border-radius: 5px;
            }
            QTableWidget {
                background-color: #2c303a;
                color: #ffffff;
                gridline-color: #4a5160;
                border: 1px solid #4a5160;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #555c6d;
            }
            QHeaderView::section {
                background-color: #3e4452;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #4a5160;
            }
            QLabel, QTextEdit {
                color: #ffffff;
                font-size: 14px;
            }
            QTextEdit {
                background-color: #2c303a;
                border: 1px solid #4a5160;
                border-radius: 5px;
                padding: 10px;
            }
        """)

        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # Top section with file upload and sheet selection
        self.top_section = QWidget()
        self.top_layout = QVBoxLayout(self.top_section)
        
        self.file_button = QPushButton("Upload Excel File")
        self.file_button.clicked.connect(self.open_file_dialog)
        self.top_layout.addWidget(self.file_button)

        self.sheet_combo = QComboBox()
        self.sheet_combo.currentIndexChanged.connect(self.load_sheet_data)
        self.sheet_combo.setEnabled(False)  # Disabled until a file is loaded
        self.top_layout.addWidget(self.sheet_combo)

        # Add new controls for advanced features
        self.advanced_controls = QWidget()
        self.advanced_layout = QHBoxLayout(self.advanced_controls)
        
        # Data Cleaning button
        self.clean_button = QPushButton("Clean Data")
        self.clean_button.clicked.connect(self.clean_data)
        self.advanced_layout.addWidget(self.clean_button)
        
        # Predictive Modeling controls
        self.target_label = QLabel("Target Column:")
        self.target_combo = QComboBox()
        self.build_model_button = QPushButton("Build Model")
        self.build_model_button.clicked.connect(self.build_model)
        
        self.advanced_layout.addWidget(self.target_label)
        self.advanced_layout.addWidget(self.target_combo)
        self.advanced_layout.addWidget(self.build_model_button)

        # New buttons for row and column management
        self.highlight_button = QPushButton("Highlight Row")
        self.highlight_button.clicked.connect(self.highlight_row)
        self.advanced_layout.addWidget(self.highlight_button)

        self.add_note_button = QPushButton("Add Note to Row")
        self.add_note_button.clicked.connect(self.add_row_note)
        self.advanced_layout.addWidget(self.add_note_button)

        self.add_column_button = QPushButton("Add Column")
        self.add_column_button.clicked.connect(self.add_column)
        self.advanced_layout.addWidget(self.add_column_button)

        self.delete_column_button = QPushButton("Delete Column")
        self.delete_column_button.clicked.connect(self.delete_column)
        self.advanced_layout.addWidget(self.delete_column_button)

        self.top_layout.addWidget(self.advanced_controls)

        # Splitter to divide the window into a table view and analysis view
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left side for data table
        self.table_widget = QTableWidget()
        self.splitter.addWidget(self.table_widget)

        # Right side for plot and analysis
        self.analysis_widget = QWidget()
        self.analysis_layout = QVBoxLayout(self.analysis_widget)

        # Matplotlib canvas for the plot
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.analysis_layout.addWidget(self.canvas)
        
        # Text edit for advice and suggestions
        self.advice_label = QLabel("Data Insights and Advice")
        self.advice_text = QTextEdit()
        self.advice_text.setReadOnly(True)
        self.analysis_layout.addWidget(self.advice_label)
        self.analysis_layout.addWidget(self.advice_text)

        self.splitter.addWidget(self.analysis_widget)

        # Set initial sizes for the splitter panes
        self.splitter.setSizes([self.width() // 2, self.width() // 2])

        self.main_layout.addWidget(self.top_section)
        self.main_layout.addWidget(self.splitter)

        # Member variables to store data
        self.excel_file = None
        self.df_dict = {}
        self.current_df = None
        # Store highlighted rows and notes
        self.highlighted_rows = set()
        self.row_notes = {}
        self.note_column_name = "Note"

    def open_file_dialog(self):
        """
        Opens a file dialog to select an Excel file and loads its sheets.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select an Excel File",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.excel_file = file_path
            self.load_excel_sheets()

    def load_excel_sheets(self):
        """
        Reads the Excel file and gets the names of all its sheets.
        """
        try:
            self.df_dict = pd.read_excel(self.excel_file, sheet_name=None)
            sheet_names = list(self.df_dict.keys())
            
            self.sheet_combo.clear()
            self.sheet_combo.addItems(sheet_names)
            self.sheet_combo.setEnabled(True)
            self.advice_text.setText(f"File '{self.excel_file.split('/')[-1]}' loaded successfully. Please select a sheet to explore.")
            self.load_sheet_data()
        except Exception as e:
            QMessageBox.critical(self, "Error Loading File", f"An error occurred while loading the file: {e}")
            self.advice_text.setText(f"Error: Could not load file. {e}")
            self.sheet_combo.setEnabled(False)

    def load_sheet_data(self):
        """
        Loads the data for the currently selected sheet and displays it.
        """
        sheet_name = self.sheet_combo.currentText()
        if not sheet_name:
            self.current_df = None
            return

        self.current_df = self.df_dict.get(sheet_name).copy()
        if self.current_df is None:
            return

        # Reset state for a new sheet
        self.highlighted_rows.clear()
        self.row_notes.clear()

        # Check if a 'Note' column already exists in the data and if not, add it
        if self.note_column_name not in self.current_df.columns:
            self.current_df[self.note_column_name] = ""
        
        # Populate the target column combo box
        self.target_combo.clear()
        self.target_combo.addItems(self.current_df.columns.tolist())

        # Display data in the QTableWidget
        self.display_dataframe_in_table(self.current_df)

        # Generate a simple plot
        self.generate_plot(self.current_df)

        # Provide data insights and advice
        self.provide_advice(self.current_df)

    def display_dataframe_in_table(self, df):
        """
        Populates the QTableWidget with the data from a pandas DataFrame.
        Includes styling for highlighted rows and notes.
        """
        self.table_widget.clear()
        # Handle case of empty dataframe
        if df.empty:
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            self.advice_text.append("\n**Warning:** The selected sheet is empty.")
            return

        self.table_widget.setRowCount(df.shape[0])
        self.table_widget.setColumnCount(df.shape[1])
        self.table_widget.setHorizontalHeaderLabels(df.columns.astype(str))
        
        for row_idx in range(df.shape[0]):
            for col_idx in range(df.shape[1]):
                value = str(df.iloc[row_idx, col_idx])
                item = QTableWidgetItem(value)
                # Check for and display notes
                if df.columns[col_idx] == self.note_column_name:
                    item.setToolTip(self.row_notes.get(row_idx, ""))

                self.table_widget.setItem(row_idx, col_idx, item)

            # Apply highlighting if the row is in the highlighted_rows set
            if row_idx in self.highlighted_rows:
                for col_idx in range(df.shape[1]):
                    item = self.table_widget.item(row_idx, col_idx)
                    if item:
                        item.setBackground(QColor("#5d5c61"))  # A subtle gray highlight

    def generate_plot(self, df):
        """
        Generates a plot based on the DataFrame data, using logic from the provided example.
        """
        self.canvas.axes.cla() # Clear the old plot
        self.canvas.fig.tight_layout() # Adjust layout to prevent labels from overlapping
        
        # Find the first two numeric columns for a scatter plot
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            # Drop rows with NaN values for plotting to prevent errors
            plot_df = df[[x_col, y_col]].dropna()
            
            if not plot_df.empty:
                self.canvas.axes.scatter(plot_df[x_col], plot_df[y_col], alpha=0.7, color='#8fbcbb')
                self.canvas.axes.set_title(f'Scatter Plot of {x_col} vs {y_col}')
                self.canvas.axes.set_xlabel(x_col)
                self.canvas.axes.set_ylabel(y_col)
            else:
                self.canvas.axes.text(
                    0.5, 0.5, "No valid data to plot.",
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.canvas.axes.transAxes, color='white'
                )
                self.canvas.axes.set_title("Plot Unavailable")

        elif len(numeric_cols) == 1:
            # If only one numeric column, plot a histogram
            x_col = numeric_cols[0]
            # Drop NaN values for plotting
            plot_data = df[x_col].dropna()
            
            if not plot_data.empty:
                self.canvas.axes.hist(plot_data, bins=20, color='#8fbcbb', edgecolor='white')
                self.canvas.axes.set_title(f'Histogram of {x_col}')
                self.canvas.axes.set_xlabel(x_col)
                self.canvas.axes.set_ylabel('Frequency')
            else:
                self.canvas.axes.text(
                    0.5, 0.5, "No valid data to plot.",
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.canvas.axes.transAxes, color='white'
                )
                self.canvas.axes.set_title("Plot Unavailable")

        else:
            self.canvas.axes.text(
                0.5, 0.5, "No numeric data to plot.",
                horizontalalignment='center', verticalalignment='center',
                transform=self.canvas.axes.transAxes, color='white'
            )
            self.canvas.axes.set_title("Plot Unavailable")
        
        self.canvas.draw()

    def provide_advice(self, df):
        """
        Analyzes the DataFrame and provides basic insights and advice.
        """
        if df.empty:
            self.advice_text.setText("The selected sheet is empty. No insights available.")
            return

        num_rows, num_cols = df.shape
        advice_text = f"Data insights for sheet '{self.sheet_combo.currentText()}':\n"
        advice_text += f"--------------------------------------------------\n"
        advice_text += f"• The dataset contains {num_rows} rows and {num_cols} columns.\n"
        
        # Check for missing values
        missing_count = df.isnull().sum().sum()
        if missing_count > 0:
            advice_text += f"• **Warning:** There are {missing_count} missing values in the dataset. You may need to clean or impute this data.\n"
        else:
            advice_text += "• **Good News!** There are no missing values in this dataset.\n"
            
        # Analyze data types
        advice_text += f"\nColumn data types and unique values:\n"
        for col in df.columns:
            dtype = df[col].dtype
            unique_count = df[col].nunique()
            advice_text += f"• **'{col}'**: dtype is '{dtype}', has {unique_count} unique values.\n"
            
        self.advice_text.setText(advice_text)

    # --- New Methods for Advanced Functionality ---
    
    def clean_data(self):
        """
        Handles missing values and standardizes numerical columns using the provided logic.
        """
        if self.current_df is None or self.current_df.empty:
            QMessageBox.warning(self, "Warning", "Please upload and select a sheet with data first.")
            return

        try:
            # Separate numeric and non-numeric columns
            numeric_cols = self.current_df.select_dtypes(include=np.number).columns
            if numeric_cols.empty:
                QMessageBox.warning(self, "Warning", "No numeric columns to clean.")
                return

            non_numeric_df = self.current_df.drop(columns=numeric_cols)
            numeric_df = self.current_df[numeric_cols]
            
            # Handle missing values using KNN imputer
            imputer = KNNImputer(n_neighbors=5)
            df_imputed = pd.DataFrame(imputer.fit_transform(numeric_df), columns=numeric_cols)
            
            # Standardize numerical columns
            scaler = StandardScaler()
            df_scaled = pd.DataFrame(scaler.fit_transform(df_imputed), columns=numeric_cols)
            
            # Re-combine the dataframes
            # Note: The index will be reset.
            self.current_df = pd.concat([df_scaled, non_numeric_df.reset_index(drop=True)], axis=1)
            
            # Update the UI
            self.display_dataframe_in_table(self.current_df)
            self.generate_plot(self.current_df)
            self.provide_advice(self.current_df)
            self.advice_text.append("\n**Data has been cleaned (imputed and standardized).**")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during data cleaning: {e}")
            self.advice_text.append(f"\n**Error during data cleaning:**\n{e}")

    def build_model(self):
        """
        Builds a linear regression model using the provided logic.
        """
        if self.current_df is None or self.current_df.empty:
            QMessageBox.warning(self, "Warning", "Please upload and select a sheet with data first.")
            return

        target_col = self.target_combo.currentText()
        if not target_col or target_col not in self.current_df.columns:
            QMessageBox.warning(self, "Warning", "Please select a valid target column.")
            return
            
        if self.current_df[target_col].dtype not in [np.number]:
            QMessageBox.warning(self, "Warning", "The target column must be numeric.")
            return

        try:
            X = self.current_df.drop(columns=[target_col])
            y = self.current_df[target_col]
            
            # Drop non-numeric columns from X before modeling
            X = X.select_dtypes(include=np.number)
            
            # Check for any missing values after dropping columns and impute if necessary
            if X.isnull().sum().sum() > 0:
                imputer = KNNImputer(n_neighbors=5)
                X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            model = LinearRegression()
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            
            self.advice_text.append(f"\n**Predictive Model Results (Linear Regression):**")
            self.advice_text.append(f"• Target Column: '{target_col}'")
            self.advice_text.append(f"• Mean Squared Error (MSE): {mse:.2f}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during model building: {e}")
            self.advice_text.append(f"\n**Error during model building:**\n{e}")

    def highlight_row(self):
        """
        Highlights the selected row in the table.
        """
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a row to highlight.")
            return
        
        row_index = selected_rows[0].row()
        if row_index in self.highlighted_rows:
            self.highlighted_rows.remove(row_index)
        else:
            self.highlighted_rows.add(row_index)
        
        # Redraw the table to apply the highlight/unhighlight
        self.display_dataframe_in_table(self.current_df)

    def add_row_note(self):
        """
        Adds a note to the selected row, which appears as a tooltip on the 'Note' column.
        """
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a row to add a note to.")
            return
        
        row_index = selected_rows[0].row()
        current_note = self.row_notes.get(row_index, "")
        
        text, ok = QInputDialog.getText(self, "Add/Edit Note", f"Enter a note for row {row_index}:", text=current_note)
        
        if ok:
            self.row_notes[row_index] = text
            # Ensure the note column exists and update it
            if self.note_column_name not in self.current_df.columns:
                 self.current_df[self.note_column_name] = ""
            self.current_df.at[row_index, self.note_column_name] = text
            self.display_dataframe_in_table(self.current_df)
            self.advice_text.append(f"\n**Note added to row {row_index}.**")

    def add_column(self):
        """
        Adds a new, empty column to the DataFrame and updates the table.
        """
        if self.current_df is None:
            QMessageBox.warning(self, "Warning", "Please upload and select a sheet first.")
            return

        column_name, ok = QInputDialog.getText(self, "Add Column", "Enter new column name:")
        if ok and column_name:
            if column_name in self.current_df.columns:
                QMessageBox.warning(self, "Warning", f"A column with the name '{column_name}' already exists.")
            else:
                self.current_df[column_name] = ""
                self.display_dataframe_in_table(self.current_df)
                self.advice_text.append(f"\n**New column '{column_name}' added.**")

    def delete_column(self):
        """
        Deletes the currently selected column from the DataFrame.
        """
        selected_cols = self.table_widget.selectionModel().selectedColumns()
        if not selected_cols:
            QMessageBox.warning(self, "Warning", "Please select a column to delete.")
            return

        col_index = selected_cols[0].column()
        column_name = self.current_df.columns[col_index]

        if column_name == self.note_column_name:
            QMessageBox.warning(self, "Warning", "The 'Note' column cannot be deleted.")
            return

        try:
            self.current_df.drop(columns=[column_name], inplace=True)
            self.display_dataframe_in_table(self.current_df)
            self.advice_text.append(f"\n**Column '{column_name}' deleted.**")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while deleting the column: {e}")
            self.advice_text.append(f"\n**Error deleting column:**\n{e}")

# Main application entry point
if __name__ == "__main__":
    # It is critical to set these attributes before creating the QApplication instance.
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    
    window = DataExplorerApp()
    window.show()
    sys.exit(app.exec_())
