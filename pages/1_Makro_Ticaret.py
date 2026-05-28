import streamlit as st
import pandas as pd
from fredapi import Fred

# --- API BAĞLANTISI ---
# Streamlit secrets üzerinden API anahtarını güvenle çekiyoruz
try:
    fred = Fred(api_key=st.secrets["FRED_API_KEY"])
except Exception as e:
    st.error("⚠️ FRED API Anahtarı bulunamadı. Lütfen .streamlit/secrets.toml dosyasını kontrol edin.")
    st.stop()

# --- SAYFA TASARIMI ---
st.header("🌍 Global Makro Ticaret ve Tedarik Zinciri")
st.caption("Ülkelerin ticaret hacimleri ve FRED API üzerinden alınan gerçek makroekonomik veriler.")
st.markdown("---")

# FRED'de ABD'nin ticaret yaptığı bazı ana ülkelerin veri serisi kodları
fred_series_map = {
    "Çin": {"İhracat": "EXPCH", "İthalat": "IMPCH"},
    "Almanya": {"İhracat": "EXPGM", "İthalat": "IMPGM"},
    "Japonya": {"İhracat": "EXPJP", "İthalat": "IMPJP"},
    "Kanada": {"İhracat": "EXPCA", "İthalat": "IMPCA"},
    "Meksika": {"İhracat": "EXPMX", "İthalat": "IMPMX"},
    "Birleşik Krallık": {"İhracat": "EXPUK", "İthalat": "IMPUK"}
}

col_search, col_period = st.columns([3, 1])
with col_search:
    secilen_ulke = st.selectbox("🔍 ABD'nin Ticaret Yaptığı Ülkeyi Seç", list(fred_series_map.keys()))
with col_period:
    st.info("Veri Kaynağı: FRED 🦅")

st.markdown("---")
st.subheader(f"📊 ABD - {secilen_ulke} İkili Ticaret Hacmi (Milyon $)")

# --- GERÇEK VERİ ÇEKME FONKSİYONU ---
@st.cache_data(ttl=86400) # Veriyi 24 saat önbellekte tutar, API limitini korur
def get_fred_data(series_id):
    try:
        # Son 5 yıllık veriyi çekelim
        df = fred.get_series(series_id)
        df = df.tail(60) # Son 60 ay (5 Yıl)
        return df
    except Exception as e:
        return None

col_exp, col_imp = st.columns(2)

with col_exp:
    st.markdown(f"#### 🚀 ABD'nin {secilen_ulke}'ye İhracatı")
    ihracat_kodu = fred_series_map[secilen_ulke]["İhracat"]
    ihracat_verisi = get_fred_data(ihracat_kodu)
    
    if ihracat_verisi is not None:
        son_deger = ihracat_verisi.iloc[-1]
        onceki_deger = ihracat_verisi.iloc[-2]
        degisim = ((son_deger - onceki_deger) / onceki_deger) * 100
        
        st.metric("Son Ay Hacmi", f"${son_deger:,.1f} M", f"{degisim:.2f}% (Aylık)")
        st.line_chart(ihracat_verisi)
    else:
        st.warning("Veri çekilemedi.")

with col_imp:
    st.markdown(f"#### 🛬 ABD'nin {secilen_ulke}'den İthalatı")
    ithalat_kodu = fred_series_map[secilen_ulke]["İthalat"]
    ithalat_verisi = get_fred_data(ithalat_kodu)
    
    if ithalat_verisi is not None:
        son_deger = ithalat_verisi.iloc[-1]
        onceki_deger = ithalat_verisi.iloc[-2]
        degisim = ((son_deger - onceki_deger) / onceki_deger) * 100
        
        st.metric("Son Ay Hacmi", f"${son_deger:,.1f} M", f"{degisim:.2f}% (Aylık)")
        st.line_chart(ithalat_verisi)
    else:
        st.warning("Veri çekilemedi.")

# --- HİSSE ETKİ KORELASYONU (MANTIK BÖLÜMÜ) ---
st.markdown("---")
st.subheader("💡 Arz-Talep ve Hisse Etkisi (Algoritmik Öngörü)")

with st.container(border=True):
    if ithalat_verisi is not None and ihracat_verisi is not None:
        if degisim > 0 and secilen_ulke == "Çin":
            st.markdown("🔴 **Yarı İletken & Üretim Uyarı:** Çin'den yapılan ithalatta artış var. Bu durum **NVDA, AAPL, TSLA** gibi donanım/üretim maliyetlerine bağımlı şirketlerin tedarik zincirinde stok birikimi veya talep artışı anlamına gelebilir.")
        elif degisim < 0 and secilen_ulke == "Almanya":
            st.markdown("🟢 **Avrupa Otomotiv Zayıflığı:** Almanya'dan ithalattaki düşüş, **F, GM** gibi yerli ABD otomotiv devleri için pazar payı avantajı yaratabilir.")
        else:
            st.markdown("⚪ **Nötr Seyir:** Seçili ülkedeki ticaret hacmi dalgalanmaları mevcut çeyrek için majör teknoloji veya endüstri hisselerinde doğrudan agresif bir tedarik şoku yaratmıyor.")