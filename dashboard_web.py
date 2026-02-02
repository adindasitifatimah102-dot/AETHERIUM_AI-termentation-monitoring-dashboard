import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time
import base64
from datetime import datetime
import os
from rembg import remove
from PIL import Image
import io

# ==================== 1. KONFIGURASI HALAMAN & STATE ====================
st.set_page_config(page_title="AETHERIUM_AI Dashboard", layout="wide")

if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'show_guide' not in st.session_state:
    st.session_state.show_guide = True
if 'guide_step' not in st.session_state:
    st.session_state.guide_step = 0
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["Waktu", "Suhu", "Kelembaban"])
if 'status' not in st.session_state:
    st.session_state.status = {"temp": 0.0, "hum": 0.0, "mode": "NONE", "range": "0-0"}

# ==================== 2. FUNGSI GAMBAR (DENGAN REMOVE BG) ====================
@st.cache_data
def get_processed_image(image_path, remove_bg=False):
    # Mencari lokasi folder tempat script berada agar path akurat
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, image_path)
    
    if os.path.exists(full_path):
        try:
            with open(full_path, "rb") as img_file:
                img_data = img_file.read()
                
                # --- BAGIAN PENGHAPUS LATAR BELAKANG ---
                if remove_bg:
                    try:
                        img_data = remove(img_data)
                    except Exception as e:
                        st.error(f"Gagal menghapus background: {e}")
                # ---------------------------------------

                return base64.b64encode(img_data).decode()
        except Exception as e:
            return None
    return None

# Memuat gambar aset
# img_splash biarkan False agar gambarnya utuh kotak (atau ubah True jika ingin transparan juga)
img_splash = get_processed_image("cendrawasih.jpeg", remove_bg=False) 

# Gambar karakter set ke True agar background hilang (transparan)
img_menunjuk = get_processed_image("img_menunjuk.jpeg", remove_bg=True)
img_sabar = get_processed_image("img_sabar.jpeg", remove_bg=True)
img_santun = get_processed_image("img_santun.jpeg", remove_bg=True)
img_peringatan = get_processed_image("img_peringatan.jpeg", remove_bg=True)

# ==================== 3. CSS KUSTOM (BUBBLE & ANIMASI) ====================
st.markdown("""
    <style>
    .stApp { background-color: #e3f2fd !important; }
    
    /* Animasi Mulut Bergerak */
    @keyframes talking {
        0% { transform: scaleY(1); }
        50% { transform: scaleY(1.06); }
        100% { transform: scaleY(1); }
    }
    
    /* Animasi Melayang */
    @keyframes floating {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

    /* Bubble Chat Styling */
    .bubble {
        position: fixed; bottom: 220px; right: 40px; background: white;
        border: 3px solid #1c83e1; padding: 15px; border-radius: 20px;
        max-width: 280px; z-index: 1001; font-family: 'Arial', sans-serif; 
        font-size: 15px; color: #333; font-weight: bold;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Ekor Bubble Chat */
    .bubble::after {
        content: ''; position: absolute; bottom: -15px; right: 50px;
        border-width: 15px 15px 0; border-style: solid;
        border-color: white transparent transparent;
    }

    .cendra-guide {
        position: fixed; bottom: 20px; right: 20px; width: 180px; z-index: 1000;
        transform-origin: bottom;
    }
    
    .ani-talk-float { 
        animation: talking 0.25s infinite, floating 3s ease-in-out infinite; 
    }

    .time-container {
        background: white; padding: 15px; border-radius: 10px;
        border-left: 8px solid #1c83e1; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== 4. MQTT & LOGIKA KONEKSI ====================
@st.cache_resource
def start_mqtt():
    def on_message(client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            st.session_state.status.update({
                "temp": data.get("temperature", 0.0),
                "hum": data.get("humidity", 0.0),
                "mode": data.get("mode", "NONE"),
                "range": f"{data.get('target_min', 0)}-{data.get('target_max', 0)} °C"
            })
            now = datetime.now().strftime("%H:%M:%S")
            new_row = pd.DataFrame([{"Waktu": now, "Suhu": data.get("temperature"), "Kelembaban": data.get("humidity")}])
            st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True).tail(20)
        except: pass
        
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.on_message = on_message
    try:
        c.connect("broker.hivemq.com", 1883, 60)
        c.subscribe("sic/dibimbing/AETHERIUM_AI/FAKHRI_MAULANA_SUBANDI/pub/dht")
        c.loop_start()
    except Exception as e:
        print(f"MQTT Error: {e}")
    return c

mqtt_client = start_mqtt()

# ==================== 5. SPLASH SCREEN (VERSI FIXED) ====================
if not st.session_state.initialized:
    placeholder = st.empty()
    with placeholder.container():
        # Pastikan variabel ini mengambil nama file yang benar
        # Jika di folder namanya cendrawasih.jpeg.jpeg, sesuaikan di sini
        img_splash = get_processed_image("cendrawasih.jpeg.jpeg", remove_bg=False)

        if img_splash:
            splash_html = f'<img src="data:image/jpeg;base64,{img_splash}" style="width:500px; border-radius:20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">'
        else:
            splash_html = '<h1 style="font-size:100px;">🦜</h1>'

        # KODE DI BAWAH INI HARUS DITULIS PERSIS SEPERTI INI
        # JANGAN SAMPAI ADA TANDA KUTIP YANG TERLEWAT
        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90vh; background-color: #f0f8ff; text-align: center;">
                <div style="margin-bottom: 20px;">
                    {splash_html}
                </div>
                <h1 style="color:#1c83e1; margin: 10px 0; font-family: sans-serif;">AETHERIUM_AI CENDRAFERMA</h1>
                <p style="color: #555; font-size: 18px; font-style: italic;">Memuat sistem cerdas Cendrawasih...</p>
                <div class="loader"></div>
            </div>
            <style>
                .loader {{
                    border: 5px solid #f3f3f3;
                    border-top: 5px solid #1c83e1;
                    border-radius: 50%;
                    width: 45px;
                    height: 45px;
                    animation: spin 1s linear infinite;
                    margin-top: 15px;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
            """, 
            unsafe_allow_html=True
        )
        
        time.sleep(5)
    st.session_state.initialized = True
    st.rerun()

# ==================== 6. LOGIKA PANDUAN (BUBBLE & TEKS) ====================
if st.session_state.show_guide:
    panduan_list = [
        {"img": img_menunjuk, "msg": "Halo! Aku Cendra. Klik 'Control Panel' untuk pilih mode fermentasi ya!"},
        {"img": img_santun, "msg": "Setelah pilih mode, klik '🚀 AKTIFKAN'. Aku akan bantu jaga suhunya!"},
        {"img": img_sabar, "msg": "Jika data masih 0.0, pastikan alatmu sudah terhubung ke WiFi ya! 📊"},
        {"img": img_menunjuk, "msg": "Grafik di kiri akan mencatat riwayat suhu secara otomatis setiap menit."},
        {"img": img_santun, "msg": "Gunakan tombol '🛑 STOP' jika ingin menghentikan proses fermentasi."}
    ]

    # Prioritas Bahaya Suhu Tinggi
    if st.session_state.status['temp'] > 40:
        current_img, guide_msg = img_peringatan, "Waduh! Suhunya ketinggian! Bahaya Kak, segera matikan alat! ⚠️"
    else:
        # Menentukan urutan panduan
        step = st.session_state.guide_step % len(panduan_list)
        current_img = panduan_list[step]["img"]
        guide_msg = panduan_list[step]["msg"]

    # Render Bubble Chat & Karakter (Hanya jika gambar berhasil di-load)
    if current_img:
        # Perhatikan: src menggunakan format PNG karena hasil rembg mendukung transparansi (RGBA)
        st.markdown(f"""
            <div class="bubble">{guide_msg}</div>
            <img src="data:image/png;base64,{current_img}" class="cendra-guide ani-talk-float">
        """, unsafe_allow_html=True)

# ==================== 7. UI DASHBOARD UTAMA ====================
st.title("🌡️ AETHERIUM_AI Monitoring Dashboard")

now = datetime.now()
st.markdown(f'<div class="time-container">📅 {now.strftime("%A, %d %B %Y")}<br><span style="font-size:30px; color:#1c83e1;">⏰ {now.strftime("%H:%M:%S")} WIB</span></div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Suhu", f"{st.session_state.status['temp']} °C")
m2.metric("Kelembaban", f"{st.session_state.status['hum']} %")
m3.metric("Mode Aktif", st.session_state.status['mode'])
m4.metric("Target", st.session_state.status['range'])

st.markdown("---")
col_graph, col_ctrl = st.columns([2, 1])

with col_graph:
    st.subheader("📊 Grafik Real-time")
    if not st.session_state.history.empty:
        st.line_chart(st.session_state.history.set_index("Waktu"))
    else:
        st.info("Menunggu data masuk...")

with col_ctrl:
    st.subheader("🎮 Control Panel")
    # Baris 203 yang sudah diperbaiki:
    menu_mode = {
        "--- Pilih Mode ---": None, 
        "🍞 Roti": "ROTI", 
        "🍺 Bir": "BIR", 
        "🌱 Tempe": "TEMPE", 
        "🥣 Yoghurt": "YOGHURT"
    }
    
    selected = st.selectbox("PILIH MODE:", list(menu_mode.keys()))
    
    if st.button("🚀 AKTIFKAN"):
        if menu_mode[selected]:
            mqtt_client.publish("sic/dibimbing/AETHERIUM_AI/FAKHRI_MAULANA_SUBANDI/sub/led", menu_mode[selected])
            st.success(f"Mode {selected} Aktif!")
            st.session_state.show_guide = False
            st.rerun()
        else: 
            st.error("Silakan pilih mode terlebih dahulu!")
    
    if st.button("🛑 STOP"):
        mqtt_client.publish("sic/dibimbing/AETHERIUM_AI/FAKHRI_MAULANA_SUBANDI/sub/led", "STOP")
        st.warning("Berhenti!")

    if st.button("❓ Panduan Berikutnya"):
        st.session_state.show_guide = True
        st.session_state.guide_step += 1 
        st.rerun()

time.sleep(2)
st.rerun()