import pandas as pd
from tkinter import Tk, filedialog, Toplevel, Label, OptionMenu, StringVar, Button, messagebox
import sys
import traceback

# --- GUI and File Handling Functions ---

def select_file(root):
    """Open file dialog to select the source Excel file."""
    file_path = filedialog.askopenfilename(parent=root,
                                           title="Select the Source Excel File",
                                           filetypes=[("Excel Files", "*.xlsx;*.xls")])
    if not file_path:
        return None
    return file_path

def load_data(file_path):
    """Load data from Excel, handling both .xls and .xlsx."""
    print(f"\n--- Attempting to load file: {file_path} ---")
    try:
        df = pd.read_excel(file_path, engine=None)
        print("--- File loaded successfully into DataFrame! ---")
        return df
    except Exception as e:
        error_type = type(e).__name__
        error_details = traceback.format_exc()
        print("!!!!!!!!!!!!!!!!!! ERROR LOADING FILE !!!!!!!!!!!!!!!!!!", file=sys.stderr)
        print(error_details, file=sys.stderr)
        messagebox.showerror("CRITICAL: Could Not Read File", f"Failed to read Excel file.\n\nError Type: {error_type}")
        return None

def column_mapping_dialog(df, target_columns, root):
    """Create a dialog for the user to map source columns to target columns."""
    print("--- Creating the Column Mapping dialog... ---")
    dialog = Toplevel(root)
    dialog.title("Column Mapping")
    dialog.attributes('-topmost', True)

    dropdown_vars = {}
    for i, target_col in enumerate(target_columns):
        Label(dialog, text=f"Map '{target_col}' to:").grid(row=i, column=0, padx=10, pady=5, sticky="e")
        var = StringVar(dialog)
        matching_cols = [col for col in df.columns if col.lower() == target_col.lower()]
        var.set(matching_cols[0] if matching_cols else "Not Mapped")
        options = ["Not Mapped"] + list(df.columns)
        dropdown = OptionMenu(dialog, var, *options)
        dropdown.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
        dropdown_vars[target_col] = var

    final_mapping = {}
    def on_ok():
        for target, var in dropdown_vars.items():
            selected_source_col = var.get()
            if selected_source_col != "Not Mapped":
                final_mapping[target] = selected_source_col
        dialog.destroy()

    ok_button = Button(dialog, text="OK", command=on_ok)
    ok_button.grid(row=len(target_columns), column=0, columnspan=2, pady=15)
    
    dialog.transient(root)
    dialog.grab_set()
    root.wait_window(dialog)
    
    print("--- Column Mapping dialog has been closed. ---")

    if not final_mapping:
        messagebox.showwarning("Cancelled", "Column mapping was cancelled or no columns were mapped.")
        return None
    return final_mapping

# --- Data Processing and Saving Functions ---

def filter_and_map_data(df, column_mapping, target_columns):
    if 'DA Comment / Action' not in column_mapping:
        messagebox.showerror("Mapping Error", "The 'DA Comment / Action' column must be mapped.")
        return None
    filter_col = column_mapping['DA Comment / Action']
    filtered_df = df[df[filter_col].notna() & (df[filter_col].astype(str).str.strip() != '')].copy()
    if filtered_df.empty:
        return pd.DataFrame(columns=target_columns)

    rename_mapping = {v: k for k, v in column_mapping.items()}
    source_cols_to_keep = list(column_mapping.values())
    mapped_data = filtered_df[source_cols_to_keep]
    mapped_data = mapped_data.rename(columns=rename_mapping)

    # --- Sort data by date from oldest to latest before returning ---
    date_col_name = 'Date (DD/MM/YYYY)'
    if date_col_name in mapped_data.columns and not mapped_data[date_col_name].isnull().all():
        print(f"--- Sorting new data by '{date_col_name}' (oldest to latest)... ---")

        # Convert to datetime for proper sorting, assuming DD/MM/YYYY format
        mapped_data[date_col_name] = pd.to_datetime(
            mapped_data[date_col_name], dayfirst=True, errors='coerce'
        )

        # Sort the DataFrame by the date column. Unparseable dates go to the end.
        mapped_data = mapped_data.sort_values(by=date_col_name, ascending=True, na_position='last').reset_index(drop=True)

        # Format the date back to a string to ensure consistent formatting in Excel
        valid_dates_mask = mapped_data[date_col_name].notna()
        mapped_data.loc[valid_dates_mask, date_col_name] = mapped_data.loc[valid_dates_mask, date_col_name].dt.strftime('%d/%m/%Y')
        print("--- Sorting complete. ---")

    mapped_data = mapped_data.reindex(columns=target_columns)
    return mapped_data

def save_to_tracker(mapped_data, tracker_file_path):
    try:
        tracker_df = pd.read_excel(tracker_file_path, engine='openpyxl')
    except FileNotFoundError:
        tracker_df = pd.DataFrame(columns=mapped_data.columns)
    updated_tracker_df = pd.concat([tracker_df, mapped_data], ignore_index=True)
    with pd.ExcelWriter(tracker_file_path, mode='w', engine='openpyxl') as writer:
        updated_tracker_df.to_excel(writer, index=False, sheet_name='Sheet1')  # Specify sheet_name if needed
    messagebox.showinfo("Success", f"{len(mapped_data)} row(s) successfully added to the tracker.")

# --- Main Application Logic ---

def run_processing_logic(root):
    tracker_file_path = r'C:\Office work\Upstream SCRAP news\Tracker\USC News Tracker.xlsx'
    target_columns = [
        'Date (DD/MM/YYYY)', 'Link', 'Article Title', 'Priority', 'Contractor',
        'Field / Project', 'Country', 'DA Comment / Action'
    ]
    source_file_path = select_file(root)
    if not source_file_path:
        root.destroy()
        return
    df = load_data(source_file_path)
    if df is None:
        root.destroy()
        return
    column_mapping = column_mapping_dialog(df, target_columns, root)
    if not column_mapping:
        root.destroy()
        return
    mapped_data = filter_and_map_data(df, column_mapping, target_columns)
    if mapped_data is None:
        root.destroy()
        return
    if mapped_data.empty:
        messagebox.showinfo("No Data Found", "No rows with comments were found. Nothing to add.")
        root.destroy()
        return
    save_to_tracker(mapped_data, tracker_file_path)
    root.destroy()

def main():
    """Sets up the Tkinter root and starts the application."""
    root = Tk()
    
    # --- THIS IS THE FIX ---
    # Instead of root.withdraw(), we make a tiny window and move it off-screen.
    # This keeps the root window "active" enough for the dialog to appear.
    root.geometry("0x0-100-100") 
    root.title("Filling Tracker Backend") # Optional: give it a name in case it flashes

    root.after(50, lambda: run_processing_logic(root))
    root.mainloop()

if __name__ == "__main__":
    main()