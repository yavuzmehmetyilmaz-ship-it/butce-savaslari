from datetime import date, datetime
import random
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 1. GOOGLE E-TABLO BAĞLANTISI VE SAYFA AYARI
# ==========================================
st.set_page_config(
    page_title="Bütçe Savaşları", page_icon="⚔️", layout="wide"
)

# gspread üzerinden güvenli Google Sheets bağlantısı kurulması
@st.cache_resource
def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["connections.gsheets"])
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(credentials)

gc = get_gspread_client()
spreadsheet_url = st.secrets["connections.gsheets"]["spreadsheet"]
sheet = gc.open_by_url(spreadsheet_url).worksheet("Sayfa1")


@st.cache_data(ttl=5)
def load_data():
    """Google E-Tablo'dan verileri çeker."""
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    # Boş satırları temizle
    df = df.dropna(how="all")
    if "Tarih" in df.columns and not df.empty:
        df["Tarih"] = pd.to_datetime(df["Tarih"]).dt.date
    return df


def save_data(df):
    """Yeni veriyi Google E-Tablo'ya günceller/yazar."""
    df_to_save = df.copy()
    if "Tarih" in df_to_save.columns:
        df_to_save["Tarih"] = df_to_save["Tarih"].astype(str)
    
    sheet.clear()
    sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
    st.cache_data.clear()


# ==========================================
# 2. KATEGORİLER VE MİZAH HAVUZU
# ==========================================
CATEGORIES = {
    "Gider": {
        "Market": [
            "Gıda & Şarküteri",
            "Manav & Meyve/Sebze",
            "Temizlik & Hijyen",
            "Kişisel Bakım",
            "Atıştırmalık & İçecek",
            "Ev Gereçleri",
        ],
        "Akaryakıt": ["Benzin", "Motorin", "LPG", "Oto Hijyen / Yıkama"],
        "Sağlık": [
            "İlaç & Eczane",
            "Muayene & Hastane",
            "Diş Sağlığı",
            "Medikal / Takviye",
        ],
        "Ulaşım": [
            "Toplu Taşıma",
            "Otoban & Köprü (HGS)",
            "Taksi & Dolmuş",
            "Otopark",
            "Araç Kiralama",
        ],
        "Bakım Onarım": [
            "Araç Bakım & Servis",
            "Araç Muayene / Sigorta",
            "Ev Tadilat & Tamirat",
            "Beyaz Eşya Servis",
            "Elektronik Tamir",
        ],
        "Eğitim": [
            "Okul / Kreş Taksiti",
            "Kurs & Özel Ders",
            "Kitap & Kırtasiye",
            "Eğitim Materyali",
        ],
        "Sosyal Faaliyetler": [
            "Dışarıda Yeme & İçme",
            "Sinema & Tiyatro & Etkinlik",
            "Gezi & Tatil",
            "Spor & Hobi",
            "Hediye & Eğlence",
        ],
        "Diğer": ["Diğer Gider", "Muhtelif / Tanımsız"],
    },
    "Gelir": {
        "Maaş": ["Aylık Maaş", "İkramiye / Prim", "Tazminat / Mesai"],
        "Ek Ödeme": [
            "Serbest Çalışan / Ek İş",
            "Kira Geliri",
            "Satış / İkinci El",
        ],
        "Aile Desteği": ["Harçlık", "Akraba Desteği", "Hediye / Bağış"],
        "Borsa": ["Temettü Geliri", "Hisse Satış Karı", "VİOP / Fon Geliri"],
        "Diğer": ["Diğer Gelir", "Muhtelif / Tanımsız"],
    },
}

GELIR_MESAJLARI = [
    "Bereket versin! Kasa ferahladı, bıyıklar buruldu! 💰🕺",
    "Gelsin paracıklar! Hesap hareketlendi, yüzler güldü! 🚀✨",
    "Maaş/Gelir dediğin böyle olur! Çaylar benden! ☕🎉",
    "Ağam bizimle eğlenir! Haneye taze para girişi yapıldı! 🏠💎",
    "Hesaba para yatınca gelen o 'dünyayı ben yarattım' hissi... 😎💅",
    "Biri 'para mutluluk getirmez' demişti, ona bu dekontu göndermek lazım! 📩💸",
    "Finansal özgürlük yükleniyor: %15... Devamını bekliyoruz! 🔋📈",
    "Kasa alev aldı! Fakirliğe 1 ay daha ara veriyoruz. 🥳🍾",
]

EZO_ASIRI_GIDER_MESAJLARI = [
    "🚨 ALARM ALARM! Ezo yine card'ı sarstı! Kredi kartı ekstreye isyan bayrağını çekti! 😱🔥",
    "Eyvahlar olsun! Avm'ler şokta, Ezo yine fırtına gibi esti! Cüzdan yoğun bakımda! 🚑💨",
    "Ağlamak istiyorum sayın seyirciler! Bu harcama ev ekonomisini temelinden sarstı! 📉💸",
    "Kartın çipi eridi eriyecek! Hızlı harcamada rekor kırılıyor! ⚡🛍️",
    "Ezo kartı pos cihazına dokundurdu, temassız limiti bile 'Ben bu yükü çekemem' dedi! 🤖💳",
    "X'te TT olduk: #EzoNedenHarcadı! Bütçede son durum: Yoğun bakım... 🏥💔",
]

MYY_SOFT_GIDER_MESAJLARI = [
    "Alt tarafı bi harcama yaptık, ne olacak canım, altı üstü kuruş! Manzara güzel ama... ☕😌",
    "Ufak tefek masraflar bunlar, kasayı sarsmaz, pirinç tanesi kadar dert etmeyin efenim. 🌾🍵",
    "Huzur harcaması diyelim biz buna; cüzdan gülüyor, MYY mutlu! 😊💸",
    "Aman ne olacak, bir kahve parası, idare edeceğiz gari! 🥐👍",
]

BUTCE_IPUCLARI = [
    "💡 Market alışverişine aç karnına çıkılmadığı bir ay dileriz! 🛒",
    "💡 Dışarıda içilen tek bir kahve = Evde 1 paket çekirdek kahve! Mesele kahve değil, konsept! ☕",
    "💡 Unutmayın: En ucuz harcama, yapılmayan harcamadır! 🧘‍♂️",
]


def get_financial_period(dt_val):
    if isinstance(dt_val, str):
        dt_val = datetime.strptime(dt_val, "%Y-%m-%d").date()

    year = dt_val.year
    month = dt_val.month

    if dt_val.day >= 15:
        period_start_year = year
        period_start_month = month
    else:
        if month == 1:
            period_start_year = year - 1
            period_start_month = 12
        else:
            period_start_year = year
            period_start_month = month - 1

    return f"{period_start_year}-{period_start_month:02d} Dönemi (15'i Başlangıçlı)"


# ==========================================
# 3. ARAYÜZ (UI) TASARIMI
# ==========================================
st.title("⚔️ Bütçe Savaşları: Kim Daha Harcadı? 💸")
st.info(random.choice(BUTCE_IPUCLARI))

df = load_data()
current_period = get_financial_period(date.today())

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Yeni Kayıt Ekle",
    "📊 Mevcut Dönem Özeti",
    "🏆 Kişi Bazlı Müsabaka & Analiz",
    "📁 Geçmiş Dönem Raporları",
])

# ------------------------------------------
# SEKME 1: YENİ KAYIT EKLE
# ------------------------------------------
with tab1:
    st.subheader("Yeni Gelir / Gider Ekle")

    with st.form("add_record_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            kisi = st.selectbox("Harcamayı / Geliri Yapan", ["❤️EZO❤️", "💙MYY💙", "Ortak"])
            tarih = st.date_input("Tarih", date.today())
            tur = st.selectbox("Tür", ["Gider", "Gelir"])

        with col2:
            ust_kat_options = list(CATEGORIES[tur].keys())
            ust_kat = st.selectbox("Üst Kategori", ust_kat_options)

            alt_kat_options = CATEGORIES[tur][ust_kat]
            alt_kat = st.selectbox("Alt Kategori", alt_kat_options)

        with col3:
            tutar = st.number_input("Tutar (TL)", min_value=0.0, step=10.0)
            aciklama = st.text_input("Açıklama")

        submit = st.form_submit_button("💾 Kaydet")

        if submit:
            next_id = int(df["ID"].max() + 1) if not df.empty and "ID" in df.columns and pd.notna(df["ID"].max()) else 1
            donem = get_financial_period(tarih)

            new_row = {
                "ID": next_id,
                "Harcamayı Yapan Kim": kisi,
                "Tarih": str(tarih),
                "Tür": tur,
                "Üst Kategori": ust_kat,
                "Alt Kategori": alt_kat,
                "Tutar": tutar,
                "Açıklama": aciklama,
                "Dönem": donem,
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)

            if tur == "Gelir":
                st.balloons()
                mesaj = random.choice(GELIR_MESAJLARI)
                st.success(
                    f"🎉 {mesaj}\n\n**Eklenen Tutar:** {tutar:,.2f} TL | **Yapan:** {kisi}",
                    icon="💵",
                )
            else:
                if kisi == "❤️EZO❤️":
                    mesaj = random.choice(EZO_ASIRI_GIDER_MESAJLARI)
                    st.error(
                        f"💥 {mesaj}\n\n**Harcama:** {tutar:,.2f} TL | **Kategori:** {ust_kat}",
                        icon="🚨",
                    )
                elif kisi == "💙MYY💙":
                    mesaj = random.choice(MYY_SOFT_GIDER_MESAJLARI)
                    st.info(
                        f"☕ {mesaj}\n\n**Harcama:** {tutar:,.2f} TL | **Kategori:** {ust_kat}",
                        icon="😌",
                    )
                else:
                    st.warning(
                        f"⚠️ Ortak harcama kaydedildi ({tutar:,.2f} TL - {ust_kat}). Bölüşüyoruz!",
                        icon="🤝",
                    )

# ------------------------------------------
# SEKME 2: MEVCUT DÖNEM ÖZETİ
# ------------------------------------------
with tab2:
    st.subheader(f"🗓️ Aktif Dönem Özeti: {current_period}")

    current_df = df[df["Dönem"] == current_period] if not df.empty and "Dönem" in df.columns else df

    if current_df.empty:
        st.info("Bu döneme ait henüz bir kayıt bulunmuyor.")
    else:
        toplam_gelir = current_df[current_df["Tür"] == "Gelir"]["Tutar"].sum()
        toplam_gider = current_df[current_df["Tür"] == "Gider"]["Tutar"].sum()
        kalan_bakiye = toplam_gelir - toplam_gider

        col_g1, col_g2, col_g3 = st.columns(3)
        col_g1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} TL")
        col_g2.metric("Toplam Gider", f"{toplam_gider:,.2f} TL")
        col_g3.metric(
            "Net Kalan Bakiye",
            f"{kalan_bakiye:,.2f} TL",
            delta=f"{kalan_bakiye:,.2f} TL",
        )

        gider_df = current_df[current_df["Tür"] == "Gider"]
        if not gider_df.empty:
            st.markdown("---")
            st.write("### 📊 Kategori Bazlı Harcama Dağılımı")
            kat_gider = gider_df.groupby("Üst Kategori")["Tutar"].sum()
            st.bar_chart(kat_gider)

        st.markdown("---")
        st.write("### Dönem İşlem Listesi")
        st.dataframe(current_df, use_container_width=True)

# ------------------------------------------
# SEKME 3: KİŞİ BAZLI MÜSABAKA & ANALİZ
# ------------------------------------------
with tab3:
    st.subheader(
        f"👥 Kişi Bazlı Harcama Analizi & Şampiyonluk ({current_period})"
    )

    current_df = df[df["Dönem"] == current_period] if not df.empty and "Dönem" in df.columns else df

    if current_df.empty:
        st.info("Bu dönemde henüz kaydedilmiş bir harcama bulunmuyor.")
    else:
        gider_df = current_df[current_df["Tür"] == "Gider"]

        ezo_toplam = gider_df[gider_df["Harcamayı Yapan Kim"] == "❤️EZO❤️"][
            "Tutar"
        ].sum() if not gider_df.empty else 0
        myy_toplam = gider_df[gider_df["Harcamayı Yapan Kim"] == "💙MYY💙"][
            "Tutar"
        ].sum() if not gider_df.empty else 0

        if ezo_toplam > 0 or myy_toplam > 0:
            if ezo_toplam < myy_toplam:
                st.success(
                    "🏆 **AYIN TASARRUF ŞAMPİYONU:** ❤️EZO❤️ (Daha az harcama yaptı! Tebrikler! 🎉)"
                )
            elif myy_toplam < ezo_toplam:
                st.success(
                    "🏆 **AYIN TASARRUF ŞAMPİYONU:** 💙MYY💙 (Ekonomi Bakanı koltuğunu koruyor! 😎)"
                )
            else:
                st.info("🤝 **DURUM EŞİT!** İki taraf da aynı tutarda harcama yaptı.")

        col_p1, col_p2 = st.columns(2)

        with col_p1:
            st.markdown("### ❤️EZO❤️")
            st.metric("Toplam Harcama", f"{ezo_toplam:,.2f} TL")
            ezo_df = gider_df[gider_df["Harcamayı Yapan Kim"] == "❤️EZO❤️"]
            if not ezo_df.empty:
                st.write("#### Üst Kategori Dağılımı")
                ezo_ozet = ezo_df.groupby("Üst Kategori")["Tutar"].sum().reset_index()
                st.dataframe(ezo_ozet, use_container_width=True)
            else:
                st.info("Bu dönem harcaması yok.")

        with col_p2:
            st.markdown("### 💙MYY💙")
            st.metric("Toplam Harcama", f"{myy_toplam:,.2f} TL")
            myy_df = gider_df[gider_df["Harcamayı Yapan Kim"] == "💙MYY💙"]
            if not myy_df.empty:
                st.write("#### Üst Kategori Dağılımı")
                myy_ozet = myy_df.groupby("Üst Kategori")["Tutar"].sum().reset_index()
                st.dataframe(myy_ozet, use_container_width=True)
            else:
                st.info("Bu dönem harcaması yok.")

# ------------------------------------------
# SEKME 4: GEÇMİŞ DÖNEM RAPORLARI
# ------------------------------------------
with tab4:
    st.subheader("📁 Geçmiş Dönem Raporları ve Arşiv")

    if df.empty or "Dönem" not in df.columns:
        st.info("Henüz geçmiş veri bulunmamaktadır.")
    else:
        tum_donemler = sorted(df["Dönem"].unique(), reverse=True)
        secilen_donem = st.selectbox("İncelemek İstediğiniz Dönemi Seçin", tum_donemler)

        donem_df = df[df["Dönem"] == secilen_donem]

        g_toplam = donem_df[donem_df["Tür"] == "Gelir"]["Tutar"].sum()
        h_toplam = donem_df[donem_df["Tür"] == "Gider"]["Tutar"].sum()

        st.write(
            f"**{secilen_donem} Özeti:** Toplam Gelir: **{g_toplam:,.2f} TL** | Toplam Gider: **{h_toplam:,.2f} TL**"
        )

        st.write("#### Üst Kategori Bazlı Dağılım")
        ozet_tbl = (
            donem_df.groupby(["Tür", "Üst Kategori"])["Tutar"].sum().reset_index()
        )
        st.table(ozet_tbl)

        st.write("#### Detaylı İşlem Listesi")
        st.dataframe(donem_df, use_container_width=True)
