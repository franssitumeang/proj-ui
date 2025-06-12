import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
# from utils.util import engine, read_database
import pandas as pd
import numpy as np


@st.cache_data
def get_data_vehicle_type():
    # query = """
    #     select
    #         upper(kode_titik) as kode_titik,
    #         case
    #             when jenis in ('Angkot', 'angkot') then 'Angkot'
    #             when jenis in ('Bis B', 'bisbesar') then 'Bus Besar'
    #             when jenis in ('Bis K', 'bissedang') then 'Bus Kecil'
    #             when jenis in ('Pick Up', 'pickup') then 'Pick Up/Box'
    #             when jenis in ('Truk 2G', 'truk2gandar') then 'Truk 2 Gandar'
    #             when jenis in ('Truk 3G', 'truk3gandar') then 'Truk 3 Gandar'
    #             when jenis in ('Truk 4G', 'truk4gandar') then 'Truk 4 Gandar'
    #             when jenis in ('Truk 5G', 'truk5gandar') then 'Truk 5 Gandar'
    #             when jenis in ('mobilpribadi', 'Mobil') then 'Mobil Pribadi'
    #             when jenis in ('motor', 'Motor') then 'Sepeda Motor'
    #         end as jenis,
    #         count(1) as count_vehicle
    #     from survey_asal_tujuan
    #     group by jenis,
    #         kode_titik
    #     order by jenis, kode_titik
    #     ;
    # """
    # df = read_database(engine=engine, query=query)
    return pd.read_pickle("data/origin_destination_vehicle_type_.pkl")

@st.cache_data
def get_data_origin_dest_agg():
    # query = """
    #     with
    #     grouping_data as (
    #         select
    #             kode_titik,
    #             case
    #                 when asal_tempat in ('-', '0') then 'Tempat Tidak Diketahui'
    #                 when asal_tempat in ('tempatkerja') then 'Tempat Kerja'
    #                 when asal_tempat in ('tempatpendidikan') then 'Tempat Pendidikan'
    #                 when asal_tempat in ('tempatperbelanjaan') then 'Tempat Perbelanjaan'
    #                 when asal_tempat in ('tempatrekreasi') then 'Tempat Rekreasi'
    #                 when asal_tempat in ('tempattinggal') then 'Tempat Tinggal'
    #                 when asal_tempat in ('tempatusaha') then 'Tempat Usaha'
    #             end as asal_tempat,
    #             case
    #                 when tujuan_tempat in ('-', '0') then 'Tempat Tidak Diketahui'
    #                 when tujuan_tempat in ('tempatkerja') then 'Tempat Kerja'
    #                 when tujuan_tempat in ('tempatpendidikan') then 'Tempat Pendidikan'
    #                 when tujuan_tempat in ('tempatperbelanjaan') then 'Tempat Perbelanjaan'
    #                 when tujuan_tempat in ('tempatrekreasi') then 'Tempat Rekreasi'
    #                 when tujuan_tempat in ('tempattinggal') then 'Tempat Tinggal'
    #                 when tujuan_tempat in ('tempatusaha') then 'Tempat Usaha'
    #             end as tujuan_tempat,
    #             upper(trim(asal_kab_kota)) as asal_kab_kota_original,
    #             upper(trim(tujuan_kab_kota)) as tujuan_kab_kota_original,
    #             case
    #                 when upper(trim(asal_kab_kota)) in ('BALI', 'BANDAR LAMPUNG', 'BENGKULU', 'JAMBI', 'LAMPUNG', 'RIAU',
    #                                     'SUMATERA BARAT', 'SUMATERA SELATAN', 'SUMATERA UTARA', 'KALIMANTAN TENGAH',
    #                                     'SULAWESI SELATAN', 'BALIKPAPAN', 'NUSA TENGGARA BARAT', 'KALIMANTAN SELATAN',
    #                                     'KALIMANTAN TENGAH', 'KAB. BULELENG') then 'EKSTERNAL'
    #                 else REPLACE(asal_kab_kota, 'KAB. ', '')
    #             end as asal_kab_kota,
    #             case
    #             when upper(trim(tujuan_kab_kota)) in ('BALI', 'BANDAR LAMPUNG', 'BENGKULU', 'JAMBI', 'LAMPUNG', 'RIAU',
    #                                 'SUMATERA BARAT', 'SUMATERA SELATAN', 'SUMATERA UTARA', 'KALIMANTAN TENGAH',
    #                                 'SULAWESI SELATAN', 'BALIKPAPAN', 'NUSA TENGGARA BARAT', 'KALIMANTAN SELATAN',
    #                                 'KALIMANTAN TENGAH', 'ACEH', 'KOTA MEDAN', 'IKN', 'KOTA PALEMBANG',
    #                                 'BANGKA BELITUNG', 'KOTA PEKANBARU', 'NUSA TENGGARA TIMUR', 'KAB. LAMPUNG SELATAN',
    #                                 'KAB. LAMPUNG BARAT', 'KOTA DENPASAR', 'KOTA MATARAM', 'KAB. SUMBAWA', 'KAB. SIAK',
    #                                 'KOTA PAGAR ALAM') then 'EKSTERNAL'
    #             else REPLACE(tujuan_kab_kota, 'KAB. ', '')
    #             end as tujuan_kab_kota,
    #             r_asal.latitude as asal_latitude,
    #             r_asal.longitude as asal_longitude,
    #             r_tujuan.latitude as tujuan_latitude,
    #             r_tujuan.longitude as tujuan_longitude
    #         from survey_asal_tujuan s
    #         left join regencies r_asal
    #         on REPLACE(upper(REPLACE(upper(s.asal_kab_kota), 'ADM. ', '')), 'KAB. ', 'KABUPATEN ') = r_asal.name
    #         left join regencies r_tujuan
    #         on REPLACE(upper(REPLACE(upper(s.tujuan_kab_kota), 'ADM. ', '')), 'KAB. ', 'KABUPATEN ') = r_tujuan.name
    #     ),
    #     agg_data as (
    #         select
    #             upper(kode_titik) as kode_titik,
    #             COUNT(1) OVER (PARTITION BY kode_titik) AS count_data,
    #             COUNT(1) OVER (PARTITION BY kode_titik, asal_tempat) AS count_origin,
    #             COUNT(1) OVER (PARTITION BY kode_titik, tujuan_tempat) AS count_dest,
    #             COUNT(1) OVER (PARTITION BY kode_titik, asal_tempat, tujuan_tempat) AS count_origin_dest,
    #             COUNT(1) OVER (PARTITION BY kode_titik, asal_kab_kota, tujuan_kab_kota) AS count_origin_dest_kab_kota,
    #             asal_tempat,
    #             tujuan_tempat,
    #             asal_kab_kota,
    #             asal_kab_kota_original,
    #             tujuan_kab_kota,
    #             tujuan_kab_kota_original,
    #             asal_latitude,
    #             asal_longitude,
    #             tujuan_latitude,
    #             tujuan_longitude
    #     from grouping_data
    # )

    # select
    #     distinct
    #     upper(kode_titik) as kode_titik,
    #     asal_tempat,
    #     ROUND(((count_origin::float / count_data::float) * 100)::numeric, 2) as precentage_asal_tempat,
    #     tujuan_tempat,
    #     ROUND(((count_dest::float / count_data::float) * 100)::numeric, 2) as precentage_tujuan_tempat,
    #     asal_kab_kota,
    #     tujuan_kab_kota,
    #     count_origin_dest_kab_kota as _count_origin_dest_kab_kota,
    #     case
    #         when count_origin_dest_kab_kota <= 10 then 10
    #         when count_origin_dest_kab_kota > 10 and count_origin_dest_kab_kota <= 20 then 20
    #         when count_origin_dest_kab_kota > 20 and count_origin_dest_kab_kota <= 30 then 30
    #         when count_origin_dest_kab_kota > 30 and count_origin_dest_kab_kota <= 40 then 40
    #         when count_origin_dest_kab_kota > 40 and count_origin_dest_kab_kota <= 50 then 50
    #         when count_origin_dest_kab_kota > 50 and count_origin_dest_kab_kota <= 60 then 60
    #         when count_origin_dest_kab_kota > 60 and count_origin_dest_kab_kota <= 70 then 70
    #         when count_origin_dest_kab_kota > 70 and count_origin_dest_kab_kota <= 80 then 80
    #         when count_origin_dest_kab_kota > 80 and count_origin_dest_kab_kota <= 90 then 90
    #         when count_origin_dest_kab_kota > 90 and count_origin_dest_kab_kota <= 100 then 100
    #         when count_origin_dest_kab_kota > 100 and count_origin_dest_kab_kota <= 500 then 500
    #         when count_origin_dest_kab_kota > 500 and count_origin_dest_kab_kota <= 1000 then 1000
    #         when count_origin_dest_kab_kota > 1000 and count_origin_dest_kab_kota <= 1500 then 1500
    #         when count_origin_dest_kab_kota > 1500 and count_origin_dest_kab_kota <= 2000 then 2000
    #     end count_origin_dest_kab_kota,
    #     case
    #         when asal_kab_kota_original in ('BANDAR LAMPUNG', 'BENGKULU', 'JAMBI', 'LAMPUNG', 'RIAU', 'SUMATERA BARAT',
    #                 'SUMATERA SELATAN', 'SUMATERA UTARA', 'ACEH', 'BANGKA BELITUNG', 'KAB. LAMPUNG BARAT',
    #                 'KAB. LAMPUNG SELATAN', 'KAB. SIAK', 'KOTA MEDAN', 'KOTA PAGAR ALAM', 'KOTA PALEMBANG',
    #                 'KOTA PEKANBARU') then -5.933002183915104
    #         WHEN asal_kab_kota_original in ('BALI', 'KAB. BULELENG', 'NUSA TENGGARA BARAT', 'KAB. SUMBAWA', 'KOTA DENPASAR',
    #                 'KOTA MATARAM', 'NUSA TENGGARA BARAT', 'NUSA TENGGARA TIMUR') then -8.142900298290554
    #         WHEN asal_kab_kota_original in ('IKN', 'KALIMANTAN SELATAN', 'BALIKPAPAN', 'KALIMANTAN TENGAH',
    #                 'SULAWESI SELATAN') then -7.219475761110419
    #         WHEN asal_kab_kota_original in ('KAB. ADM. KEP. SERIBU') then -6.1049698996928985
    #         else asal_latitude
    #     end as asal_latitude,
    #     case
    #         when asal_kab_kota_original in ('BANDAR LAMPUNG', 'BENGKULU', 'JAMBI', 'LAMPUNG', 'RIAU', 'SUMATERA BARAT',
    #                 'SUMATERA SELATAN', 'SUMATERA UTARA', 'ACEH', 'BANGKA BELITUNG', 'KAB. LAMPUNG BARAT',
    #                 'KAB. LAMPUNG SELATAN', 'KAB. SIAK', 'KOTA MEDAN', 'KOTA PAGAR ALAM', 'KOTA PALEMBANG',
    #                 'KOTA PEKANBARU') then 105.99945230749717
    #         WHEN asal_kab_kota_original in ('BALI', 'KAB. BULELENG', 'NUSA TENGGARA BARAT', 'KAB. SUMBAWA', 'KOTA DENPASAR',
    #                 'KOTA MATARAM', 'NUSA TENGGARA BARAT', 'NUSA TENGGARA TIMUR') then 114.40067867683435
    #         WHEN asal_kab_kota_original in ('IKN', 'KALIMANTAN SELATAN', 'BALIKPAPAN', 'KALIMANTAN TENGAH',
    #                 'SULAWESI SELATAN') then 112.7359184414066
    #         WHEN asal_kab_kota_original in ('KAB. ADM. KEP. SERIBU') then 106.77171544080802
    #         else asal_longitude
    #     end as asal_longitude,
    #     case
    #     when tujuan_kab_kota_original in ('BANDAR LAMPUNG', 'BENGKULU', 'JAMBI', 'LAMPUNG', 'RIAU', 'SUMATERA BARAT',
    #                 'SUMATERA SELATAN', 'SUMATERA UTARA', 'ACEH', 'BANGKA BELITUNG', 'KAB. LAMPUNG BARAT',
    #                 'KAB. LAMPUNG SELATAN', 'KAB. SIAK', 'KOTA MEDAN', 'KOTA PAGAR ALAM', 'KOTA PALEMBANG',
    #                 'KOTA PEKANBARU') then -5.933002183915104
    #         WHEN tujuan_kab_kota_original in ('BALI', 'KAB. BULELENG', 'NUSA TENGGARA BARAT', 'KAB. SUMBAWA', 'KOTA DENPASAR',
    #                 'KOTA MATARAM', 'NUSA TENGGARA BARAT', 'NUSA TENGGARA TIMUR') then -8.142900298290554
    #         WHEN tujuan_kab_kota_original in ('IKN', 'KALIMANTAN SELATAN', 'BALIKPAPAN', 'KALIMANTAN TENGAH',
    #                 'SULAWESI SELATAN') then -7.219475761110419
    #         WHEN tujuan_kab_kota_original in ('KAB. ADM. KEP. SERIBU') then -6.1049698996928985
    #         else tujuan_latitude
    #     end as tujuan_latitude,
    #     case
    #         when tujuan_kab_kota_original in ('BANDAR LAMPUNG', 'BENGKULU', 'JAMBI', 'LAMPUNG', 'RIAU', 'SUMATERA BARAT',
    #                 'SUMATERA SELATAN', 'SUMATERA UTARA', 'ACEH', 'BANGKA BELITUNG', 'KAB. LAMPUNG BARAT',
    #                 'KAB. LAMPUNG SELATAN', 'KAB. SIAK', 'KOTA MEDAN', 'KOTA PAGAR ALAM', 'KOTA PALEMBANG',
    #                 'KOTA PEKANBARU') then 105.99945230749717
    #         WHEN tujuan_kab_kota_original in ('BALI', 'KAB. BULELENG', 'NUSA TENGGARA BARAT', 'KAB. SUMBAWA', 'KOTA DENPASAR',
    #                 'KOTA MATARAM', 'NUSA TENGGARA BARAT', 'NUSA TENGGARA TIMUR') then 114.40067867683435
    #         WHEN tujuan_kab_kota_original in ('IKN', 'KALIMANTAN SELATAN', 'BALIKPAPAN', 'KALIMANTAN TENGAH',
    #                 'SULAWESI SELATAN') then 112.7359184414066
    #         WHEN tujuan_kab_kota_original in ('KAB. ADM. KEP. SERIBU') then 106.77171544080802
    #         else tujuan_longitude
    #     end as tujuan_longitude
    # from agg_data
    # order by kode_titik, asal_tempat
    # ;
    # """
    # df = read_database(engine=engine, query=query)
    return pd.read_pickle("data/origin_destination_agg.pkl")


df_vehicle_type = get_data_vehicle_type()
df_origin_dest_agg = get_data_origin_dest_agg()
vehicle_type = df_vehicle_type["_jenis"].unique()
kode_titik = df_vehicle_type["kode_titik"].unique()

def chart_vehicle_origin_destination(kode_titik):
    df_vehicle_type_selected = df_vehicle_type.loc[df_vehicle_type['kode_titik'] == kode_titik]
    df_origin_dest_agg_selected = df_origin_dest_agg.loc[df_origin_dest_agg['kode_titik'] == kode_titik]
    df_origin_dest_map_line = df_origin_dest_agg_selected
    # df_origin_dest_map_line = df_origin_dest_agg_selected.loc[(df_origin_dest_agg_selected['asal_kab_kota'] != 'EKSTERNAL') & (df_origin_dest_agg_selected['tujuan_kab_kota'] != 'EKSTERNAL')]
    values_vehicle_type = []
    for _type in vehicle_type:
        values_vehicle_type.append(int(df_vehicle_type_selected.loc[df_vehicle_type_selected['_jenis'] == _type, 'count_vehicle'].iloc[0]) if _type in df_vehicle_type_selected["_jenis"].values else 0)
    
    origin = []
    destination = []
    percentage_origin_dest_kab_kota = []
    origin_kab_kota = []
    dest_kab_kota = []
    
    concatenated_origin_dest_kab_kota = []
    for idx, row in df_origin_dest_agg_selected.iterrows():
        origin.append(row["asal_tempat"])
        destination.append(row["tujuan_tempat"])
        concatenated_origin_dest_kab_kota.append(f'{row["asal_kab_kota"]}|{row["tujuan_kab_kota"]}|{row["_count_origin_dest_kab_kota"]}')
        
    concatenated_origin_dest_kab_kota = list(set(concatenated_origin_dest_kab_kota))
    for d in concatenated_origin_dest_kab_kota:
        data = str(d).split('|')
        origin_kab_kota.append(data[0])
        dest_kab_kota.append(data[1])
        percentage_origin_dest_kab_kota.append(int(data[2]))
        
    concatenated_origin_dest_lat_long = []
    for idx, row in df_origin_dest_map_line.iterrows():
        concatenated_origin_dest_lat_long.append(f'{row["asal_latitude"]}|{row["asal_longitude"]}|{row["tujuan_latitude"]}|{row["tujuan_longitude"]}|{row["count_origin_dest_kab_kota"]}|{row["asal_kab_kota"]}|{row["tujuan_kab_kota"]}')
    concatenated_origin_dest_lat_long = list(set(concatenated_origin_dest_lat_long))
    
    asal_latitude = []
    asal_longitude = []
    tujuan_latitude = []
    tujuan_longitude = []
    weight = []
    _asal_kab_kota = []
    _tujuan_kab_kota = []
    for d in concatenated_origin_dest_lat_long:
        data = str(d).split('|')
        asal_latitude.append(float(data[0]))
        asal_longitude.append(float(data[1]))
        tujuan_latitude.append(float(data[2]))
        tujuan_longitude.append(float(data[3]))
        weight.append(int(data[4]))
        _asal_kab_kota.append(data[5])
        _tujuan_kab_kota.append(data[6])
    
    df_map_line =  pd.DataFrame({
        'asal_latitude': asal_latitude,
        'asal_longitude': asal_longitude,
        'tujuan_latitude': tujuan_latitude,
        'tujuan_longitude': tujuan_longitude,
        'weight': weight,
        '_asal_kab_kota': _asal_kab_kota,
        '_tujuan_kab_kota': _tujuan_kab_kota,
    })
    
    data_matrix_origin = {
        'Asal Perjalanan': list(set(origin)),
        'Persentase': [df_origin_dest_agg_selected.loc[df_origin_dest_agg_selected['asal_tempat'] == x, 'precentage_asal_tempat'].iloc[0] for x in list(set(origin))]
    }
    data_matrix_dest = {
        'Tujuan Perjalanan': list(set(destination)),
        'Persentase': [df_origin_dest_agg_selected.loc[df_origin_dest_agg_selected['tujuan_tempat'] == x, 'precentage_tujuan_tempat'].iloc[0] for x in list(set(destination))]
    }
        
    data_matrix_origin_dest = {
        "Asal": origin_kab_kota,
        "Tujuan": dest_kab_kota,
        "Persentase": percentage_origin_dest_kab_kota
    }
    df_matrix_origin_dest = pd.DataFrame(data_matrix_origin_dest)

    pivot_matrix_origin_dest = df_matrix_origin_dest.pivot(index="Tujuan", columns="Asal", values="Persentase").fillna(0)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        fig_vehicle_type = go.Figure()
        
        for i, category in enumerate(vehicle_type):
            fig_vehicle_type.add_trace(go.Bar(
                x=[category],
                y=[values_vehicle_type[i]],
                text=values_vehicle_type[i],
                textposition='outside',
            ))

        fig_vehicle_type.update_layout(
            title_text="Jumlah Responden berdasarkan Jenis Kendaraan",
            xaxis_title="Jenis Kendaraan",
            yaxis_title="Jumlah",
            showlegend=False
        )

        st.plotly_chart(fig_vehicle_type)
        
    with col2:
        fig_matrix_origin = px.pie(
            data_matrix_origin,
            names='Asal Perjalanan',
            values='Persentase',
            title='Persentase Responden berdasarkan Jenis Asal perjalanan',
            hole=0
        )

        fig_matrix_origin.update_traces(textposition='outside', textinfo='percent+label')
        fig_matrix_origin.update_layout(
            showlegend=True,
            legend_title_text=None,
            margin=dict(t=100, b=100, l=100, r=100),
            font=dict(size=9.5),
        )
        st.plotly_chart(fig_matrix_origin)
        
    with col3:
        fig_matrix_dest = px.pie(
            data_matrix_dest,
            names='Tujuan Perjalanan',
            values='Persentase',
            title='Persentase Responden berdasarkan Jenis Tujuan perjalanan',
            hole=0
        )

        fig_matrix_dest.update_traces(textposition='outside', textinfo='percent+label')
        fig_matrix_dest.update_layout(
            showlegend=True,
            legend_title_text=None,
            margin=dict(t=100, b=100, l=100, r=100),
            font=dict(size=9.5),
        )
        st.plotly_chart(fig_matrix_dest)
    
    with st.container(border=True):
        fig_matrix_origin_dest = px.imshow(pivot_matrix_origin_dest, text_auto=True, aspect="auto", color_continuous_scale="Blues")
        fig_matrix_origin_dest.update_traces(
            hovertemplate="Dari <b>%{y}</b> ke <b>%{x}</b>: <b>%{z}</b><extra></extra>"
        )
        fig_matrix_origin_dest.update_layout(title="Matriks Asal Tujuan Perjalanan", xaxis_title="Tujuan", yaxis_title="Asal", height=900)

        st.plotly_chart(fig_matrix_origin_dest)
        
    with st.container(border=True):
        fig_map_line = px.scatter_mapbox(
            data_frame=df_map_line,
            lat=[*df_map_line['asal_latitude'], *df_map_line['tujuan_latitude']],
            lon=[*df_map_line['asal_longitude'], *df_map_line['tujuan_longitude']],
            hover_name=[*df_map_line['_asal_kab_kota'], *df_map_line['_tujuan_kab_kota']],
            mapbox_style="carto-positron",
            zoom=6.5,
            center={"lat": -7.5, "lon": 111.5},
            title=f"Desire Line Map {kode_titik}"
        )
        weight_flag = {}
        for i in range(len(df_map_line)):
            weight_flag[df_map_line["weight"][i]] = False if df_map_line["weight"][i] in weight_flag else True
            
            fig_map_line.add_trace(go.Scattermapbox(
                mode="lines",
                lon=[df_map_line['asal_longitude'][i], df_map_line['tujuan_longitude'][i]],
                lat=[df_map_line['asal_latitude'][i], df_map_line['tujuan_latitude'][i]],
                line=dict(width=df_map_line['weight'][i] / 20, color='blue'),
                showlegend=weight_flag[df_map_line["weight"][i]],
                name=f': {df_map_line["weight"][i]}' if weight_flag[df_map_line["weight"][i]] else None
            ))
            
        fig_map_line.update_layout(height=800)
            
        st.plotly_chart(fig_map_line)
        
    with st.container(border=True):
        data_dist_origin = {
            'latitude': asal_latitude,
            'longitude': asal_longitude,
        }
        df_dist_origin = pd.DataFrame(data_dist_origin)


        x_bins = np.linspace(df_dist_origin['longitude'].min(), df_dist_origin['longitude'].max(), 10)
        y_bins = np.linspace(df_dist_origin['latitude'].min(), df_dist_origin['latitude'].max(), 10)
        hist, x_edges, y_edges = np.histogram2d(df_dist_origin['longitude'], df_dist_origin['latitude'], bins=[x_bins, y_bins])

        density = []
        for lon, lat in zip(df_dist_origin['longitude'], df_dist_origin['latitude']):
            x_bin = min(max(np.digitize(lon, x_edges) - 1, 0), hist.shape[0] - 1)
            y_bin = min(max(np.digitize(lat, y_edges) - 1, 0), hist.shape[1] - 1)
            density.append(hist[x_bin, y_bin])

        df_dist_origin['keterangan'] = density

        fig_dist_origin = px.density_mapbox(
            df_dist_origin,
            lat="latitude",
            lon="longitude",
            z="keterangan",
            radius=10,
            center=dict(lat=-7.41278, lon=110.935),
            zoom=6,
            mapbox_style="carto-positron",
            color_continuous_scale="Reds"
        )

        fig_dist_origin.update_layout(
            title={
                "text": f"Sebaran Asal Perjalanan pada Lokasi {kode_titik}",
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            title_font=dict(size=20, color="black", family="Arial"),
        )
        st.plotly_chart(fig_dist_origin)
        
        # =========
        
        data_dist_dest = {
            'latitude': tujuan_latitude,
            'longitude': tujuan_longitude,
        }
        df_dist_dest = pd.DataFrame(data_dist_dest)


        x_bins = np.linspace(df_dist_dest['longitude'].min(), df_dist_dest['longitude'].max(), 10)
        y_bins = np.linspace(df_dist_dest['latitude'].min(), df_dist_dest['latitude'].max(), 10)
        hist, x_edges, y_edges = np.histogram2d(df_dist_dest['longitude'], df_dist_dest['latitude'], bins=[x_bins, y_bins])

        density = []
        for lon, lat in zip(df_dist_dest['longitude'], df_dist_dest['latitude']):
            x_bin = min(max(np.digitize(lon, x_edges) - 1, 0), hist.shape[0] - 1)
            y_bin = min(max(np.digitize(lat, y_edges) - 1, 0), hist.shape[1] - 1)
            density.append(hist[x_bin, y_bin])

        df_dist_dest['keterangan'] = density

        fig_dist_dest = px.density_mapbox(
            df_dist_dest,
            lat="latitude",
            lon="longitude",
            z="keterangan",
            radius=10,
            center=dict(lat=-7.41278, lon=110.935),
            zoom=6,
            mapbox_style="carto-positron",
            color_continuous_scale="Reds"
        )

        fig_dist_dest.update_layout(
            title={
                "text": f"Sebaran Tujuan Perjalanan pada Lokasi {kode_titik}",
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            title_font=dict(size=20, color="black", family="Arial"),
        )
        st.plotly_chart(fig_dist_dest)

        
        
def show():
    display_text_select = {
        "RSI1": "OD1",
        "RSI2": "OD2 - RSI",
        "RSI3": "OD3",
        "RSI4": "OD4 - RSI",
        "RSI5": "OD5 - RSI",
        "RSI6": "OD6",
        "RSI7": "OD7 - RSI",
        "RSI8": "OD8 - RSI",
        "RSI9": "OD9",
    }
    kode_titik_select = st.selectbox("Filter Kode Titik", sorted(kode_titik), key=f"kode_titik_select", format_func=lambda x: display_text_select[x])
    chart_vehicle_origin_destination(kode_titik_select)

