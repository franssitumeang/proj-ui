import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


@st.cache_data
def load_travel_journey_data():
    df = pd.read_feather("data/survey_travel_journey.feather")
    df['arah'] = df['arah'].str.replace(r'\s+-\s+', ' - ', regex=True).str.strip()
    return df

@st.cache_data
def load_tarvel_journey_jarak_data():
    df = pd.read_feather("data/survey_travel_journey_jarak.feather")
    return df

@st.cache_data
def clean_raw_tracking_data(raw_data_df):
    """
    Create a clean DataFrame with unique sheet, direction, and gmap values.
    
    Parameters:
    -----------
    raw_data_df : pandas.DataFrame
        Raw tracking data with columns [sheet, arah, gmap]
        
    Returns:
    --------
    pandas.DataFrame
        Cleaned DataFrame with unique sheet and gmap combinations
    """
    gmap_df = raw_data_df[['sheet', 'gmap']].drop_duplicates().reset_index(drop=True)
    return gmap_df

@st.cache_data
def process_distance_sheets(checkpoint_data, gmap_data):
    """
    Process distance data from multiple sheets and add calculated columns.
    
    Parameters:
    -----------
    checkpoint_data : pandas.DataFrame
        Input DataFrame with columns [jarak, arah, sheet, seq]
    gmap_data : pandas.DataFrame
        DataFrame with gmap values, must contain columns [sheet, gmap]
        
    Returns:
    --------
    pandas.DataFrame
        Processed DataFrame with checkpoint distances and cumulative sums
    """
    # Create a copy to avoid modifying the original DataFrame
    result_df = checkpoint_data.copy()
    
    # Initialize new columns
    result_df['checkpoint_distance'] = 0.0
    result_df['checkpoint_distance_cumsum'] = 0.0
    
    # Process each unique combination of sheet and direction
    for sheet in checkpoint_data['sheet'].unique():
        for direction in checkpoint_data[checkpoint_data['sheet'] == sheet]['arah'].unique():
            # Create mask for current sheet and direction
            mask = (result_df['sheet'] == sheet) & (result_df['arah'] == direction)
            
            # Get subset of data
            subset = result_df[mask]
            
            # Calculate total distance for this direction
            total_distance = subset['jarak'].sum()
            
            # Get gmap value from the gmap DataFrame
            gmap_value = gmap_data[
                gmap_data['sheet'] == sheet
            ]['gmap'].iloc[0]
            
            # Calculate checkpoint distance
            checkpoint_distances = subset['jarak'].apply(
                lambda x: x * gmap_value / total_distance if total_distance != 0 else 0
            )
            
            # Assign calculated values
            result_df.loc[mask, 'checkpoint_distance'] = checkpoint_distances
            result_df.loc[mask, 'checkpoint_distance_cumsum'] = checkpoint_distances.cumsum()
    
    return result_df

@st.cache_data
def add_time_and_speed(check_point_data, raw_tracking_data):
    """
    Add time values and speed calculations to checkpoint DataFrame.
    
    Parameters:
    -----------
    check_point_data : pandas.DataFrame
        DataFrame with checkpoint distances
    raw_tracking_data : pandas.DataFrame
        Reference DataFrame with detailed journey data
        
    Returns:
    --------
    pandas.DataFrame
        Checkpoint DataFrame with added time and speed columns
    """
    def find_closest_time(distance, ref_subset):
        """Find the time value for the closest matching distance"""
        if distance == 0:
            return 0.0
        
        # Get the closest distance match
        idx = (ref_subset['jarak_km'] - distance).abs().idxmin()
        return ref_subset.loc[idx, 'waktu_menit']
    
    # Create a copy to avoid modifying the original
    result_df = check_point_data.copy()
    
    # Get the sheet and direction
    sheet = result_df['sheet'].iloc[0]
    direction = result_df['arah'].iloc[0]
    
    # Filter reference data for this sheet and direction
    ref_subset = raw_tracking_data[
        raw_tracking_data['sheet'] == sheet
    ].copy()
    
    # Sort reference data by distance
    ref_subset = ref_subset.sort_values('jarak_km')
    
    # Add time column by looking up closest distance match
    result_df['t'] = result_df['checkpoint_distance_cumsum'].apply(
        lambda x: find_closest_time(x, ref_subset)
    )
    
    # Calculate time difference with previous row
    result_df['t_diff'] = result_df['t'].diff()
    # Set first row's diff to null since there's no previous row
    result_df.loc[result_df.index[0], 't_diff'] = None
    
    # Calculate speed (km/h) = (distance in km / time in minutes) * 60
    result_df['speed'] = result_df.apply(
        lambda row: (row['checkpoint_distance'] / row['t_diff'] * 60) 
        if pd.notnull(row['t_diff']) and row['t_diff'] != 0 
        else None, 
        axis=1
    )
    
    return result_df

@st.cache_data
def process_all_sheets(scaled_checkpoints_df, raw_tracking_data):
    """
    Process time and speed calculations for all sheets and directions.
    
    Parameters:
    -----------
    scaled_checkpoints_df : pandas.DataFrame
        DataFrame with scaled checkpoint distances
    raw_tracking_data : pandas.DataFrame
        Raw tracking data with time information
        
    Returns:
    --------
    pandas.DataFrame
        Complete DataFrame with time and speed for all sheets
    """
    all_results = []
    
    # Get unique sheets
    for sheet in scaled_checkpoints_df['sheet'].unique():
        # Check if this sheet has AM/PM splits in raw data
        raw_sheet_data = raw_tracking_data[raw_tracking_data['sheet'] == sheet]
        has_am_pm = any('AM' in arah or 'PM' in arah for arah in raw_sheet_data['arah'].unique())
        
        # Process each direction
        for base_arah in scaled_checkpoints_df[scaled_checkpoints_df['sheet'] == sheet]['arah'].unique():
            if has_am_pm:
                # Process AM and PM separately
                for period in ['AM', 'PM']:
                    # Get checkpoint data (same for AM/PM)
                    checkpoint_subset = scaled_checkpoints_df[
                        (scaled_checkpoints_df['sheet'] == sheet) & 
                        (scaled_checkpoints_df['arah'] == base_arah)
                    ].copy()
                    
                    # Get raw data for this period
                    period_arah = f"{base_arah} - {period}"
                    raw_data_subset = raw_tracking_data[
                        (raw_tracking_data['sheet'] == sheet) & 
                        (raw_tracking_data['arah'] == period_arah)
                    ].copy()
                    
                    if raw_data_subset.empty:
                        print(f"Warning: No raw tracking data found for {sheet} {period_arah}")
                        continue
                    
                    # Update arah in checkpoint data to match period
                    checkpoint_subset['arah'] = period_arah
                    
                    try:
                        result = add_time_and_speed(checkpoint_subset, raw_data_subset)
                        all_results.append(result)
                    except Exception as e:
                        print(f"Error processing {sheet} {period_arah}: {str(e)}")
            
            else:
                # Process regular A/B direction
                checkpoint_subset = scaled_checkpoints_df[
                    (scaled_checkpoints_df['sheet'] == sheet) & 
                    (scaled_checkpoints_df['arah'] == base_arah)
                ].copy()
                
                raw_data_subset = raw_tracking_data[
                    (raw_tracking_data['sheet'] == sheet) & 
                    (raw_tracking_data['arah'] == base_arah)
                ].copy()
                
                if raw_data_subset.empty:
                    print(f"Warning: No raw tracking data found for {sheet} {base_arah}")
                    continue
                
                try:
                    result = add_time_and_speed(checkpoint_subset, raw_data_subset)
                    all_results.append(result)
                except Exception as e:
                    print(f"Error processing {sheet} {base_arah}: {str(e)}")
    
    if not all_results:
        raise ValueError("No data was successfully processed")
    
    # Combine all results
    final_df = pd.concat(all_results, ignore_index=True)
    
    return final_df

def create_step_data_for_sheet(df):
    """
    Create step line data for all directions in a sheet (A-AM, A-PM, B-AM, B-PM), removing duplicates.
    Uses x coordinates from arah A - AM as reference for distance points.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input DataFrame containing all direction data for a sheet
        
    Returns:
    --------
    dict
        Dictionary of pandas.DataFrames with direction as key and step data as value
        Each DataFrame has columns 'x' and 'y' for step line plotting
    """
    # Get all unique directions
    directions = df['arah'].unique()
    
    # Get reference x coordinates from arah A - AM (or first available direction if A-AM doesn't exist)
    ref_direction = next((d for d in directions if 'arah A' in d), directions[0])
    df_ref = df[df['arah'] == ref_direction].sort_values('seq').reset_index(drop=True)
    x_points = df_ref['checkpoint_distance_cumsum'].tolist()
    
    # Dictionary to store results
    step_data = {}
    
    # Process each direction
    for direction in directions:
        df_dir = df[df['arah'] == direction].sort_values('seq').reset_index(drop=True)
        x_coords = []
        y_coords = []
        
        if 'arah A' in direction:
            # First segment for Arah A - use second row's speed
            if len(df_dir) > 1 and not pd.isna(df_dir['speed'].iloc[1]):
                x_coords.append(0)
                y_coords.append(df_dir['speed'].iloc[1])
            
            # Process transitions forward
            for i in range(1, len(df_dir)-1):
                if not pd.isna(df_dir['speed'].iloc[i+1]):
                    # Add current point with current speed
                    x_coords.append(x_points[i])
                    y_coords.append(df_dir['speed'].iloc[i])
                    
                    # Add same point with next speed
                    x_coords.append(x_points[i])
                    y_coords.append(df_dir['speed'].iloc[i+1])
            
            # Add final point
            if len(df_dir) > 0:
                x_coords.append(x_points[-1])
                y_coords.append(df_dir['speed'].iloc[-1])
                
        else:
            # First segment for Arah B - use first row's speed
            if len(df_dir) > 0 and not pd.isna(df_dir['speed'].iloc[0]):
                x_coords.append(0)
                y_coords.append(df_dir['speed'].iloc[0])
            
            # Process transitions backward
            for i in range(0, len(df_dir)-1):
                if not pd.isna(df_dir['speed'].iloc[i+1]):
                    # Add current point with current speed
                    x_coords.append(x_points[i+1])
                    y_coords.append(df_dir['speed'].iloc[i])
                    
                    # Add same point with next speed
                    x_coords.append(x_points[i+1])
                    y_coords.append(df_dir['speed'].iloc[i+1])
            
            # Add final point with the last known speed value
            if len(df_dir) > 0 and y_coords:  # Check if we have any y coordinates
                x_coords.append(x_points[-1])
                y_coords.append(y_coords[-1])  # Use the last known speed instead of df_dir['speed'].iloc[-1]
        
        # Create DataFrame and remove duplicates
        step_data[direction] = pd.DataFrame({
            'x': x_coords,
            'y': y_coords
        }).drop_duplicates()
    
    return step_data

def display_statistics_in_columns(direction: str, df_dir: pd.DataFrame):
    """
    Display statistics for a given direction in a streamlit column
    """
    with st.container():
        st.markdown(f"**Statistik untuk {direction}**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Jumlah titik", len(df_dir))
            st.metric("Kecepatan rata-rata", f"{df_dir['kmph'].mean():.1f} km/jam")
            st.metric("Kecepatan maksimum", f"{df_dir['kmph'].max()} km/jam")
            
        with col2:
            st.metric("Kecepatan minimum", f"{df_dir['kmph'].min()} km/jam")
            st.metric("Waktu mulai", df_dir['timestamp'].min())
            st.metric("Waktu akhir", df_dir['timestamp'].max())

def display_statistics_in_columns(direction: str, df_dir: pd.DataFrame):
    """
    Display statistics for a given direction in a streamlit column
    """
    with st.container():
        st.markdown(f"**Statistik untuk {direction}**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Jumlah titik", len(df_dir))
            st.metric("Kecepatan rata-rata", f"{df_dir['kmph'].mean():.1f} km/jam")
            st.metric("Kecepatan maksimum", f"{df_dir['kmph'].max()} km/jam")
            
        with col2:
            st.metric("Kecepatan minimum", f"{df_dir['kmph'].min()} km/jam")
            st.metric("Waktu mulai", df_dir['timestamp'].min())
            st.metric("Waktu akhir", df_dir['timestamp'].max())

def generate_two_route_maps(df:pd.DataFrame):
    
    LINE_WIDTH = 7
    ZOOM = 9

    # Get unique direction
    direction_a_start = df[df['arah'] == 'arah A']['arah_awal'].iloc[0]
    direction_a_end = df[df['arah'] == 'arah A']['arah_akhir'].iloc[0]
    direction_b_start = df[df['arah'] == 'arah B']['arah_awal'].iloc[0]
    direction_b_end = df[df['arah'] == 'arah B']['arah_akhir'].iloc[0]

    # Create automated titles
    title_a = f'Arah A ({direction_a_start} → {direction_a_end})'
    title_b = f'Arah B ({direction_b_start} → {direction_b_end})'
    # Create two subplots side by side
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(title_a, title_b),
        specs=[[{"type": "mapbox"}, {"type": "mapbox"}]],
        horizontal_spacing=0.05
    )

    # Define speed ranges
    speed_ranges = [
        (0, 20, '#2F2F2F', '0-20 km/jam'),
        (21, 40, 'red', '21-40 km/jam'),
        (41, 60, 'orange', '41-60 km/jam'),
        (61, float('inf'), 'blue', '61+ km/jam')
    ]

    # Function to add traces for specific direction
    def add_direction_traces(df_direction, col_num):
        for min_speed, max_speed, color, label in speed_ranges:
            mask = (df_direction['kmph'] >= min_speed) & (df_direction['kmph'] <= max_speed)
            df_range = df_direction[mask]

            if not df_range.empty:
                fig.add_trace(
                    go.Scattermapbox(
                        lon=df_range['x'],
                        lat=df_range['y'],
                        mode='markers',
                        marker=dict(
                            size=LINE_WIDTH,
                            color=color,
                            opacity=0.8
                        ),
                        name=label,
                        hovertemplate=(
                            'Kecepatan: %{text} km/jam<br>'
                            'Waktu: %{customdata}<br>'
                            'Lat: %{lat}<br>'
                            'Lon: %{lon}'
                            '<extra></extra>'
                        ),
                        text=df_range['kmph'],
                        customdata=df_range['timestamp'],
                        showlegend=(col_num == 1) # Show legend only for first subplot
                    ),
                    row=1, col=col_num
                )
    
    # Split data by direction
    df_a = df[df['arah'] == 'arah A']
    df_b = df[df['arah'] == 'arah B']

    # Calculate centers for each direction
    center_a = dict(lat=df_a['y'].mean(), lon=df_a['x'].mean())
    center_b = dict(lat=df_b['y'].mean(), lon=df_b['x'].mean())

    # Add traces for each direction
    add_direction_traces(df_a, 1)
    add_direction_traces(df_b, 2)

    # Update layout
    fig.update_layout(
        mapbox1=dict(
            style='carto-positron',
            center=center_a,
            zoom=ZOOM
        ),
        mapbox2=dict(
            style='carto-positron',
            center=center_b,
            zoom=ZOOM
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1
        ),
        legend_font_color='black',
        height=500,
        width=1600,
        title='Peta Rute'
    )

    # st.subheader('Peta Rute')
    st.plotly_chart(fig, use_container_width=True)

    # Write some statistics for each direction
    # Display statistics in columns
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            display_statistics_in_columns(title_a, df_a)
    
    with col2:
        with st.container(border=True):
            display_statistics_in_columns(title_b, df_b)

def generate_four_route_maps(df: pd.DataFrame):

    LINE_WIDTH = 7
    ZOOM = 10

    # Get unique directions and create titles
    directions = {
        'AM': {
            'A': df[df['arah'] == 'arah A - AM'],
            'B': df[df['arah'] == 'arah B - AM']
        },
        'PM': {
            'A': df[df['arah'] == 'arah A - PM'],
            'B': df[df['arah'] == 'arah B - PM']
        }
    }
    
    # Create titles for each subplot
    titles = {}
    for period in ['AM', 'PM']:
        for direction in ['A', 'B']:
            df_dir = directions[period][direction]
            if not df_dir.empty:
                start = df_dir['arah_awal'].iloc[0]
                end = df_dir['arah_akhir'].iloc[0]
                titles[f'{direction}_{period}'] = f'Arah {direction} - {period} ({start} → {end})'

    # Create four subplots in a 2x2 grid
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            titles['A_AM'], titles['B_AM'],
            titles['A_PM'], titles['B_PM']
        ),
        specs=[[{"type": "mapbox"}, {"type": "mapbox"}],
               [{"type": "mapbox"}, {"type": "mapbox"}]],
        vertical_spacing=0.1,
        horizontal_spacing=0.05
    )

    # Define speed ranges
    speed_ranges = [
        (0, 20, '#2F2F2F', '0-20 km/jam'),
        (21, 40, 'red', '21-40 km/jam'),
        (41, 60, 'orange', '41-60 km/jam'),
        (61, float('inf'), 'blue', '61+ km/jam')
    ]

    # Function to add traces for specific direction
    def add_direction_traces(df_direction, row, col, is_first=False):
        for min_speed, max_speed, color, label in speed_ranges:
            mask = (df_direction['kmph'] >= min_speed) & (df_direction['kmph'] <= max_speed)
            df_range = df_direction[mask]

            if not df_range.empty:
                fig.add_trace(
                    go.Scattermapbox(
                        lon=df_range['x'],
                        lat=df_range['y'],
                        mode='markers',
                        marker=dict(
                            size=LINE_WIDTH,
                            color=color,
                            opacity=0.8
                        ),
                        name=label,
                        hovertemplate=(
                            'Kecepatan: %{text} km/jam<br>'
                            'Waktu: %{customdata}<br>'
                            'Lat: %{lat}<br>'
                            'Lon: %{lon}'
                            '<extra></extra>'
                        ),
                        text=df_range['kmph'],
                        customdata=df_range['timestamp'],
                        showlegend=is_first  # Show legend only for first subplot
                    ),
                    row=row, col=col
                )

    # Add traces for each direction and time period
    subplot_positions = {
        ('A', 'AM'): (1, 1),
        ('B', 'AM'): (1, 2),
        ('A', 'PM'): (2, 1),
        ('B', 'PM'): (2, 2)
    }

    # Calculate centers for each subplot
    centers = {}
    for period in ['AM', 'PM']:
        for direction in ['A', 'B']:
            df_dir = directions[period][direction]
            if not df_dir.empty:
                centers[f'{direction}_{period}'] = dict(
                    lat=df_dir['y'].mean(),
                    lon=df_dir['x'].mean()
                )

    # Add all traces
    is_first = True
    for (direction, period), (row, col) in subplot_positions.items():
        df_dir = directions[period][direction]
        if not df_dir.empty:
            add_direction_traces(df_dir, row, col, is_first)
            is_first = False

    # Update layout with four mapboxes
    fig.update_layout(
        mapbox1=dict(
            style='carto-positron',
            center=centers['A_AM'],
            zoom=ZOOM
        ),
        mapbox2=dict(
            style='carto-positron',
            center=centers['B_AM'],
            zoom=ZOOM
        ),
        mapbox3=dict(
            style='carto-positron',
            center=centers['A_PM'],
            zoom=ZOOM
        ),
        mapbox4=dict(
            style='carto-positron',
            center=centers['B_PM'],
            zoom=ZOOM
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1
        ),
        legend_font_color='black',
        height=800,  # Increased height to accommodate 2x2 grid
        width=1600,
        title='Peta Rute'
    )
    # st.subheader('Peta Rute')
    st.plotly_chart(fig, use_container_width=True)

    # Display statistics in a 2x2 grid
    col1, col2 = st.columns(2)

    # Write statistics for each direction and time period
    with col1:
        for direction in ['A']:
            for period in ['AM', 'PM']:
                df_dir = directions[period][direction]
                if not df_dir.empty:
                    with st.container(border=True):
                        display_statistics_in_columns(
                            titles[f'{direction}_{period}'],
                            df_dir
                        )
    
    with col2:
        for direction in ['B']:
            for period in ['AM', 'PM']:
                df_dir = directions[period][direction]
                if not df_dir.empty:
                    with st.container(border=True):
                        display_statistics_in_columns(
                            titles[f'{direction}_{period}'],
                            df_dir
                        )

def generate_linechart_two_directions(df: pd.DataFrame):
    # Create separate dataframes for each direction
    df_a = df[df['arah']== 'arah A'].copy()
    df_b = df[df['arah']== 'arah B'].copy()

    # Get direction names from the first row of each dataframe
    # Since all rows in each direction should have the same arah_awal/arah_akhir
    direction_a_name = f"arah A ({df_a['arah_awal'].iloc[0]} → {df_a['arah_akhir'].iloc[0]})"
    direction_b_name = f"arah B ({df_b['arah_awal'].iloc[0]} → {df_b['arah_akhir'].iloc[0]})"

    # Create custom hover text
    df_a['hover_text'] = df_a.apply(lambda row: f'Waktu: {row["waktu_menit"]:.1f} menit<br>Distance: {row["jarak_km"]:.2f} km', axis=1)
    df_b['hover_text'] = df_b.apply(lambda row: f'Waktu: {row["waktu_menit"]:.1f} menit<br>Distance: {row["jarak_km"]:.2f} km', axis=1)

    # Create the figure
    fig = go.Figure()

    # Add traces for Dietction A (using x-axis at the bottom)
    fig.add_trace(
        go.Scatter(
            x=df_a['jarak_km'],
            y=df_a['waktu_menit'],
            name=direction_a_name,
            line=dict(color='rgb(44, 160, 44)', width=2),  # Green color
            hovertext=df_a['hover_text'],
            hoverinfo='text',
            xaxis='x'
        )
    )

    # Add traces for Direction B (using secondary x-axis at the top)
    fig.add_trace(
        go.Scatter(
            x=df_b['jarak_km'],
            y=df_b['waktu_menit'],
            name=direction_b_name,
            line=dict(color='rgb(255, 127, 14)', width=2),  # Orange/red color
            hovertext=df_b['hover_text'],
            hoverinfo='text',
            xaxis='x2'
        )
    )

    # Update layout with two x-axes
    max_distance = max(df_a['jarak_km'].max(), df_b['jarak_km'].max())
    max_time = max(df_a['waktu_menit'].max(), df_b['waktu_menit'].max())

    fig.update_layout(
        title_text="Grafik Waktu Perjalanan vs. Jarak",
        plot_bgcolor='white',
        showlegend=True,
        height=500,
        
        # Configure the x-axes
        xaxis=dict(
            title="Jarak (km) - Arah A",
            titlefont=dict(color='rgb(44, 160, 44)'),
            tickfont=dict(color='rgb(44, 160, 44)'),
            side='bottom',
            range=[0, max_distance],
            ticksuffix=" km",
            showgrid=False
        ),
        xaxis2=dict(
            title="Jarak (km) - Arah B",
            titlefont=dict(color='rgb(255, 127, 14)'),
            tickfont=dict(color='rgb(255, 127, 14)'),
            side='top',
            range=[max_distance, 0],  # Reversed range
            ticksuffix=" km",
            overlaying='x',
            showgrid=False
        ),
        
        # Configure the y-axis
        yaxis=dict(
            title="Waktu (menit)",
            range=[0, max_time],
            ticksuffix=" min"
        ),
        
        # Hover label settings
        hoverlabel=dict(
            # bgcolor="white",
            font_size=14,
            font_family="Arial"
        ),

        
        # Legend settings
        # legend=dict(
        #     yanchor="top",
        #     y=0.99,
        #     xanchor="left",
        #     x=0.01,
        #     bgcolor="rgba(255, 255, 255, 0.8)"
        # ),
        
        # Margins
        margin=dict(t=100)  # Increased top margin for the second x-axis
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='lightgray'
    )

    # Display the plot in Streamlit
    # st.header("Grafik Waktu Perjalanan vs. Jarak")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Statistik**")
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    # # Get direction names from the first row of each direction
    # direction_a_name = f"Direction A ({df_a['arah_awal'].iloc[0]} to {df_a['arah_akhir'].iloc[0]})"
    # direction_b_name = f"Direction B ({df_b['arah_awal'].iloc[0]} to {df_b['arah_akhir'].iloc[0]})"
    
    # Generate statistics for Direction A
    with col1:
        with st.container(border=True):
            st.write(f"**{direction_a_name}**")
            # st.write(f"Average Distance: {df_a['jarak_km'].mean():.2f} km")
            st.write(f"Waktu Maksimum: {df_a['waktu_menit'].max():.1f} menit")
            st.write(f"Jarak Total: {df_a['jarak_km'].max():.2f} km")
            st.write(f"Rata-rata Kecepatan: {(df_a['jarak_km'].mean() / df_a['waktu_menit'].mean() * 60):.2f} km/h")
            # st.write("---")

    # Generate statistics for Direction B
    with col2:
        with st.container(border=True):
            st.write(f"**{direction_b_name}**")
            # st.write(f"Average Distance: {df_b['jarak_km'].mean():.2f} km")
            st.write(f"Waktu Maksimum: {df_b['waktu_menit'].max():.1f} menit")
            st.write(f"Jarak Total: {df_b['jarak_km'].max():.2f} km")
            st.write(f"Rata-rata Kecepatan: {(df_b['jarak_km'].mean() / df_b['waktu_menit'].mean() * 60):.2f} km/jam")
            # st.write("---")

def generate_linechart_four_directions(df: pd.DataFrame):
    # Create separate dataframes for each direction
    df_a_am = df[df['arah'] == 'arah A - AM'].copy()
    df_a_pm = df[df['arah'] == 'arah A - PM'].copy()
    df_b_am = df[df['arah'] == 'arah B - AM'].copy()
    df_b_pm = df[df['arah'] == 'arah B - PM'].copy()

    # Get direction names from the first row of each dataframe
    # Get direction name from the dataframe
    def get_direction_name(direction_df):
        if len(direction_df) > 0:
            arah_full = direction_df['arah'].iloc[0]  # Gets full direction string (e.g., 'arah A - AM')
            return f"{arah_full} ({direction_df['arah_awal'].iloc[0]} → {direction_df['arah_akhir'].iloc[0]})"
        return "No data"

    # Create custom hover text for each direction
    for direction_df in [df_a_am, df_a_pm, df_b_am, df_b_pm]:
        direction_df['hover_text'] = direction_df.apply(
            lambda row: f'Waktu: {row["waktu_menit"]:.1f} menit<br>Jarak: {row["jarak_km"]:.2f} km', 
            axis=1
        )

    # Create the figure
    fig = go.Figure()

    # Define trace configurations
    traces = [
        {
            'df': df_a_am,
            'name': get_direction_name(df_a_am),
            'color': 'rgb(44, 160, 44)',  # Green
            'dash': 'solid',
            'xaxis': 'x'
        },
        {
            'df': df_a_pm,
            'name': get_direction_name(df_a_pm),
            'color': 'rgb(44, 160, 44)',  # Green
            'dash': 'dot',
            'xaxis': 'x'
        },
        {
            'df': df_b_am,
            'name': get_direction_name(df_b_am),
            'color': 'rgb(255, 127, 14)',  # Orange
            'dash': 'solid',
            'xaxis': 'x2'
        },
        {
            'df': df_b_pm,
            'name': get_direction_name(df_b_pm),
            'color': 'rgb(255, 127, 14)',  # Orange
            'dash': 'dot',
            'xaxis': 'x2'
        }
    ]

    # Add traces
    for trace in traces:
        fig.add_trace(
            go.Scatter(
                x=trace['df']['jarak_km'],
                y=trace['df']['waktu_menit'],
                name=trace['name'],
                line=dict(
                    color=trace['color'],
                    width=2,
                    dash=trace['dash']
                ),
                hovertext=trace['df']['hover_text'],
                hoverinfo='text',
                xaxis=trace['xaxis']
            )
        )

    # Calculate maximum values for axes
    all_dfs = [df_a_am, df_a_pm, df_b_am, df_b_pm]
    max_distance = max(df['jarak_km'].max() for df in all_dfs if not df.empty)
    max_time = max(df['waktu_menit'].max() for df in all_dfs if not df.empty)

    # Update layout
    fig.update_layout(
        title_text="Grafik Waktu Perjalanan vs. Jarak",
        plot_bgcolor='white',
        showlegend=True,
        height=500,
        
        # Configure the x-axes
        xaxis=dict(
            title="Jarak (km) - Arah A",
            titlefont=dict(color='rgb(44, 160, 44)'),
            tickfont=dict(color='rgb(44, 160, 44)'),
            side='bottom',
            range=[0, max_distance],
            ticksuffix=" km",
            showgrid=False
        ),
        xaxis2=dict(
            title="Jarak (km) - Arah B",
            titlefont=dict(color='rgb(255, 127, 14)'),
            tickfont=dict(color='rgb(255, 127, 14)'),
            side='top',
            range=[max_distance, 0],  # Reversed range
            ticksuffix=" km",
            overlaying='x',
            showgrid=False
        ),
        
        # Configure the y-axis
        yaxis=dict(
            title="Waktu (menit)",
            range=[0, max_time],
            ticksuffix=" min"
        ),
        
        # Hover label settings
        hoverlabel=dict(
            # bgcolor="white",
            font_size=14,
            font_family="Arial",
            # font_color='black'
        ),
        
        # Legend settings
        # legend=dict(
        #     yanchor="top",
        #     y=0.99,
        #     xanchor="left",
        #     x=0.01,
        #     bgcolor="rgba(255, 255, 255, 0.8)"
        # ),
        
        # Margins
        margin=dict(t=100)
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='lightgray'
    )

    # Display the plot in Streamlit
    # st.header("Grafik Waktu Perjalanan vs. Jarak")
    st.plotly_chart(fig, use_container_width=True)

    # Automated summary statistics generation
    st.markdown("**Statistik**")
    
    # Create a dynamic grid based on the number of non-empty dataframes
    non_empty_dfs = [df for df in all_dfs if not df.empty]
    num_cols = min(2, len(non_empty_dfs))  # Maximum 2 columns
    num_rows = (len(non_empty_dfs) + num_cols - 1) // num_cols
    
    # Create columns for layout
    cols = st.columns(num_cols)
    
    # Direction names mapping
    direction_names = {
        'arah A - AM': f"Arah A ({df_a_am['arah_awal'].iloc[0]} → {df_a_am['arah_akhir'].iloc[0]}) - Pagi",
        'arah A - PM': f"Arah A ({df_a_pm['arah_awal'].iloc[0]} → {df_a_pm['arah_akhir'].iloc[0]}) - Sore",
        'arah B - AM': f"Arah B ({df_b_am['arah_awal'].iloc[0]} → {df_b_am['arah_akhir'].iloc[0]}) - Pagi",
        'arah B - PM': f"Arah B ({df_b_pm['arah_awal'].iloc[0]} → {df_b_pm['arah_akhir'].iloc[0]}) - Sore"
    }
    
    # Generate statistics for each direction
    for idx, direction_df in enumerate(non_empty_dfs):
        col_idx = idx % num_cols
        with cols[col_idx]:
            with st.container(border=True):
                direction = direction_df['arah'].iloc[0]
                st.write(f"**{direction_names[direction]}**")
                # st.write(f"Average Distance: {direction_df['jarak_km'].mean():.2f} km")
                st.write(f"Waktu Maksimum: {direction_df['waktu_menit'].max():.1f} menit")
                st.write(f"Jarak Total: {direction_df['jarak_km'].max():.2f} km")
                st.write(f"Rata-rata Kecepatan: {(direction_df['jarak_km'].mean() / direction_df['waktu_menit'].mean() * 60):.2f} km/jam")
                # st.write("---")

def generate_stepchart_two_directions(step_data_dict, title="Grafik Kecepatan Rata-rata vs. Jarak"):
    """
    Create a styled step line plot using Plotly for two directions with custom x-axis ticks
    
    Parameters:
    -----------
    step_data_dict : dict
        Dictionary containing DataFrames with 'x' and 'y' columns for each direction
    title : str
        Plot title
        
    Returns:
    --------
    None
        Displays the plot in Streamlit
    """
    # Create the figure
    fig = go.Figure()
    
    # Color mapping for directions
    color_map = {
        'arah A': 'green',
        'arah B': 'red'
    }
    
    # Get unique x values across all directions
    all_x_values = set()
    for step_df in step_data_dict.values():
        all_x_values.update(step_df['x'].unique())
    x_ticks = sorted(list(all_x_values))
    
    # Add traces for each direction
    for direction, step_df in step_data_dict.items():
        fig.add_trace(go.Scatter(
            x=step_df['x'],
            y=step_df['y'],
            mode='lines',
            line=dict(
                color=color_map.get(direction, 'blue'),  # Default to blue if direction not in map
                width=2
            ),
            name=direction
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0,  # Left align title
            font=dict(size=14)
        ),
        xaxis=dict(
            title="Jarak (km)",
            gridcolor='lightgray',
            gridwidth=1,
            griddash='dot',
            zeroline=False,
            tickmode='array',  # Use custom tick values
            tickvals=x_ticks,  # Set tick locations to unique x values
            ticktext=[f"{x:.1f}" for x in x_ticks],  # Format tick labels
            # tickangle=45  # Rotate labels for better readability
        ),
        yaxis=dict(
            title=title,
            gridcolor='lightgray',
            gridwidth=1,
            griddash='dot',
            zeroline=False,
            dtick=10  # Set major grid lines interval
        ),
        plot_bgcolor='white',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=-0.2,  # Moves legend below the chart
            xanchor="center",
            x=0.5,  # Centers the legend
            orientation="h"  # Makes legend horizontal
        ),
        margin=dict(l=50, r=20, t=50, b=100),  # Increased bottom margin to accommodate legend
        height=400,
        width=800
    )
    
    # Display the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)


def generate_stepchart_four_directions(step_data_dict, title="Grafik Kecepatan Rata-rata vs. Jarak"):
    """
    Create a styled step line plot using Plotly for four directions (AM/PM variants)
    
    Parameters:
    -----------
    step_data_dict : dict
        Dictionary containing DataFrames with 'x' and 'y' columns for each direction
    title : str
        Plot title
        
    Returns:
    --------
    None
        Displays the plot in Streamlit
    """
    # Create the figure
    fig = go.Figure()
    
    # Color and style mapping for directions
    style_map = {
        'arah A - AM': {'color': 'green', 'dash': 'solid'},
        'arah B - AM': {'color': 'red', 'dash': 'solid'},
        'arah A - PM': {'color': 'green', 'dash': 'dash'},
        'arah B - PM': {'color': 'red', 'dash': 'dash'}
    }
    
    # Get unique x values across all directions
    all_x_values = set()
    for step_df in step_data_dict.values():
        all_x_values.update(step_df['x'].unique())
    x_ticks = sorted(list(all_x_values))
    
    # Add traces for each direction
    for direction, step_df in step_data_dict.items():
        style = style_map.get(direction, {'color': 'blue', 'dash': 'solid'})
        fig.add_trace(go.Scatter(
            x=step_df['x'],
            y=step_df['y'],
            mode='lines',
            line=dict(
                color=style['color'],
                width=2,
                dash=style['dash']
            ),
            name=direction
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0,  # Left align title
            font=dict(size=14)
        ),
        xaxis=dict(
            title="Jarak (km)",
            gridcolor='lightgray',
            gridwidth=1,
            griddash='dot',
            zeroline=False,
            tickmode='array',  # Use custom tick values
            tickvals=x_ticks,  # Set tick locations to unique x values
            ticktext=[f"{x:.1f}" for x in x_ticks],  # Format tick labels
            # tickangle=45  # Rotate labels for better readability
        ),
        yaxis=dict(
            title=title,
            gridcolor='lightgray',
            gridwidth=1,
            griddash='dot',
            zeroline=False,
            dtick=10
        ),
        plot_bgcolor='white',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=-0.2,  # Moves legend below the chart
            xanchor="center",
            x=0.5,  # Centers the legend
            orientation="h"  # Makes legend horizontal
        ),
        margin=dict(l=50, r=20, t=50, b=100),  # Increased bottom margin to accommodate legend
        height=400,
        width=800
    )
    
    # Display the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)

def get_route_type(df: pd.DataFrame) -> str:
    """
    Determine if the route has two or four directions.
    Returns 'two' or 'four' based on the data structure.
    """
    unique_directions = df['arah'].unique()
    return 'four' if any('AM' in direction or 'PM' in direction for direction in unique_directions) else 'two'

def generate_travel_journey_dashboard(df: pd.DataFrame, speed_df: pd.DataFrame, selected_route: str):
    """
    Generate the dashboard for the selected route, automatically choosing
    between two or four direction maps based on the data structure.
    """
    # Filter data for selected route
    selected_df = df[df['sheet'] == selected_route]
    selected_speed_df = speed_df[speed_df['sheet'] == selected_route]
    step_dict = create_step_data_for_sheet(selected_speed_df)

    # Determine route type and generate appropriate map
    route_type = get_route_type(selected_df)

    
    if route_type == 'two':
        pass
        generate_two_route_maps(selected_df)
        st.write("---")
        generate_linechart_two_directions(selected_df)
        st.write("---")
        generate_stepchart_two_directions(step_dict)
    else:  # route_type == 'four'
        generate_four_route_maps(selected_df)
        st.write("---")
        generate_linechart_four_directions(selected_df)
        st.write("---")
        generate_stepchart_four_directions(step_dict)
        pass

    # Display the dataframe
    # st.write("---")
    # st.markdown(f"#### Data Untuk {selected_route}")
    # st.dataframe(selected_df, hide_index=True, use_container_width=True)
    # st.dataframe(selected_speed_df, hide_index=True, use_container_width=True)
    # st.write(step_dict)
    

def show_travel_journey():
    # Load and process data
    travel_journey_df = load_travel_journey_data()
    raw_tracking_data_df = travel_journey_df.copy()
    check_point_data_df = load_tarvel_journey_jarak_data()
    gmap_df = clean_raw_tracking_data(raw_tracking_data_df)
    scaled_checkpoints_df = process_distance_sheets(check_point_data_df, gmap_df)
    speed_df = process_all_sheets(scaled_checkpoints_df, raw_tracking_data_df)


    # Create a mapping of sheet names to their display labels
    route_display = {}
    for sheet in travel_journey_df['sheet'].unique():
        # Get the first row for this sheet (we can use either direction)
        route_info = travel_journey_df[travel_journey_df['sheet'] == sheet].iloc[0]
        display_text = f"{sheet} ({route_info['arah_awal']} - {route_info['arah_akhir']})"
        route_display[sheet] = display_text

    # Create the list for the selectbox with the display labels
    route_list = list(travel_journey_df['sheet'].unique())
    # display_list = [route_display[sheet] for sheet in route_list]

    # Use format_func to show the display text while keeping the original sheet value
    selected_route = st.selectbox(
        "Pilih Rute",
        route_list,
        format_func=lambda x: route_display[x],
        help="Pilih rute untuk divisualisasikan"
    )

    # Generate dashboard
    generate_travel_journey_dashboard(travel_journey_df, speed_df, selected_route)
