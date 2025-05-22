# app.py - Enhanced Hydro Monitoring Dashboard (Final Version)

import streamlit as st
from db import fetch_data
from constraints import check_constraints
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import re

# --------------------------- PAGE CONFIG ---------------------------
st.set_page_config(
    page_title="HydroVision Pro",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------- CUSTOM CSS ---------------------------
st.markdown("""
    <style>
        /* Main styles */
        .main {
            background-color: #f8f9fa;
        }
        
        /* Metric cards */
        .metric-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-3px);
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);
            color: white;
        }
        
        /* Tabs styling */
        .stTabs [role="tablist"] {
            gap: 10px;
            padding: 10px 0;
        }
        .stTabs [role="tab"] {
            border-radius: 8px !important;
            padding: 12px 24px !important;
            transition: all 0.3s ease;
            background: #f0f2f6 !important;
        }
        .stTabs [role="tab"][aria-selected="true"] {
            background: #3498db !important;
            color: white !important;
        }
        
        /* Console styling */
        .console {
            background-color: #1e1e1e;
            color: #00ff00;
            padding: 15px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            min-height: 200px;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #3d3d3d;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------------- DATA SOURCES ---------------------------
data_sources = {
    "River": "river_data",
    "Dam": "dam_data",
    "EPAN": "epan_data",
    "AWS": "aws_data",
    "ARS": "ars_data",
    "Gate": "gate_data"
}

# --------------------------- SIDEBAR ---------------------------
with st.sidebar:
    st.image("logo.png", use_container_width=True)
    st.markdown("---")
    st.subheader("🚀 Quick Status")
    st.markdown("Last Updated:")
    st.caption(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# --------------------------- DATA LOADING ---------------------------
@st.cache_data(ttl=300)
def load_all_data():
    all_data = {}
    for name, table in data_sources.items():
        try:
            df = fetch_data(table)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            all_data[name] = df
        except Exception as e:
            st.error(f"Error loading {name} data: {e}")
            all_data[name] = pd.DataFrame()
    return all_data

all_data = load_all_data()

# --------------------------- MAIN INTERFACE ---------------------------
st.title("Mechatronics Pro Dashboard")

# --------------------------- TOP METRICS ---------------------------
metric_cols = st.columns(3)
with metric_cols[0]:
    st.markdown("""
        <div class="metric-card">
            <h3 style='color: #2c3e50; margin:0'>🌍 Active Stations</h3>
            <p style='font-size: 32px; margin:0'>{0}/6</p>
            <div style='height: 4px; background: #ecf0f1; border-radius: 2px; margin: 10px 0'>
                <div style='width: 100%; height: 100%; background: #2ecc71; border-radius: 2px'></div>
            </div>
        </div>
    """.format(len(all_data)), unsafe_allow_html=True)

with metric_cols[1]:
    total_records = sum(len(df) for df in all_data.values())
    st.markdown(f"""
        <div class="metric-card">
            <h3 style='color: #2c3e50; margin:0'>📊 Total Data Entries</h3>
            <p style='font-size: 32px; margin:0'>{total_records:,}</p>
            <div style='color: #95a5a6; font-size: 12px'>+12% from last week</div>
        </div>
    """, unsafe_allow_html=True)

# --------------------------- MAIN TABS ---------------------------
# --------------------------- MAIN TABS ---------------------------
tab_overview, tab_stations, tab_history, tab_custom, tab_graphs = st.tabs(
    ["🌐 Overview", "📡 Station Dashboards", "📜 Historical Analysis", "🔍 Custom Selection", "📈 Graphs"]
)

# --------------------------- OVERVIEW TAB ---------------------------
with tab_overview:
    st.subheader("Raw Data Explorer")
    selected_station = st.selectbox("Select Station", list(data_sources.keys()))
    if not all_data[selected_station].empty:
        st.dataframe(all_data[selected_station], use_container_width=True)
    else:
        st.warning(f"No data available for {selected_station}")

    
   
# --------------------------- STATION DASHBOARDS TAB ---------------------------
with tab_stations:
    # First show date selection at the top
    selected_date = st.date_input(
        "Select Date", 
        value=datetime.now().date(),
        key="station_date_selector"
    )
    selected_date_str = selected_date.strftime("%Y-%m-%d")
    
    # Then show station tabs
    station_tabs = st.tabs(list(data_sources.keys()))
    
    for idx, (station_name, table_name) in enumerate(data_sources.items()):
        with station_tabs[idx]:
            df = all_data[station_name]
            
            if not df.empty:
                st.subheader(f"{station_name} Station")
                
                # Project Filter (only show if we have data)
                if 'project_name' in df.columns:
                    projects = df['project_name'].unique()
                    selected_project = st.selectbox(
                        "Select Project",
                        options=["All Projects"] + list(projects),
                        key=f"proj_{station_name}_{idx}"
                    )
                
                # Filter data for selected date
                if 'data_date' in df.columns:
                    daily_df = df[df['data_date'].astype(str) == selected_date_str]
                    if selected_project != "All Projects":
                        daily_df = daily_df[daily_df['project_name'] == selected_project]
                else:
                    daily_df = pd.DataFrame()
                
                # Only proceed if we have data for the selected date
                if not daily_df.empty:
                    # Data Display
                    st.markdown("### 📋 Current Readings")
                    
                    # Initialize alerts for this station and date
                    alert_rows = []
                    
                    # Custom Highlighting Function for all station types
                    def highlight_alerts(row):
                        styles = [''] * len(row)
                        alert_detected = False
                        
                        # Common checks for all stations
                        if 'batt_volt' in row and pd.notnull(row['batt_volt']):
                            try:
                                if float(row['batt_volt']) < 10.5:
                                    styles = ['background-color: #ffcccc'] * len(row)
                                    alert_detected = True
                            except:
                                pass
                        
                        # Station-specific checks
                        if station_name == 'Gate':
                            gate_cols = [col for col in daily_df.columns if re.match(r'^g\d+$', col)]
                            for col in gate_cols:
                                if col in row and pd.notnull(row[col]):
                                    try:
                                        if float(row[col]) > 0.00:
                                            styles = ['background-color: #ffcccc'] * len(row)
                                            alert_detected = True
                                            break
                                    except:
                                        continue
                        
                        elif station_name == 'EPAN' and 'epan_water_depth' in row:
                            try:
                                if float(row['epan_water_depth']) < 15:
                                    styles = ['background-color: #ffcccc'] * len(row)
                                    alert_detected = True
                            except:
                                pass
                        
                        elif station_name == 'AWS':
                            # AWS-specific alert conditions
                            if 'rainfall' in row and pd.notnull(row['rainfall']):
                                try:
                                    if float(row['rainfall']) > 50:  # Rainfall threshold in mm
                                        styles = ['background-color: #ffcccc'] * len(row)
                                        alert_detected = True
                                except:
                                    pass
                            
                            if 'wind_speed' in row and pd.notnull(row['wind_speed']):
                                try:
                                    if float(row['wind_speed']) > 30:  # Wind speed threshold in km/h
                                        styles = ['background-color: #ffcccc'] * len(row)
                                        alert_detected = True
                                except:
                                    pass
                            
                            if 'temperature' in row and pd.notnull(row['temperature']):
                                try:
                                    if float(row['temperature']) > 40:  # Temperature threshold in °C
                                        styles = ['background-color: #ffcccc'] * len(row)
                                        alert_detected = True
                                except:
                                    pass
                        
                        if alert_detected:
                            alert_rows.append(row)
                        
                        return styles
                    
                    # Apply highlighting
                    styled_df = daily_df.style.apply(highlight_alerts, axis=1)
                    st.dataframe(
                        styled_df,
                        use_container_width=True,
                        height=min(400, len(daily_df) * 35 + 50)
                    )
                    
                    # Show alerts for this specific date and station
                    if alert_rows:
                        st.markdown("---")
                        st.subheader(f"⚠ Alerts for {selected_date_str}")
                        
                        # Create columns for alert count and details
                        col1, col2 = st.columns([1, 3])
                        
                        
                        st.metric(
                            label="Total Alerts",
                            value=len(alert_rows),
                            help=f"Number of alert records found for {station_name} on {selected_date_str}"
                        )
                        
                       
                        alert_df = pd.DataFrame(alert_rows)
                        st.dataframe(
                            alert_df.style.apply(
                                lambda x: ['background-color: #ffebee']*len(x), 
                                axis=1
                            ),
                            use_container_width=True,
                            height=min(400, len(alert_rows) * 35 + 50)
                        )
                    else:
                        st.success(f"✅ No alerts detected for {selected_date_str}")
                    
                else:
                    st.warning(f"No data available for {selected_date_str}")
            else:
                st.warning(f"No data available for {station_name} station")

# --------------------------- HISTORICAL ANALYSIS TAB ---------------------------
# --------------------------- HISTORICAL ANALYSIS TAB ---------------------------
with tab_history:
    st.subheader("Historical Data Explorer")
    
    # Date Range Selector
    cols = st.columns(3)
    with cols[0]:
        station = st.selectbox("Select Station", list(data_sources.keys()), key="hist_station")
    with cols[1]:
        param = st.selectbox("Select Parameter", ["All Parameters"] + list(
            all_data[station].select_dtypes(include='number').columns.tolist()
        ), key="hist_param")
    
    # Date inputs in historical tab
    hist_start = st.date_input("Start Date", value=datetime.now() - timedelta(days=7), key="hist_start")
    hist_end = st.date_input("End Date", value=datetime.now(), key="hist_end")
    
    # Data Query
    if st.button("Load Historical Data", key="hist_load"):
        with st.spinner("Loading data..."):
            try:
                hist_df = fetch_data(
                    table_name=data_sources[station],
                    start_date=hist_start.strftime('%Y-%m-%d'),
                    end_date=hist_end.strftime('%Y-%m-%d'),
                    date_column='data_date'
                )
                
                if not hist_df.empty:
                    if 'data_date' in hist_df.columns:
                        hist_df['data_date'] = pd.to_datetime(hist_df['data_date'])
                    
                    # Filter by parameter if selected
                    if param != "All Parameters":
                        if param in hist_df.columns:
                            hist_df = hist_df[['data_date', param] + 
                                           [col for col in hist_df.columns 
                                            if col not in ['data_date', param]]]
                        else:
                            st.warning(f"Parameter '{param}' not found in data")
                    
                    # Display the raw data
                    st.dataframe(
                        hist_df,
                        use_container_width=True,
                        height=600
                    )
                else:
                    st.warning("No historical data found for selected parameters")
            
            except Exception as e:
                st.error(f"Error loading historical data: {str(e)}")

# --------------------------- CUSTOM DATABASE TAB ---------------------------
# --------------------------- CUSTOM DATABASE TAB ---------------------------
# --------------------------- CUSTOM DATABASE TAB ---------------------------
with tab_custom:
    st.subheader("🔍 Advanced Data Explorer")
    st.markdown("---")
    
    # Section 1: Date Range Selector
    with st.container(border=True):
        st.markdown("### 📅 Date Range Selection")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date", 
                value=datetime.now() - timedelta(days=30),
                help="Select start date for data retrieval"
            )
        with col2:
            end_date = st.date_input(
                "End Date", 
                value=datetime.now(),
                help="Select end date for data retrieval"
            )
    
    # Section 2: Search Parameters
    with st.container(border=True):
        st.markdown("### 🔎 Search Parameters")
        
        # Predefined project list
        PROJECT_OPTIONS = ["Godavari", "Godavari Lower", "Kokan", "Krishna Bhima", "Tapi"]
        
        col1, col2 = st.columns([1, 3])
        with col1:
            search_type = st.radio(
                "Search By",
                ["Location ID", "Project Name"],
                horizontal=True,
                help="Choose between searching by unique Location ID or Project Name"
            )
        
        with col2:
            if search_type == "Project Name":
                search_value = st.selectbox(
                    "Select Project",
                    options=PROJECT_OPTIONS,
                    index=0,
                    help="Select from predefined projects",
                    key="project_select"
                )
            else:
                search_value = st.text_input(
                    "Enter Location ID",
                    placeholder="GOD123",
                    help="Enter exact Location ID to search",
                    key="location_input"
                )

    # Section 3: Search Execution
    st.markdown("---")
    if st.button(
        "🚀 Execute Advanced Search", 
        use_container_width=True,
        help="Initiate cross-database search with selected parameters",
        type="primary"
    ):
        if not search_value.strip():
            st.warning("Please enter/select a search value")
        else:
            results = {}
            total_records = 0
            
            with st.status("🔍 Scanning all data sources...", expanded=True) as status:
                try:
                    # Initialize progress bar
                    progress_text = "Searching across stations..."
                    progress_bar = st.progress(0, text=progress_text)
                    
                    stations = list(data_sources.items())
                    for i, (display_name, table_name) in enumerate(stations):
                        try:
                            # Update progress
                            progress_bar.progress(
                                (i+1)/len(stations), 
                                text=f"Checking {display_name} station..."
                            )
                            
                            # Fetch data with combined filters
                            df = fetch_data(
                                table_name=table_name,
                                filter_column=search_type.lower().replace(" ", "_"),
                                filter_value=search_value.strip(),
                                start_date=start_date.strftime('%Y-%m-%d'),
                                end_date=end_date.strftime('%Y-%m-%d'),
                                date_column='data_date'
                            )
                            
                            if not df.empty:
                                # Convert all columns to strings for display safety
                                df = df.astype(str)
                                results[display_name] = df
                                total_records += len(df)
                                
                        except Exception as e:
                            st.error(f"Error searching {display_name}: {str(e)}")
                
                    status.update(
                        label="Search complete!",
                        state="complete", 
                        expanded=False
                    )
                    
                finally:
                    progress_bar.empty()

            # Display Results
            if not results:
                st.info(f"🚨 No matching records found for {search_type} '{search_value}' between {start_date} and {end_date}")
            else:
                # Success Header
                st.success(f"✅ Found {total_records} records across {len(results)} data sources")
                
                # Results Summary Cards
                with st.container():
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("Total Sources", len(results), help="Number of stations with matching data")
                    with cols[1]:
                        st.metric("Total Records", total_records, help="Total entries across all stations")
                    with cols[2]:
                        valid_timestamps = [
                            pd.to_datetime(df['timestamp']).max() 
                            for df in results.values() 
                            if 'timestamp' in df.columns and not df.empty
                        ]
                        most_recent = (
                            max(valid_timestamps).strftime("%Y-%m-%d %H:%M") 
                            if valid_timestamps else "N/A"
                        )
                        st.metric("Most Recent Entry", most_recent)

                # Detailed Results Section
                st.markdown("---")
                st.subheader("📂 Detailed Results")
                
                # Create expandable sections for each data source
                for display_name, df in results.items():
                    with st.expander(
                        f"🌊 {display_name} Station ({len(df)} records)", 
                        expanded=True
                    ):
                        # Add quick summary row
                        c1, c2, c3 = st.columns(3)
                        c1.metric("First Date", df['data_date'].min())
                        c2.metric("Last Date", df['data_date'].max())
                        c3.metric("Unique Locations", df['location_id'].nunique())
                        
                        # Display dataframe with improved formatting
                        st.dataframe(
                            df,
                            use_container_width=True,
                            height=min(400, 35 * len(df) + 50),
                            column_config={
                                "location_id": "Location ID",
                                "project_name": st.column_config.TextColumn(
                                    "Project",
                                    help="Associated project name"
                                ),
                                "data_date": st.column_config.DateColumn(
                                    "Date",
                                    format="YYYY-MM-DD",
                                    help="Recording date"
                                ),
                                "timestamp": st.column_config.DatetimeColumn(
                                    "Timestamp",
                                    help="Exact measurement time"
                                )
                            }
                        )

with tab_graphs:
    st.subheader("ARS Data Visualization")
    
    # Get ARS data
    ars_data = all_data.get("ARS", pd.DataFrame())
    
    if not ars_data.empty:
        try:
            # Convert data_time to string and clean it
            ars_data['data_time'] = ars_data['data_time'].astype(str)
            ars_data['clean_time'] = ars_data['data_time'].str.replace(r'\d+ days ', '', regex=True)
            
            # Create datetime column
            ars_data['datetime'] = pd.to_datetime(
                ars_data['data_date'].astype(str) + ' ' + ars_data['clean_time'],
                format='%Y-%m-%d %H:%M:%S',
                errors='coerce'
            )
            
            # Drop invalid rows
            ars_data = ars_data.dropna(subset=['datetime'])
            
            # Parameter selection
            parameter = st.selectbox(
                "Select Parameter to Visualize",
                options=['hour_rain', 'daily_rain', 'batt_volt'],
                help="Choose measurement parameter to display"
            )
            
            # Create a time series plot
            fig = px.line(
                ars_data,
                x='datetime',
                y=parameter,
                title=f'ARS {parameter.replace("_", " ").title()} Over Time',
                labels={parameter: parameter.replace("_", " ").title(), 'datetime': 'Date'},
                template='plotly_white'
            )
            
            # Customize layout
            fig.update_layout(
                hovermode='x unified',
                showlegend=True,
                height=600,
                xaxis_title='Time',
                yaxis_title=parameter.replace("_", " ").title()
            )
            
            # Display the plot
            st.plotly_chart(fig, use_container_width=True)
            
            # Optional: Show data summary
            st.markdown("### Data Summary")
            st.dataframe(ars_data.describe(), use_container_width=True)
            
        except Exception as e:
            st.error(f"Error processing ARS data: {str(e)}")
    else:
        st.warning("No ARS data available for visualization")
