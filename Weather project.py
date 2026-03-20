# Boilerplate code
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import seaborn as sns


DEFAULT_CSV = "/mnt/data/pune.csv"   #
YEARS_RANGE = list(range(2008, 2023))
MONTH_NAMES = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]

# Globals
APP = {}
df = None


# Utility helpers

def try_parse_dates(df_in):
    df_loc = df_in.copy()
    # Try common date columns if 'date_time' missing
    date_candidates = [c for c in df_loc.columns if 'date' in c.lower()]
    if 'date_time' in df_loc.columns:
        date_col = 'date_time'
    elif date_candidates:
        date_col = date_candidates[0]
    else:
        raise ValueError("No date column found. Expect a 'date_time' column or similar.")
    df_loc[date_col] = pd.to_datetime(df_loc[date_col], errors='coerce')
    df_loc = df_loc.dropna(subset=[date_col]).reset_index(drop=True)
    df_loc['year'] = df_loc[date_col].dt.year
    df_loc['month'] = df_loc[date_col].dt.month
    df_loc['day'] = df_loc[date_col].dt.day
    # normalize column names for known fields
    return df_loc

def clear_display():
    for w in APP['display_frame'].winfo_children():
        w.destroy()

def embed_figure(fig, include_toolbar=True):
    """Embed a matplotlib Figure into the display area. Returns canvas."""
    clear_display()
    canvas = FigureCanvasTkAgg(fig, master=APP['display_frame'])
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.pack(fill='both', expand=True)
    if include_toolbar:
        toolbar = NavigationToolbar2Tk(canvas, APP['display_frame'])
        toolbar.update()
        toolbar.pack(side='bottom', fill='x')
    return canvas

def set_status(text):
    APP['status_var'].set(text)


# Button callbacks

def load_csv():
    global df
    path = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
    if not path:
        return
    try:
        tmp = pd.read_csv(path)
        tmp = try_parse_dates(tmp)
        df = tmp
        set_status(f"Loaded {os.path.basename(path)} ({len(df)} rows)")
    except Exception as e:
        messagebox.showerror("Load error", f"Could not load CSV:\n{e}")

def show_table():
    global df

    if df is None:
        if os.path.exists(DEFAULT_CSV):
            try:
                tmp = pd.read_csv(DEFAULT_CSV)
                tmp = try_parse_dates(tmp)
                df = tmp
                set_status(f"Auto-loaded {os.path.basename(DEFAULT_CSV)}")
            except Exception as e:
                messagebox.showerror("Load error", f"Could not load default CSV:\n{e}")
                return
        else:
            messagebox.showwarning("No data", "Load a CSV first (button 1).")
            return

    clear_display()
    frame = APP['display_frame']

    cols = list(df.columns)
    tree_frame = tk.Frame(frame)
    tree_frame.pack(fill='both', expand=True)

    tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=20)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=120, anchor='w')
    # limit display to first 1000 rows for responsiveness
    max_rows = 1000
    for r in df.head(max_rows).itertuples(index=False):
        tree.insert('', 'end', values=list(r))
    vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
    hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
    tree.configure(yscroll=vsb.set, xscroll=hsb.set)
    tree.grid(row=0, column=0, sticky='nsew')
    vsb.grid(row=0, column=1, sticky='ns')
    hsb.grid(row=1, column=0, sticky='ew')
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    note = ttk.Label(frame, text=f"Showing first {min(len(df), max_rows)} rows (dataset rows: {len(df)})",
                     font=('Segoe UI', 9))
    note.pack(fill='x', padx=6, pady=6)

def heatmap_monthly_years():
    global df
    if df is None:
        if os.path.exists(DEFAULT_CSV):
            try:
                tmp = pd.read_csv(DEFAULT_CSV)
                tmp = try_parse_dates(tmp)
                df = tmp
                set_status(f"Auto-loaded {os.path.basename(DEFAULT_CSV)}")
            except Exception as e:
                messagebox.showerror("Load error", f"Could not load default CSV:\n{e}")
                return
        else:
            messagebox.showwarning("No data", "Load a CSV first (button 1).")
            return

    # Pick temp column
    if "tempC" in df.columns:
        temp_col = "tempC"
        working = df
    elif set(["maxtempC", "mintempC"]).issubset(df.columns):
        working = df.copy()
        working["tempC"] = (
            working["maxtempC"].astype(float) + working["mintempC"].astype(float)
        ) / 2
        temp_col = "tempC"
    else:
        messagebox.showerror("Missing temp", "Missing temp column (tempC or max/min).")
        return

    # LIMIT YEARS → 2009–2022
    data = working[working["year"].isin(range(2009, 2023))]

    if data.empty:
        messagebox.showwarning("No data", "No data for years 2009–2022.")
        return

    # pivot: rows = months (1–12), columns = years
    pivot = (
        data.pivot_table(
            index="month", columns="year", values=temp_col, aggfunc="mean"
        )
        .reindex(index=range(1, 13), columns=range(2009, 2023))
    )

    clear_display()
    fig = Figure(figsize=(12, 6))
    ax = fig.add_subplot(111)

    sns.heatmap(
        pivot,
        ax=ax,
        cmap="coolwarm",
        annot=True,
        fmt=".1f",
        linewidths=0.4,
        linecolor="gray",
        cbar_kws={"label": "Temperature (°C)"},
        yticklabels=MONTH_NAMES
    )

    ax.set_xlabel("Year")
    ax.set_ylabel("Month")
    ax.set_title("Monthly Average Temperature (2009–2022)")

    embed_figure(fig)



def precip_scatter():

    global df
    if df is None:
        if os.path.exists(DEFAULT_CSV):
            try:
                tmp = pd.read_csv(DEFAULT_CSV)
                tmp = try_parse_dates(tmp)
                df = tmp
                set_status(f"Auto-loaded {os.path.basename(DEFAULT_CSV)}")
            except Exception as e:
                messagebox.showerror("Load error", f"Could not load default CSV:\n{e}")
                return
        else:
            messagebox.showwarning("No data", "Load a CSV first (button 1).")
            return

    if 'precipMM' not in df.columns:
        messagebox.showerror("Missing precip", "CSV lacks 'precipMM' column.")
        return

    # filter and jitter
    df_plot = df[['year','precipMM']].dropna()
    df_plot = df_plot[df_plot['year'].isin(YEARS_RANGE)]
    if df_plot.empty:
        messagebox.showwarning("No data", "No precipitation data in years 2008-2022.")
        return

    clear_display()
    fig = Figure(figsize=(10,5))
    ax = fig.add_subplot(111)
    jitter = np.random.normal(scale=0.12, size=len(df_plot))
    ax.scatter(df_plot['year'] + jitter, df_plot['precipMM'], alpha=0.6, s=18)
    ax.set_xticks(YEARS_RANGE)
    ax.set_xlim(min(YEARS_RANGE)-0.6, max(YEARS_RANGE)+0.6)
    ax.set_xlabel("Year")
    ax.set_ylabel("Precipitation (mm)")
    ax.set_title("Precipitation samples (2008 - 2022)")
    ax.grid(alpha=0.25)

    embed_figure(fig)

def wind_dotplot():

    global df
    if df is None:
        if os.path.exists(DEFAULT_CSV):
            try:
                tmp = pd.read_csv(DEFAULT_CSV)
                tmp = try_parse_dates(tmp)
                df = tmp
                set_status(f"Auto-loaded {os.path.basename(DEFAULT_CSV)}")
            except Exception as e:
                messagebox.showerror("Load error", f"Could not load default CSV:\n{e}")
                return
        else:
            messagebox.showwarning("No data", "Load a CSV first (button 1).")
            return

    # prefer windspeedKmph else try wind_kph / windspeed_kmph variants
    wind_cols = [c for c in df.columns if 'wind' in c.lower()]
    chosen = None
    for c in ['windspeedKmph','windspeed_kmph','wind_kmph','wind_kph','windSpeed']:
        if c in df.columns:
            chosen = c
            break
    if chosen is None:
        # pick first with 'wind'
        chosen = wind_cols[0] if wind_cols else None

    if chosen is None:
        messagebox.showerror("Missing wind", "No wind speed column found (expected names like 'windspeedKmph').")
        return

    yearly_wind = df.groupby('year')[chosen].mean().reindex(YEARS_RANGE)
    if yearly_wind.dropna().empty:
        messagebox.showwarning("No data", "No windspeed data for years 2008-2022.")
        return

    clear_display()
    fig = Figure(figsize=(10,5))
    ax = fig.add_subplot(111)
    # Dot plot: larger markers, colored
    colors = plt.cm.plasma(np.linspace(0,1,len(yearly_wind)))
    ax.scatter(yearly_wind.index, yearly_wind.values, s=160, c=colors, edgecolor='k', linewidth=0.6)
    for x,y in zip(yearly_wind.index, yearly_wind.values):
        if not np.isnan(y):
            ax.text(x, y + 0.05*max(yearly_wind.values), f"{y:.1f}", ha='center', fontsize=8)
    ax.set_xticks(YEARS_RANGE)
    ax.set_xlim(min(YEARS_RANGE)-0.6, max(YEARS_RANGE)+0.6)
    ax.set_xlabel("Year")
    ax.set_ylabel(f"Mean {chosen}")
    ax.set_title("Mean windspeed per year (dot plot)")
    ax.grid(alpha=0.25)

    embed_figure(fig)

def avg_temp_bar():

    global df
    if df is None:
        if os.path.exists(DEFAULT_CSV):
            try:
                tmp = pd.read_csv(DEFAULT_CSV)
                tmp = try_parse_dates(tmp)
                df = tmp
                set_status(f"Auto-loaded {os.path.basename(DEFAULT_CSV)}")
            except Exception as e:
                messagebox.showerror("Load error", f"Could not load default CSV:\n{e}")
                return
        else:
            messagebox.showwarning("No data", "Load a CSV first (button 1).")
            return

    # pick temperature column
    if 'tempC' in df.columns:
        temp_col = 'tempC'
        working = df
    elif set(['maxtempC','mintempC']).issubset(df.columns):
        working = df.copy()
        working['tempC'] = (working['maxtempC'].astype(float) + working['mintempC'].astype(float)) / 2
        temp_col = 'tempC'
    else:
        messagebox.showerror("Missing temp", "No 'tempC' or 'maxtempC/mintempC' columns found.")
        return

    yearly_avg = working.groupby('year')[temp_col].mean().reindex(YEARS_RANGE)
    if yearly_avg.dropna().empty:
        messagebox.showwarning("No data", "No temperature data found for years 2008-2022.")
        return

    clear_display()
    fig = Figure(figsize=(11,5))
    ax = fig.add_subplot(111)
    cmap = plt.cm.viridis
    colors = cmap(np.linspace(0,1,len(yearly_avg)))
    bars = ax.bar(yearly_avg.index, yearly_avg.values, color=colors, edgecolor='k')
    ax.set_xticks(YEARS_RANGE)
    ax.set_xlim(min(YEARS_RANGE)-0.6, max(YEARS_RANGE)+0.6)
    ax.set_xlabel("Year")
    ax.set_ylabel("Average Temperature (°C)")
    ax.set_title("Average annual temperature (2008 - 2022)")
    ax.grid(axis='y', alpha=0.2)
    for x,y in zip(yearly_avg.index, yearly_avg.values):
        if not np.isnan(y):
            ax.text(x, y + 0.08*max(yearly_avg.values), f"{y:.1f}", ha='center', fontsize=8)

    embed_figure(fig)


def build_gui(root):
    root.title("Weather History Visualizer")
    root.geometry("1200x720")
    # some nicer style
    style = ttk.Style()
    # prefer a modern theme if available
    try:
        style.theme_use('clam')
    except Exception:
        pass
    style.configure('TButton', font=('Segoe UI', 10), padding=8)
    style.configure('TLabel', font=('Segoe UI', 10))
    style.configure('TCombobox', font=('Segoe UI', 10))
    style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))

    # left control frame
    ctrl = tk.Frame(root, bg='#f2f4f7', width=300)
    ctrl.pack(side='left', fill='y', padx=(8,4), pady=8)
    ctrl.pack_propagate(False)

    title = ttk.Label(ctrl, text="Controls", font=('Segoe UI', 12, 'bold'))
    title.pack(pady=(12,8))

    btns = [
        ("1) Load CSV", load_csv),
        ("2) Show Table", show_table),
        ("3) Monthly Heatmap (2009–2022)", heatmap_monthly_years),
        ("4) Precipitation (scatter)", precip_scatter),
        ("5) Windspeed (dot plot)", wind_dotplot),
        ("6) Avg Temp per Year (bar)", avg_temp_bar),
    ]
    for txt, cmd in btns:
        b = ttk.Button(ctrl, text=txt, command=cmd)
        b.pack(fill='x', padx=18, pady=8)

    # status
    status_var = tk.StringVar(value="No dataset loaded.")
    status = ttk.Label(ctrl, textvariable=status_var, relief='flat', anchor='w', wraplength=260)
    status.pack(side='bottom', fill='x', padx=8, pady=10)

    # display frame
    display = tk.Frame(root, bg='white', relief='sunken', bd=1)
    display.pack(side='right', fill='both', expand=True, padx=(4,8), pady=8)

    APP.update({
        'root': root,
        'ctrl_frame': ctrl,
        'display_frame': display,
        'status_var': status_var
    })

    # auto-load default dataset silently if available
    if os.path.exists(DEFAULT_CSV):
        try:
            tmp = pd.read_csv(DEFAULT_CSV)
            tmp = try_parse_dates(tmp)
            global df
            df = tmp
            status_var.set(f"Auto-loaded {os.path.basename(DEFAULT_CSV)} ({len(df)} rows)")
        except Exception:
            pass


# Run

if __name__ == "__main__":
    root = tk.Tk()
    build_gui(root)
    root.mainloop()