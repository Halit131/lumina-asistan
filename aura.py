import os
import time
import sqlite3
import hashlib
import streamlit as st
from google import genai
from dotenv import load_dotenv
import pyttsx3

# --------------------
# SAYFA AYARI
# --------------------
st.set_page_config(
    page_title="✨ Lumina AI",
    page_icon="✨",
    layout="wide"
)

# --------------------
# SES MOTORU
# --------------------
try:
    import pyttsx3
    engine = pyttsx3.init()
except Exception as e:
    engine = None

def konus(metin):
    try:
        engine.say(metin)
        engine.runAndWait()
    except:
        pass

# --------------------
# ENV YÜKLE
# --------------------
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY bulunamadı.")
    st.stop()

client = genai.Client(api_key=api_key)

# --------------------
# SESSION
# --------------------
if "tema_rengi" not in st.session_state:
    st.session_state.tema_rengi = "#00ffcc"

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------
# CSS
# --------------------
def css_yukle(renk):

    st.markdown(f"""
    <style>

    .stApp {{
        background: #0f1117;
        color: white;
    }}

    .ana-baslik {{
        text-align:center;
        color:{renk};
        font-size:48px;
        font-weight:bold;
        margin-bottom:10px;
        text-shadow:0 0 20px {renk};
    }}

    .neon-cizgi {{
        height:2px;
        background:{renk};
        margin-bottom:20px;
    }}

    </style>
    """,
    unsafe_allow_html=True)

css_yukle(st.session_state.tema_rengi)# --------------------
# VERİTABANI
# --------------------

def veritabanini_hazirla():

    conn = sqlite3.connect("lumina.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        role TEXT,
        content TEXT
    )
    """)

    conn.commit()

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        ("admin",)
    )

    if not cursor.fetchone():

        sifre = hashlib.sha256(
            "1234".encode()
        ).hexdigest()

        cursor.execute(
            "INSERT INTO users VALUES (?, ?)",
            ("admin", sifre)
        )

        conn.commit()

    conn.close()

veritabanini_hazirla()


# --------------------
# KULLANICI EKLE
# --------------------

def kullanici_ekle(
    username,
    password
):

    conn = sqlite3.connect("lumina.db")
    cursor = conn.cursor()

    try:

        sifre = hashlib.sha256(
            password.encode()
        ).hexdigest()

        cursor.execute(
            "INSERT INTO users VALUES (?, ?)",
            (username, sifre)
        )

        conn.commit()

        return True

    except:

        return False

    finally:

        conn.close()


# --------------------
# KULLANICI KONTROL
# --------------------

def kullanici_kontrol(
    username,
    password
):

    conn = sqlite3.connect("lumina.db")
    cursor = conn.cursor()

    sifre = hashlib.sha256(
        password.encode()
    ).hexdigest()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username=?
        AND password=?
        """,
        (
            username,
            sifre
        )
    )

    sonuc = cursor.fetchone()

    conn.close()

    return sonuc is not None


# --------------------
# MESAJ KAYDET
# --------------------

def mesaj_kaydet(
    username,
    role,
    content
):

    conn = sqlite3.connect("lumina.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chat_history
        (
            username,
            role,
            content
        )
        VALUES
        (?, ?, ?)
        """,
        (
            username,
            role,
            content
        )
    )

    conn.commit()
    conn.close()


# --------------------
# GEÇMİŞ YÜKLE
# --------------------

def gecmisi_yukle(
    username
):

    conn = sqlite3.connect("lumina.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, content
        FROM chat_history
        WHERE username=?
        ORDER BY id
        """,
        (username,)
    )

    veriler = cursor.fetchall()

    conn.close()

    return [
        {
            "role": v[0],
            "content": v[1]
        }
        for v in veriler
    ]


# --------------------
# GEÇMİŞİ TEMİZLE
# --------------------

def gecmisi_sil(
    username
):

    conn = sqlite3.connect("lumina.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE
        FROM chat_history
        WHERE username=?
        """,
        (username,)
    )

    conn.commit()
    conn.close()# --------------------
# GİRİŞ EKRANI
# --------------------

if not st.session_state.giris_yapildi:

    st.markdown(
        '<div class="ana-baslik">✨ LUMINA AI ✨</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="neon-cizgi"></div>',
        unsafe_allow_html=True
    )

    giris_tab, kayit_tab = st.tabs(
        [
            "🔐 Giriş Yap",
            "📝 Hesap Oluştur"
        ]
    )

    # ----------------
    # GİRİŞ
    # ----------------

    with giris_tab:

        with st.form("giris_formu"):

            kullanici = st.text_input(
                "Kullanıcı Adı"
            )

            sifre = st.text_input(
                "Şifre",
                type="password"
            )

            giris = st.form_submit_button(
                "Lumina'ya Bağlan"
            )

            if giris:

                if kullanici_kontrol(
                    kullanici,
                    sifre
                ):

                    st.session_state.giris_yapildi = True

                    st.session_state.aktif_kullanici = kullanici

                    st.session_state.messages = gecmisi_yukle(
                        kullanici
                    )

                    st.rerun()

                else:

                    st.error(
                        "Kullanıcı adı veya şifre hatalı."
                    )

    # ----------------
    # KAYIT
    # ----------------

    with kayit_tab:

        with st.form("kayit_formu"):

            yeni_kullanici = st.text_input(
                "Yeni Kullanıcı Adı"
            )

            yeni_sifre = st.text_input(
                "Yeni Şifre",
                type="password"
            )

            kayit = st.form_submit_button(
                "Hesap Oluştur"
            )

            if kayit:

                if (
                    yeni_kullanici
                    and
                    yeni_sifre
                ):

                    if kullanici_ekle(
                        yeni_kullanici,
                        yeni_sifre
                    ):

                        st.success(
                            "Hesap oluşturuldu."
                        )

                    else:

                        st.error(
                            "Bu kullanıcı adı zaten var."
                        )

                else:

                    st.warning(
                        "Boş alan bırakma."
                    )

    st.stop()# --------------------
# ANA EKRAN
# --------------------

st.markdown(
    '<div class="ana-baslik">✨ LUMINA AI ✨</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="neon-cizgi"></div>',
    unsafe_allow_html=True
)

# --------------------
# SIDEBAR
# --------------------

st.sidebar.title("⚙️ Lumina Panel")

st.sidebar.write(
    f"👤 {st.session_state.aktif_kullanici}"
)

st.sidebar.write(
    f"💬 Mesaj Sayısı: {len(st.session_state.messages)}"
)

# --------------------
# MODEL SEÇİMİ
# --------------------

model_sec = st.sidebar.selectbox(
    "🧠 Model",
    [
        "gemini-2.5-flash",
        "gemini-2.5-pro"
    ]
)

# --------------------
# MOD SEÇİMİ
# --------------------

ai_modu = st.sidebar.selectbox(
    "🎭 Mod",
    [
        "Standart",
        "Yazılım Mentörü",
        "Dert Ortağı"
    ]
)

modlar = {

    "Standart":
    "Sen Lumina isimli yardımcı bir yapay zekasın.",

    "Yazılım Mentörü":
    """
    Sen uzman bir yazılım eğitmenisin.
    Kod örnekleri ver.
    Python öğret.
    """,

    "Dert Ortağı":
    """
    Samimi ve destekleyici ol.
    Nazik cevaplar ver.
    """
}

# --------------------
# SESLİ CEVAP
# --------------------

sesli_mod = st.sidebar.checkbox(
    "🔊 Sesli Cevap",
    value=False
)

# --------------------
# RENK SEÇİMİ
# --------------------

yeni_renk = st.sidebar.color_picker(
    "🎨 Tema Rengi",
    st.session_state.tema_rengi
)

if yeni_renk != st.session_state.tema_rengi:

    st.session_state.tema_rengi = yeni_renk

    st.rerun()

# --------------------
# GEÇMİŞİ TEMİZLE
# --------------------

if st.sidebar.button(
    "🗑️ Geçmişi Temizle"
):

    gecmisi_sil(
        st.session_state.aktif_kullanici
    )

    st.session_state.messages = []

    st.rerun()

# --------------------
# SOHBETİ İNDİR
# --------------------

sohbet_metni = ""

for mesaj in st.session_state.messages:

    sohbet_metni += (
        f"{mesaj['role']}: "
        f"{mesaj['content']}\n\n"
    )

st.sidebar.download_button(

    label="📥 Sohbeti İndir",

    data=sohbet_metni,

    file_name="lumina_sohbet.txt",

    mime="text/plain"
)

# --------------------
# GÜVENLİ ÇIKIŞ
# --------------------

if st.sidebar.button(
    "🔒 Çıkış Yap"
):

    st.session_state.giris_yapildi = False

    st.session_state.messages = []

    st.rerun()# --------------------
# DOSYA YÜKLEME
# --------------------

uploaded_file = st.sidebar.file_uploader(
    "📄 TXT Dosyası Yükle",
    type=["txt"]
)

dosya_icerigi = ""

if uploaded_file:

    try:

        dosya_icerigi = uploaded_file.read().decode(
            "utf-8"
        )

        st.sidebar.success(
            "Dosya yüklendi."
        )

    except:

        st.sidebar.error(
            "Dosya okunamadı."
        )

# --------------------
# ESKİ MESAJLAR
# --------------------

for mesaj in st.session_state.messages:

    with st.chat_message(
        mesaj["role"]
    ):

        st.markdown(
            mesaj["content"]
        )

# --------------------
# YENİ MESAJ
# --------------------

if soru := st.chat_input(
    "Lumina'ya mesaj gönder..."
):

    # Kullanıcı mesajı

    with st.chat_message(
        "user"
    ):

        st.markdown(soru)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": soru
        }
    )

    mesaj_kaydet(
        st.session_state.aktif_kullanici,
        "user",
        soru
    )

    # ----------------
    # GEMINI CEVABI
    # ----------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Lumina düşünüyor..."
        ):

            try:

                gecmis = ""

                for m in st.session_state.messages:

                    if m["role"] == "user":

                        gecmis += (
                            f"Kullanıcı: "
                            f"{m['content']}\n"
                        )

                    else:

                        gecmis += (
                            f"Lumina: "
                            f"{m['content']}\n"
                        )

                prompt = f"""
Sistem:

{modlar[ai_modu]}

Sohbet Geçmişi:

{gecmis}

Dosya İçeriği:

{dosya_icerigi}

Son Mesaj:

{soru}

Lumina:
"""

                cevap = client.models.generate_content(

                    model=model_sec,

                    contents=prompt

                )

                cevap_metni = cevap.text

                st.markdown(
                    cevap_metni
                )

                # Sesli cevap

                if sesli_mod:

                    konus(
                        cevap_metni
                    )

                st.session_state.messages.append(

                    {
                        "role": "assistant",
                        "content": cevap_metni
                    }

                )

                mesaj_kaydet(

                    st.session_state.aktif_kullanici,

                    "assistant",

                    cevap_metni

                )

            except Exception as e:

                st.error(
                    f"Hata: {e}"
                )
