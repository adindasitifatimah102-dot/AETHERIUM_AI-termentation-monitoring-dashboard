import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time
from datetime import datetime

# ==================== KONFIGURASI VISUAL ====================
st.set_page_config(page_title="AETHERIUM_AI Dashboard", layout="wide")

# CSS Diperbarui agar warna kotak metric muncul sesuai permintaan
st.markdown("""
    <style>
    .stApp { background-color: #e3f2fd !important; }
    
    /* Target spesifik untuk kotak metrik agar berwarna */
    div[data-testid="stMetricBlock"] {
        padding: 20px !important; 
        border-radius: 15px !important;
        box-shadow: 2px 4px 10px rgba(0,0,0,0.1) !important;
    }
    
    /* Warna Kotak Sesuai Urutan: Merah, Biru, Kuning, Hijau */
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stMetricBlock"] { background-color: #ff4b4b !important; }
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stMetricBlock"] { background-color: #1c83e1 !important; }
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stMetricBlock"] { background-color: #faca2b !important; }
    div[data-testid="column"]:nth-of-type(4) div[data-testid="stMetricBlock"] { background-color: #29b045 !important; }
    
    /* Warna teks: Putih untuk background gelap, Hitam untuk Kuning */
    div[data-testid="column"]:nth-of-type(1) *, 
    div[data-testid="column"]:nth-of-type(2) *, 
    div[data-testid="column"]:nth-of-type(4) * { color: white !important; }
    div[data-testid="column"]:nth-of-type(3) * { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# ==================== DATA & MQTT REAL-TIME ====================
if 'history' not in st.session_state:
    # Menginisialisasi dataframe kosong untuk grafik
    st.session_state.history = pd.DataFrame(columns=["Waktu", "Suhu", "Kelembaban"])

if 'status' not in st.session_state:
    st.session_state.status = {"temp": 0.0, "hum": 0.0, "mode": "NONE", "range": "0-0"}

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        temp = data.get("temperature", 0.0)
        hum = data.get("humidity", 0.0)
        
        # Update status metrik
        st.session_state.status.update({
            "temp": temp,
            "hum": hum,
            "mode": data.get("mode", "NONE"),
            "range": f"{data.get('target_min', 0)}-{data.get('target_max', 0)} °C"
        })
        
        # Tambahkan data ke history untuk Grafik
        now = datetime.now().strftime("%H:%M:%S")
        new_row = pd.DataFrame([{"Waktu": now, "Suhu": temp, "Kelembaban": hum}])
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True).tail(20)
    except Exception as e:
        print(f"Error parsing data: {e}")

@st.cache_resource
def start_mqtt():
    c = mqtt.Client()
    c.on_message = on_message
    c.connect("broker.hivemq.com", 1883, 60)
    c.subscribe("sic/dibimbing/AETHERIUM_AI/FAKHRI_MAULANA_SUBANDI/pub/dht")
    c.loop_start()
    return c

mqtt_client = start_mqtt()

# ==================== UI DASHBOARD ====================
# Baris Judul & Waktu Real-time
c_title, c_time = st.columns([3, 1])
with c_title:
    # JUDUL LENGKAP: AETHERIUM_AI Fermentation Monitoring Dashboard
    st.title("🌡️ AETHERIUM_AI Fermentation Monitoring Dashboard")
with c_time:
    st.metric("Waktu Real-time", datetime.now().strftime("%H:%M:%S"))

# Baris Metrik Berwarna
m1, m2, m3, m4 = st.columns(4)
m1.metric("Temperature", f"{st.session_state.status['temp']} °C")
m2.metric("Humidity", f"{st.session_state.status['hum']} %")
m3.metric("Mode", st.session_state.status['mode'])
m4.metric("Target Range", st.session_state.status['range'])

st.markdown("---")

col_graph, col_ctrl = st.columns([2, 1])

with col_graph:
    st.subheader("Sensor Charts (Real-time)")
    # Grafik akan muncul secara otomatis jika data MQTT masuk
    if not st.session_state.history.empty:
        st.line_chart(st.session_state.history.set_index("Waktu"))
    else:
        st.info("Menunggu kiriman data dari sensor untuk menampilkan grafik...")

with col_ctrl:
    st.subheader("Control Panel")
    menu_mode = {
        "--- Pilih Mode ---": None,
        "🍞 Roti (Fermentasi Roti)": "ROTI",
        "🍺 Bir (Fermentasi Bir)": "BIR",
        "🌶️ Tempe (Fermentasi Kedelai)": "TEMPE",
        "🥣 Yoghurt (Fermentasi Susu)": "YOGHURT"
    }
    
    selected = st.selectbox("PILIH MODE FERMENTASI:", list(menu_mode.keys()))
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 AKTIFKAN MODE") and menu_mode[selected]:
            mqtt_client.publish("sic/dibimbing/AETHERIUM_AI/FAKHRI_MAULANA_SUBANDI/sub/led", menu_mode[selected])
            st.success(f"Mode {selected} Dikirim!")
    
    with col_btn2:
        if st.button("🛑 STOP SISTEM"):
            mqtt_client.publish("sic/dibimbing/AETHERIUM_AI/FAKHRI_MAULANA_SUBANDI/sub/led", "STOP")
            st.warning("Sistem Berhenti.")

# Auto-refresh halaman setiap 1 detik agar waktu & grafik bergerak
time.sleep(1)
st.rerun()