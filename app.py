import folium
import streamlit as st
st.set_page_config(layout = "wide")

from auth import check_password
import pandas as pd
import plotly.graph_objects as go
# from utils.util import engine, read_database
from page.origin_destination import chart_vehicle_origin_destination, show
from page.travel_journey import show_travel_journey

from streamlit_folium import st_folium
from branca.element import Template, MacroElement
from st_on_hover_tabs import on_hover_tabs


if not check_password():
    st.stop()

# Create the legend template as an HTML element
legend_template = """
{% macro html(this, kwargs) %}
<div id='maplegend' class='maplegend' 
    style='position: absolute; z-index: 9999; background-color: rgba(255, 255, 255, 0.5);
     border-radius: 6px; padding: 10px; font-size: 10.5px; right: 20px; top: 20px;'>     
<div class='legend-scale'>
  <ul class='legend-labels'>
    <li><span style='background: black; opacity: 0.75;'></span>Durasi Survei 24 jam</li>
    <li><span style='background: orange; opacity: 0.75;'></span>Durasi Survei 16 jam</li>
  </ul>
</div>
</div> 
<style type='text/css'>
  .maplegend .legend-scale ul {margin: 0; padding: 0; color: #0f0f0f;}
  .maplegend .legend-scale ul li {list-style: none; line-height: 18px; margin-bottom: 1.5px;}
  .maplegend ul.legend-labels li span {float: left; height: 15px; width: 15px; margin-right: 4.5px;}
</style>
{% endmacro %}
"""

st.markdown('<style>' + open('./style.css').read() + '</style>', unsafe_allow_html=True)
st.markdown("""
    <style>
    /* Adjust line spacing */
    p {
        line-height: 0.9;  /* You can adjust this value (1.0 is default) */
    }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    tabs = on_hover_tabs(tabName=['Traffic Counting', 'Travel Journey', 'Asal Tujuan'], 
                         iconName=['dashboard', 'construction', 'repeat_one'], default_choice=0)


# @st.cache_data
def fetch_base_data():
    # query = """
    #     with data_cor AS (
    #         select
    #             distinct
    #             kode_lokasi,
    #             sheet,
    #             filename,
    #             region,
    #             hari_tanggal,
    #             cuaca,
    #             nama_ruas_jalan,
    #             unnest(string_to_array(koordinat_lokasi, 'dan')) AS koordinat,
    #             arah_dari,
    #             arah_menuju,
    #             surveyor_rekam_hitung,
    #             durasi,
    #             kode_arah,
    #             jam_puncak_arah_1_hk,
    #             vol_jam_puncak_arah_1_hk,
    #             catatan_hk,
    #             jam_puncak_arah_2_hk,
    #             vol_jam_puncak_arah_2_hk,
    #             jam_puncak_arah_1_hl,
    #             vol_jam_puncak_arah_1_hl,
    #             catatan_hl,
    #             jam_puncak_arah_2_hl,
    #             vol_jam_puncak_arah_2_hl
    #         from survey_traffic_counting
    #     )
    #     select
    #         *,
    #         case
    #             when koordinat like '%%;%%' then cast(trim(split_part(koordinat, ';', 1)) as float)
    #             else cast(trim(split_part(koordinat, ',', 1)) as float)
    #         end as latitude,
    #         case
    #             when koordinat like '%%;%%' then cast(trim(split_part(koordinat, ';', 2)) as float)
    #             else cast(trim(split_part(koordinat, ',', 2)) as float)
    #         end as longitude
    #     from data_cor
    #     ;
    # """
    # df = read_database(engine=engine, query=query)
    return pd.read_pickle("data/fetch_base_data_tc.pkl")

# @st.cache_data
def fetch_stats_data():
    # query = """
    #         select
    #             kode_lokasi,
    #             sheet,
    #             FLOOR(cast(trim(split_part(rentang_survei, '-', 1)) as float)) as start_rentang_survei,
    #             case
    #                 when FLOOR(cast(trim(split_part(rentang_survei, '-', 1)) as float)) < 6 then FLOOR(cast(trim(split_part(rentang_survei, '-', 1)) as float)) + 25
    #                 else FLOOR(cast(trim(split_part(rentang_survei, '-', 1)) as float))
    #             end as rank_rentang_survei,
    #             (FLOOR(cast(trim(split_part(rentang_survei, '-', 1)) as float)):: varchar) || '.00 - ' || (CEIL(cast(trim(split_part(rentang_survei, '-', 2)) as float)):: varchar) || '.00' as rentang_survei_,
    #             sum("Gol-6") as gol_6,
    #             sum("Gol-1-a") as gol_1_a,
    #             sum("Gol-1-b") as gol_1_b,
    #             sum("Gol-1-c") as gol_1_c,
    #             sum("Gol-1-d") as gol_1_d,
    #             sum("Gol-1-a") as gol_1_e,
    #             sum("Gol-2") as gol_2,
    #             sum("Gol-3") as gol_3,
    #             sum("Gol-4") as gol_4,
    #             sum("Gol-5") as gol_5,
    #             sum(total_tanpa_sepeda_motor) as total_tanpa_sepeda_motor,
    #             sum(total_dengan_sepeda_motor) as total_dengan_sepeda_motor
    #         from
    #             survey_traffic_counting
    #         group by
    #             kode_lokasi,
    #             sheet,
    #             start_rentang_survei,
    #             rank_rentang_survei,
    #             rentang_survei_
    #         order by sheet, rank_rentang_survei
    #     ;
    # """
    # df = read_database(engine=engine, query=query)
    return pd.read_pickle("data/fetch_stats_data_tc.pkl")

def create_pie_chart(_data, title_suffix="", show_inside_text=True):

    width, height = 350, 300
    # For small charts, only show percentages for segments > 5%
    textinfo = 'percent'
    textfont_size = 9
    textposition = 'inside'
    legend_config = dict(
        orientation="h",
        yanchor="top",
        y=-0.05,
        xanchor="center",
        x=0.5,
        font=dict(size=8)
    )
    margin_config = dict(t=50, b=120, l=10, r=10)
    height = 550  # Add space for bottom legend

    # Create labels with percentages for legend
    labels_with_percent = [f"{label} ({(pct)}%)" for label, pct in zip(_data['vehicle_type'], _data['percentage'])]
    
    text_template = [f"{pct}%" for pct in _data['percentage']]
    # Custom colors matching your theme
    custom_colors = [
        "#6055FC",  # Teal (main color)
        '#FFE66D',  # Yellow  
        '#FF6B6B',  # Red/Pink
        '#FFB4A2',  # Light pink
        '#95E1D3',  # Light teal
        '#F38BA8',  # Pink
        '#A8DADC',  # Light blue
        "#C09DDF",  # Light purple
        '#B8860B',  # Dark golden
        "#D103D1"   # Plum
    ]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels_with_percent,  # Use labels with percentages
        values=_data['percentage'],
        
        # Text configuration with smart positioning
        # textinfo=textinfo,
        textposition=textposition,
        texttemplate=text_template,
        textfont=dict(
            size=textfont_size + 1,  # Slightly larger font for better visibility
            color='white',  # White text for better contrast on colored slices
            family='Arial Black, Arial, sans-serif'  # Use Arial Black for bolder appearance
        ),
        
        
        marker=dict(
            # colors=custom_colors,
            line=dict(color='#FFFFFF', width=2)
        ),
        
        # Enhanced hover information (show original labels)
        customdata=_data['vehicle_type'],  # Original labels for hover
        
        hovertemplate='<b>%{customdata}</b><br>' +
                     'Percentage: %{percent}<br>' +
                     '<extra></extra>',
        
        # Pull small slices for better visibility
        pull=[0.02 if val < 1 else 0 for val in _data['percentage']],
        
        # Improved text positioning for inside text
        insidetextorientation='horizontal'
    )])
    
    fig.update_layout(
        title={
            'text': f"Komposisi Jenis Kendaraan{title_suffix}",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'color': '#2F2F2F'}
        },
        
        # Legend configuration
        showlegend=True,
        legend=legend_config,
        
        # Size and margins
        width=width,
        height=height,
        margin=margin_config,
        
        # Background and font theme
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(
            family='Arial, sans-serif',
            color='#2F2F2F'
        )
    )
    
    return fig

def chart_stats(df_stats:pd.DataFrame, df_base:pd.DataFrame, kode_lokasi:str, filter_sheet:str, fig_title:str):
    df_base_filtered = df_base.loc[(df_base['kode_lokasi'] == kode_lokasi) & (df_base['sheet'].str.contains(filter_sheet))]
    
    df_stats_filtered = df_stats.loc[(df_stats['kode_lokasi'] == kode_lokasi) & (df_stats['sheet'].str.contains(filter_sheet))]
    df_stats_filtered = df_stats_filtered.groupby('rentang_survei_', as_index=False).sum()
    df_stats_filtered = df_stats_filtered.sort_values(by='rank_rentang_survei').drop(columns=['start_rentang_survei', 'kode_lokasi', 'sheet', 'rank_rentang_survei'])
    fig_scatter = go.Figure()
    
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['gol_6'], mode='lines', name='Sepeda Motor, Bajaj'))
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['gol_1_a'], mode='lines', name='Sedan, Taksi, Minibus, MPV'))
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['gol_1_b'], mode='lines', name='Angkot, Mikrolet'))
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['gol_1_c'], mode='lines', name='Bus kecil, sedang'))
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['gol_1_d'], mode='lines', name='Bus besar'))
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['gol_1_e'], mode='lines', name='Pick-up/Box'))
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['gol_2'], mode='lines', name='Truk 2 Gandar'))
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['gol_3'], mode='lines', name='Truk Besar 3 Gandar'))
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['gol_4'], mode='lines', name='Truk Besar 4 Gandar'))
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['gol_5'], mode='lines', name='Truk Besar ≥ 5 Gandar'))
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['total_tanpa_sepeda_motor'], mode='lines', name='Total Tanpa Sepeda Motor', line=dict(color='black', dash='dash')))
    fig_scatter.add_trace(go.Scatter(x=df_stats_filtered['rentang_survei_'], y=df_stats_filtered['total_dengan_sepeda_motor'], mode='lines', name='Total Dengan Sepeda Motor', line=dict(color='black')))
    
    fig_scatter.update_layout(
        title=fig_title,
        xaxis_title="Jam",
        yaxis_title="Kendaraan/Jam",
        legend_title="Keterangan"
    )
    
    labels = [
        'Sepeda Motor, Bajaj',
        'Sedan, Taksi, Minibus, MPV',
        'Angkot, Mikrolet',
        'Bus kecil, sedang',
        'Bus besar',
        'Pick-up/Box',
        'Truk 2 Gandar',
        'Truk Besar 3 Gandar',
        'Truk Besar 4 Gandar',
        'Truk Besar ≥ 5 Gandar'
    ]
    values = [
        df_base_filtered['total_gol_6'].sum(),
        df_base_filtered['total_gol_1_a'].sum(),
        df_base_filtered['total_gol_1_b'].sum(),
        df_base_filtered['total_gol_1_c'].sum(),
        df_base_filtered['total_gol_1_d'].sum(),
        df_base_filtered['total_gol_1_e'].sum(),
        df_base_filtered['total_gol_2'].sum(),
        df_base_filtered['total_gol_3'].sum(),
        df_base_filtered['total_gol_4'].sum(),
        df_base_filtered['total_gol_5'].sum(),
    ]
    values = [round((x/sum(values)),3) * 100 for x in values]
    values = [float("%.2f" % round(x, 2)) for x in values]
    _data = {
        "vehicle_type": labels,
        "percentage": values
    }
    fig_pie = create_pie_chart(_data=_data)
    # fig_pie = go.Figure(
    #     data=[go.Pie(
    #         labels=labels,
    #         values=values,
    #         # hole=0.4,
    #         textinfo='label+percent',
    #         insidetextorientation='radial'
    #         # pull=[0.01 for _ in range(3)]
    #     )]
    # )
    
    # fig_pie.update_layout(
    #     title="Komposisi Jenis Kendaraan",
    #     # annotations=[dict(text='Kendaraan', x=0.5, y=0.5, font_size=15, showarrow=False)]
    # )

    return fig_scatter, fig_pie, {
        "total_tanpa_sepeda_motor": df_base_filtered['total_tanpa_sepeda_motor_summary'].sum(),
        "total_dengan_sepeda_motor": df_base_filtered['total_dengan_sepeda_motor_summary'].sum()
    }
    
if "show_detail" not in st.session_state:
    st.session_state["show_detail"] = {}

show_detail = st.session_state["show_detail"]
if not "region" in show_detail:
    show_detail["region"] = "JABO"
    

df_base = fetch_base_data()
df_stats = fetch_stats_data()

if tabs =='Traffic Counting':
    st.header("Survei Traffic Counting")
    c1, c2 = st.columns([2,4.3])
    with c1:
        display_text_select = {
            "JABO": "JABODETABEK",
            "BDG": "BANDUNG RAYA",
            "JAWA": "JAWA"
        }
        region_select = st.selectbox("Filter Region", ['JABO', 'BDG', 'JAWA'], key=f"region_select", format_func=lambda x: display_text_select[x])
        show_detail["region"] = region_select
    
    with c2:
        region_dict = {
            "JABO": {
                "lat_long": [-6.24089, 106.84492],
                "zoom": 10.5
            },
            "BDG": {
                "lat_long": [-6.93748,107.59947],
                "zoom": 11
            },
            "JAWA": {
                "lat_long": [-7.4225,109.83343],
                "zoom": 7
            }
        }
        region = show_detail["region"]
        center_coordinate = region_dict[show_detail["region"]]["lat_long"]
        key = show_detail["region"]
        zoom_start = region_dict[show_detail["region"]]["zoom"]
        
        df_base_selected = df_base.loc[df_base['region'] == region]
        m = folium.Map(location=center_coordinate, zoom_start=zoom_start, key=key)
        macro = MacroElement()
        macro._template = Template(legend_template)
        m.get_root().add_child(macro)
        for idx, row in df_base_selected.iterrows():        
            color = "black" if row["durasi"] == "24 jam" else "orange"
            folium.Marker(
                [row["latitude"], row["longitude"]], 
                popup=row["kode_lokasi"],
                tooltip=row["kode_lokasi"],
                icon=folium.Icon(color=color)
            ).add_to(m)
        output = {}
        output[key] = st_folium(
            m, width=1200, height=585, returned_objects=["last_object_clicked_tooltip"], key=f"{key}_map"
        )
    
    last_object_clicked_tooltip = output[key]["last_object_clicked_tooltip"]
    with c1.container(border=True):
        if last_object_clicked_tooltip:
            durasi = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'durasi'].iloc[0]
            arah_dari = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'arah_dari'].iloc[0]
            arah_menuju = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'arah_menuju'].iloc[0]
            hari_tanggal_hk = df_base_selected.loc[(df_base_selected['kode_lokasi'] == last_object_clicked_tooltip) & (df_base_selected['hari_tanggal_hk'].notnull()), 'hari_tanggal_hk'].iloc[0]
            hari_tanggal_hl = df_base_selected.loc[(df_base_selected['kode_lokasi'] == last_object_clicked_tooltip) & (df_base_selected['hari_tanggal_hl'].notnull()), 'hari_tanggal_hl'].iloc[0]
            
            cuaca_hk = df_base_selected.loc[(df_base_selected['kode_lokasi'] == last_object_clicked_tooltip) & (df_base_selected['cuaca_hk'].notnull()), 'cuaca_hk'].iloc[0]
            cuaca_hl = df_base_selected.loc[(df_base_selected['kode_lokasi'] == last_object_clicked_tooltip) & (df_base_selected['cuaca_hl'].notnull()), 'cuaca_hl'].iloc[0]
            
            nama_ruas_jalan = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'nama_ruas_jalan'].iloc[0]
            surveyor_rekam_hitung = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'surveyor_rekam_hitung'].iloc[0]
            jam_puncak_arah_1_hk = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'jam_puncak_arah_1_hk'].iloc[0]
            vol_jam_puncak_arah_1_hk = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'vol_jam_puncak_arah_1_hk'].iloc[0]
            catatan_hk = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'catatan_hk'].iloc[0]
            jam_puncak_arah_2_hk = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'jam_puncak_arah_2_hk'].iloc[0]
            vol_jam_puncak_arah_2_hk = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'vol_jam_puncak_arah_2_hk'].iloc[0]
            jam_puncak_arah_1_hl = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'jam_puncak_arah_1_hl'].iloc[0]
            vol_jam_puncak_arah_1_hl = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'vol_jam_puncak_arah_1_hl'].iloc[0]
            catatan_hl = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'catatan_hl'].iloc[0]
            jam_puncak_arah_2_hl = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'jam_puncak_arah_2_hl'].iloc[0]
            vol_jam_puncak_arah_2_hl = df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'vol_jam_puncak_arah_2_hl'].iloc[0]
            
            st.write(f"**No./Kode Lokasi :** {df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'kode_lokasi'].iloc[0]}")
            st.write(f"**Durasi :** {durasi}")
            # st.write(f"**Koordinat Lokasi :** {df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'koordinat_lokasi_text'].iloc[0]}")
            st.write(f"**Koordinat Lokasi :**")
            st.markdown(df_base_selected.loc[df_base_selected['kode_lokasi'] == last_object_clicked_tooltip, 'koordinat_lokasi_text'].iloc[0].replace('\n', '  \n'), unsafe_allow_html=True)
            st.write(f"**Hari Tanggal :**")
            st.markdown(f'<p style="font-size: 14px;">Hari Kerja: {hari_tanggal_hk}</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size: 14px;">Hari Libur: {hari_tanggal_hl}</p>', unsafe_allow_html=True)
            
            st.write(f"**Cuaca :**")
            st.markdown(f'<p style="font-size: 14px;">Hari Kerja: {cuaca_hk}</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size: 14px;">Hari Libur: {cuaca_hl}</p>', unsafe_allow_html=True)
            st.write(f"**Surveyor Rekam Hitung :**")
            st.write(surveyor_rekam_hitung)
            st.write(f"**Nama Ruas Jalan :**")
            st.write(nama_ruas_jalan)
            st.write("**Arah 1**")
            st.markdown(f'<p style="font-size: 14px;">Arah dari: {arah_dari}</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size: 14px;">Arah menuju: {arah_menuju}</p>', unsafe_allow_html=True)
            st.write("**Arah 2**")
            st.markdown(f'<p style="font-size: 14px;">Arah dari: {arah_menuju}</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size: 14px;">Arah menuju: {arah_dari}</p>', unsafe_allow_html=True)

    
    if last_object_clicked_tooltip:
        st.markdown(f"<h1 style='text-align: center; color: black;'>Profil Hari Kerja - {last_object_clicked_tooltip}</h1>", unsafe_allow_html=True)
        st.write("---")
        c1, c2, c3 = st.columns([1,1,1])
        with c1.container(border=True):
            fig_hk, fig_pie_hk, agg_data = chart_stats(df_stats=df_stats, df_base=df_base, kode_lokasi=last_object_clicked_tooltip, filter_sheet="HK", fig_title="Fluktuasi Volume Kendaraan - Total Dua Arah")
            st.plotly_chart(fig_hk, use_container_width=True, key=f"{key}_fig_hk")
            st.plotly_chart(fig_pie_hk, use_container_width=True, key=f"{key}_fig_pie_hk")
            
            with st.container(border=True, height=300):
                st.markdown(f'<p style="font-size: 16px; text-decoration: underline;">Total Volume Kendaraan {durasi} - Dua arah</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Tanpa motor: {agg_data.get("total_tanpa_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Dengan motor: {agg_data.get("total_dengan_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Nama ruas jalan: {nama_ruas_jalan}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Hari, tanggal: {hari_tanggal_hk}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Durasi survei: {durasi}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Catatan: {catatan_hk}</p>', unsafe_allow_html=True)
                
        with c2.container(border=True):
            fig_hk_1, fig_pie_hk_1, agg_data = chart_stats(df_stats=df_stats, df_base=df_base, kode_lokasi=last_object_clicked_tooltip, filter_sheet="HK_Arah-1", fig_title="Fluktuasi Volume Kendaraan - Satu Arah (Arah-1)")
            st.plotly_chart(fig_hk_1, use_container_width=True, key=f"{key}_fig_hk_1")
            st.plotly_chart(fig_pie_hk_1, use_container_width=True, key=f"{key}_fig_pie_hk_1")
            
            with st.container(border=True, height=300):
                st.markdown(f'<p style="font-size: 16px; text-decoration: underline;">Total Volume Kendaraan {durasi} - Satu arah</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Tanpa motor: {agg_data.get("total_tanpa_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Dengan motor: {agg_data.get("total_dengan_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Nama ruas jalan: {nama_ruas_jalan}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Hari, tanggal: {hari_tanggal_hk}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Arah Dari: {arah_dari}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Arah Menuju: {arah_menuju}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Jam puncak: {jam_puncak_arah_1_hk}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Vol. jam Puncak: {vol_jam_puncak_arah_1_hk} smp/jam</p>', unsafe_allow_html=True)
                
            
        with c3.container(border=True):
            fig_hk_2, fig_pie_hk_2, agg_data = chart_stats(df_stats=df_stats, df_base=df_base, kode_lokasi=last_object_clicked_tooltip, filter_sheet="HK_Arah-2", fig_title="Fluktuasi Volume Kendaraan - Satu Arah (Arah-2)")
            st.plotly_chart(fig_hk_2, use_container_width=True, key=f"{key}_fig_hk_2")
            
            st.plotly_chart(fig_pie_hk_2, use_container_width=True, key=f"{key}_fig_pie_hk_2")
            
            with st.container(border=True, height=300):
                st.markdown(f'<p style="font-size: 16px; text-decoration: underline;">Total Volume Kendaraan {durasi} - Satu arah</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Tanpa motor: {agg_data.get("total_tanpa_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Dengan motor: {agg_data.get("total_dengan_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Nama ruas jalan: {nama_ruas_jalan}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Hari, tanggal: {hari_tanggal_hk}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Arah Dari: {arah_menuju}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Arah Menuju: {arah_dari}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Jam puncak: {jam_puncak_arah_2_hk}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Vol. jam Puncak: {vol_jam_puncak_arah_2_hk} smp/jam</p>', unsafe_allow_html=True)
                
        
        st.markdown(f"<h1 style='text-align: center; color: black;'>Profil Hari Libur - {last_object_clicked_tooltip}</h1>", unsafe_allow_html=True)
        st.write("---")
        c1, c2, c3 = st.columns([1,1,1])
        with c1.container(border=True):
            fig_hl, fig_pie_hl, agg_data = chart_stats(df_stats=df_stats, df_base=df_base, kode_lokasi=last_object_clicked_tooltip, filter_sheet="HL", fig_title="Fluktuasi Volume Kendaraan - Total Dua Arah")
            st.plotly_chart(fig_hl, use_container_width=True, key=f"{key}_fig_hl")
            st.plotly_chart(fig_pie_hl, use_container_width=True, key=f"{key}_fig_pie_hl")
            
            with st.container(border=True, height=300):
                st.markdown(f'<p style="font-size: 16px; text-decoration: underline;">Total Volume Kendaraan {durasi} - Dua arah</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Tanpa motor: {agg_data.get("total_tanpa_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Dengan motor: {agg_data.get("total_dengan_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Nama ruas jalan: {nama_ruas_jalan}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Hari, tanggal: {hari_tanggal_hl}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Durasi survei: {durasi}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Catatan: {catatan_hl}</p>', unsafe_allow_html=True)
                
        with c2.container(border=True):
            fig_hl_1, fig_pie_hl_1, agg_data = chart_stats(df_stats=df_stats, df_base=df_base, kode_lokasi=last_object_clicked_tooltip, filter_sheet="HL_Arah-1", fig_title="Fluktuasi Volume Kendaraan - Satu Arah (Arah-1)")
            st.plotly_chart(fig_hl_1, use_container_width=True, key=f"{key}_fig_hl_1")
            st.plotly_chart(fig_pie_hl_1, use_container_width=True, key=f"{key}_fig_pie_hl_1")
            
            with st.container(border=True, height=300):
                st.markdown(f'<p style="font-size: 16px; text-decoration: underline;">Total Volume Kendaraan {durasi} - Satu arah</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Tanpa motor: {agg_data.get("total_tanpa_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Dengan motor: {agg_data.get("total_dengan_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Nama ruas jalan: {nama_ruas_jalan}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Hari, tanggal: {hari_tanggal_hl}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Arah Dari: {arah_dari}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Arah Menuju: {arah_menuju}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Jam puncak: {jam_puncak_arah_1_hl}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Vol. jam Puncak: {vol_jam_puncak_arah_1_hl} smp/jam</p>', unsafe_allow_html=True)
                
        with c3.container(border=True):
            fig_hl_2, fig_pie_hl_2, agg_data = chart_stats(df_stats=df_stats, df_base=df_base, kode_lokasi=last_object_clicked_tooltip, filter_sheet="HL_Arah-2", fig_title="Fluktuasi Volume Kendaraan - Satu Arah (Arah-2)")
            st.plotly_chart(fig_hl_2, use_container_width=True, key=f"{key}_fig_hl_2")
            st.plotly_chart(fig_pie_hl_2, use_container_width=True, key=f"{key}_fig_pie_hl_2")
            
            with st.container(border=True, height=300):
                st.markdown(f'<p style="font-size: 16px; text-decoration: underline;">Total Volume Kendaraan {durasi} - Satu arah</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Tanpa motor: {agg_data.get("total_tanpa_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 15px;">- Dengan motor: {agg_data.get("total_dengan_sepeda_motor")} kendaraan</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Nama ruas jalan: {nama_ruas_jalan}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Hari, tanggal: {hari_tanggal_hl}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Arah Dari: {arah_menuju}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Arah Menuju: {arah_dari}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Jam puncak: {jam_puncak_arah_2_hl}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 16px;">Vol. jam Puncak: {vol_jam_puncak_arah_2_hl} smp/jam</p>', unsafe_allow_html=True)

elif tabs =='Travel Journey':
    st.header("Survei Travel Journey")
    show_travel_journey()

else:
    st.header("Survei Asal Tujuan")
    show()
    # chart_vehicle_origin_destination('RSI2')
    