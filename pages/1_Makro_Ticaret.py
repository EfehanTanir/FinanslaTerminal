import os
import streamlit as st
import pandas as pd
from fredapi import Fred

# --- API BAĞLANTISI ---
# 1. Railway (Environment Variables) üzerinden anahtarı çekmeyi dener
api_key = os.getenv("FRED_API_KEY")

# 2. Eğer Railway'de yoksa (lokal bilgisayardaysan), secrets.toml dosyasına bakar
if not api_key:
    try:
        api_key = st.secrets["FRED_API_KEY"]
    except:
        pass

# 3. İkisinde de yoksa hata verir ve durur
if not api_key:
    st.error("⚠️ FRED API Anahtarı bulunamadı. Lütfen Railway Environment Variables veya .streamlit/secrets.toml dosyasını kontrol edin.")
    st.stop()

fred = Fred(api_key=api_key)

# FRED'in sağladığı gerçek ve doğrulanmış İthalat/İhracat Seri Kodları Haritası (ABD Merkezli)
fred_series_map = {
    "Çin": {"İhracat": "EXPCH", "İthalat": "IMPCH"},
    "Kanada": {"İhracat": "EXPCA", "İthalat": "IMPCA"},
    "Meksika": {"İhracat": "EXPMX", "İthalat": "IMPMX"},
    "Japonya": {"İhracat": "EXPJP", "İthalat": "IMPJP"},
    "Almanya": {"İhracat": "EXPGM", "İthalat": "IMPGM"},
    "Birleşik Krallık": {"İhracat": "EXPUK", "İthalat": "IMPUK"},
    "Fransa": {"İhracat": "EXPFR", "İthalat": "IMPFR"},
    "Türkiye": {"İhracat": "EXP4890", "İthalat": "IMP4890"},
    "Avrupa Birliği (Genel)": {"İhracat": "EXP0003", "İthalat": "IMP0003"},
    "İleri Teknoloji Ürünleri (Global)": {"İhracat": "EXP0007", "İthalat": "IMP0007"},
    "OPEC Ülkeleri": {"İhracat": "EXP0001", "İthalat": "IMP0001"}
}

# --- SAYFA TASARIMI ---
st.header("🌍 Global Makro Ticaret ve Tedarik Zinciri")
st.caption("Ülkelerin ikili ticaret hacimleri ve FRED API üzerinden alınan gerçek makroekonomik veriler.")
st.markdown("---")

# 1. ARAMA VE FİLTRELEME ÇUBUĞU (İKİLİ SEÇİCİ)
col_ana, col_partner, col_bos = st.columns([2, 2, 1])

with col_ana:
    # FRED verileri ABD tabanlı olduğu için Ana Ülke ABD olarak kilitlidir.
    ana_ulke = st.selectbox(
        "🌍 Ana Ülke (Raporlayan)", 
        ["Amerika Birleşik Devletleri (ABD)"], 
        help="FRED API, ABD Sayım Bürosu verilerini kullandığı için ana ülke ABD olarak sabitlenmiştir."
    )
    
with col_partner:
    hedef_ulke = st.selectbox("🎯 Partner Ülke / Bölge Seçiniz", list(fred_series_map.keys()))

with col_bos:
    st.write("")
    st.write("")
    st.info("Veri: FRED 🦅")

st.markdown("---")
st.subheader(f"📊 {ana_ulke} - {hedef_ulke} İkili Ticaret Hacmi (Milyon $)")

# --- GERÇEK VERİ ÇEKME FONKSİYONU ---
@st.cache_data(ttl=86400) # Veriyi 24 saat önbellekte tutar, API limitini korur
def get_fred_data(series_id):
    try:
        # Son 5 yıllık veriyi çekelim (60 Ay)
        df = fred.get_series(series_id)
        df = df.tail(60) 
        return df
    except Exception as e:
        return None

col_exp, col_imp = st.columns(2)

with col_exp:
    st.markdown(f"#### 🚀 {ana_ulke}'nin {hedef_ulke}'ye İhracatı")
    ihracat_kodu = fred_series_map[hedef_ulke]["İhracat"]
    ihracat_verisi = get_fred_data(ihracat_kodu)
    
    if ihracat_verisi is not None and not ihracat_verisi.empty:
        son_deger = ihracat_verisi.iloc[-1]
        onceki_deger = ihracat_verisi.iloc[-2]
        degisim = ((son_deger - onceki_deger) / onceki_deger) * 100
        
        st.metric("Son Ay Hacmi", f"${son_deger:,.1f} M", f"{degisim:.2f}% (Aylık)")
        st.line_chart(ihracat_verisi)
    else:
        st.warning(f"FRED üzerinden {hedef_ulke} için ihracat verisi çekilemedi.")

with col_imp:
    st.markdown(f"#### 🛬 {ana_ulke}'nin {hedef_ulke}'den İthalatı")
    ithalat_kodu = fred_series_map[hedef_ulke]["İthalat"]
    ithalat_verisi = get_fred_data(ithalat_kodu)
    
    if ithalat_verisi is not None and not ithalat_verisi.empty:
        son_deger = ithalat_verisi.iloc[-1]
        onceki_deger = ithalat_verisi.iloc[-2]
        degisim = ((son_deger - onceki_deger) / onceki_deger) * 100
        
        st.metric("Son Ay Hacmi", f"${son_deger:,.1f} M", f"{degisim:.2f}% (Aylık)")
        st.line_chart(ithalat_verisi)
    else:
        st.warning(f"FRED üzerinden {hedef_ulke} için ithalat verisi çekilemedi.")

# --- HİSSE ETKİ KORELASYONU (MANTIK BÖLÜMÜ) ---
st.markdown("---")
st.subheader("💡 Arz-Talep ve Hisse Etkisi (Algoritmik Öngörü)")

with st.container(border=True):
    if ithalat_verisi is not None and ihracat_verisi is not None:
        if degisim > 0 and hedef_ulke == "Çin":
            st.markdown("🔴 **Yarı İletken & Üretim Uyarı:** Çin'den yapılan ithalatta artış var. Bu durum **NVDA, AAPL, TSLA** gibi donanım/üretim maliyetlerine bağımlı şirketlerin tedarik zincirinde stok birikimi veya talep artışı anlamına gelebilir.")
        elif degisim < 0 and hedef_ulke == "Almanya":
            st.markdown("🟢 **Avrupa Otomotiv Zayıflığı:** Almanya'dan ithalattaki düşüş, **F, GM** gibi yerli ABD otomotiv devleri için pazar payı avantajı yaratabilir.")
        elif degisim > 0 and hedef_ulke == "İleri Teknoloji Ürünleri (Global)":
            st.markdown("🟢 **Global Çip/Yazılım Talebi:** ABD'nin dünyaya teknoloji satışı artıyor. Bu durum **MSFT, GOOGL, NVDA** için doğrudan pozitif bilanço sinyalidir.")
        elif degisim < 0 and hedef_ulke == "Türkiye":
            st.markdown("⚪ **Gelişmekte Olan Piyasa:** Türkiye ile ABD arasındaki ticaret hacmindeki daralma, BIST tarafında (Borsa İstanbul) ihracatçı şirketleri etkileyebilir (Örn: **FROTO, SISE**).")
        else:
            st.markdown(f"⚪ **Nötr Seyir:** {ana_ulke} ile {hedef_ulke} arasındaki ticaret hacmi dalgalanmaları mevcut çeyrek için majör teknoloji veya endüstri hisselerinde doğrudan agresif bir tedarik şoku yaratmıyor.")