import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time
import base64
from datetime import datetime

# ==================== KONFIGURASI VISUAL ====================
st.set_page_config(page_title="AETHERIUM_AI Dashboard", layout="wide")

# Fungsi untuk membaca gambar lokal menjadi Base64 (Agar pasti muncul)
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""

# GANTI NAMA FILE DI SINI SESUAI FILE ANDA
img_base64 = get_base64_image("cendrawasih.jpeg.jpeg")

# CSS Kustom
st.markdown(f"""
    <style>
    .stApp {{ background-color: #e3f2fd !important; }}

    /* Animasi Melambai/Menyapa (Swing) */
    @keyframes waving {{
        0% {{ transform: rotate(0deg); }}
        25% {{ transform: rotate(5deg); }}
        75% {{ transform: rotate(-5deg); }}
        100% {{ transform: rotate(0deg); }}
    }}

    /* Animasi Naik Turun (Bounce) */
    @keyframes bounce {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-15px); }}
    }}

    .splash-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 70vh;
    }}

    .splash-img {{
        width: 400px;
        border-radius: 30px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.2);
        animation: waving 2s ease-in-out infinite; /* Efek melambai */
    }}

    .splash-text {{
        font-family: 'Trebuchet MS', sans-serif;
        font-size: 35px;
        font-weight: bold;
        color: #1c83e1;
        margin-top: 30px;
        animation: bounce 2s infinite;
    }}

    /* Burung di Pojok Kanan */
    .pointing-bird {{
        position: fixed;
        top: 80px;
        right: 20px;
        width: 180px;
        z-index: 999;
        border-radius: 15px;
        animation: waving 3s ease-in-out infinite;
        border: 3px solid white;
    }}

    div[data-testid="stMetricBlock"] {{
        padding: 20px !important; 
        border-radius: 15px !important;
        box-shadow: 2px 4px 10px rgba(0,0,0,0.1) !important;
    }}
    
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stMetricBlock"] {{ background-color: #ff4b4b !important; }}
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stMetricBlock"] {{ background-color: #1c83e1 !important; }}
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stMetricBlock"] {{ background-color: #faca2b !important; }}
    div[data-testid="column"]:nth-of-type(4) div[data-testid="stMetricBlock"] {{ background-color: #29b045 !important; }}
    
    div[data-testid="column"]:nth-of-type(1) *, 
    div[data-testid="column"]:nth-of-type(2) *, 
    div[data-testid="column"]:nth-of-type(4) * {{ color: white !important; }}
    div[data-testid="column"]:nth-of-type(3) * {{ color: black !important; }}
    </style>
    """, unsafe_allow_html=True)

# ==================== LOGIKA SPLASH SCREEN ====================
if 'initialized' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"""
            <div class="splash-container">
                <img src="data:image/jpeg;base64,{img_base64}" class="splash-img">
                <div class="splash-text">SELAMAT DATANG DI <br> AETHERIUM CENDRAFERMA</div>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(4) 
    placeholder.empty()
    st.session_state.initialized = True

# ==================== DATA & MQTT ====================
# (Kode MQTT Anda tetap sama di bawah sini...)
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["Waktu", "Suhu", "Kelembaban"])

if 'status' not in st.session_state:
    st.session_state.status = {"temp": 0.0, "hum": 0.0, "mode": "NONE", "range": "0-0"}

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        temp = data.get("temperature", 0.0)
        hum = data.get("humidity", 0.0)
        st.session_state.status.update({
            "temp": temp, "hum": hum,
            "mode": data.get("mode", "NONE"),
            "range": f"{data.get('target_min', 0)}-{data.get('target_max', 0)} °C"
        })
        now = datetime.now().strftime("%H:%M:%S")
        new_row = pd.DataFrame([{"Waktu": now, "Suhu": temp, "Kelembaban": hum}])
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True).tail(20)
    except:
        pass

@st.cache_resource
def start_mqtt():
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.on_message = on_message
    c.connect("broker.hivemq.com", 1883, 60)
    c.subscribe("sic/dibimbing/AETHERIUM_AI/FAKHRI_MAULANA_SUBANDI/pub/dht")
    c.loop_start()
    return c

mqtt_client = start_mqtt()

# ==================== UI DASHBOARD ====================

# Menampilkan gambar melambai di pojok kanan dashboard
st.markdown(f"""
    <img src="data:image/jpeg;base64,{img_base64}" class="pointing-bird">
""", unsafe_allow_html=True)

c_title, c_time = st.columns([3, 1])
with c_title:
    st.title("🌡️ AETHERIUM_AI Monitoring Dashboard")
with c_time:
    st.metric("Waktu Real-time", datetime.now().strftime("%H:%M:%S"))

# Baris Metrik
m1, m2, m3, m4 = st.columns(4)
m1.metric("Temperature", f"{st.session_state.status['temp']} °C")
m2.metric("Humidity", f"{st.session_state.status['hum']} %")
m3.metric("Mode", st.session_state.status['mode'])
m4.metric("Target Range", st.session_state.status['range'])

st.markdown("---")

col_graph, col_ctrl = st.columns([2, 1])
with col_graph:
    st.subheader("Sensor Charts (Real-time)")
    if not st.session_state.history.empty:
        st.line_chart(st.session_state.history.set_index("Waktu"))
    else:
        st.info("Menunggu data...")

with col_ctrl:
    st.subheader("Control Panel")
    menu_mode = {"--- Pilih Mode ---": None, "🍞 Roti": "ROTI", "🍺 Bir": "BIR", "🌱 Tempe": "TEMPE", "🥣 Yoghurt": "YOGHURT"}
    selected = st.selectbox("PILIH MODE:", list(menu_mode.keys()))
    
    if st.button("🚀 AKTIFKAN") and menu_mode[selected]:
        mqtt_client.publish("sic/dibimbing/AETHERIUM_AI/FAKHRI_MAULANA_SUBANDI/sub/led", menu_mode[selected])
        st.success("Mode Terkirim!")

time.sleep(2)
st.rerun()