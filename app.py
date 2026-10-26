from datetime import date, datetime
from zoneinfo import ZoneInfo
import random

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. SAYFA AYARI VE GOOGLE E-TABLO BAĞLANTISI
# ==========================================
st.set_page_config(page_title="Bütçe Savaşları", page_icon="⚔️", layout="wide")

WORKSHEET = "Sayfa1"
COLUMNS = [
    "ID",
    "Harcamayı Yapan Kim",
    "Tarih",
    "Tür",
    "Üst Kategori",
    "Alt Kategori",
    "Tutar",
    "Açıklama",
    "Dönem",
]

EZO = "❤️EZO❤️"
MYY = "💙MYY💙"

conn = st.connection("gsheets", type=GSheetsConnection)


def today_tr() -> date:
  """Streamlit Cloud sunucusu UTC çalışır; Türkiye saatine göre bugünü verir."""
  return datetime.now(ZoneInfo("Europe/Istanbul")).date()


def load_data() -> pd.DataFrame:
  """Google E-Tablo'dan verileri çeker (ttl=0: her zaman taze veri)."""
  df = conn.read(worksheet=WORKSHEET, ttl=0)
  df = df.dropna(how="all")

  # Sayfa boşsa / başlıklar eksikse güvenli iskelet
  for col in COLUMNS:
    if col not in df.columns:
      df[col] = pd.Series(dtype="object")
  df = df[COLUMNS]

  if not df.empty:
    df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce").dt.date
    # "1.234,50" gibi Türkçe formatlı metinleri de sayıya çevir
    if df["Tutar"].dtype == object:
      df["Tutar"] = (
          df["Tutar"]
          .astype(str)
          .str.replace(".", "", regex=False)
          .str.replace(",", ".", regex=False)
      )
    df["Tutar"] = pd.to_numeric(df["Tutar"], errors="coerce").fillna(0.0)
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
  return df


def save_data(df: pd.DataFrame) -> None:
  """Veriyi Google E-Tablo'ya yazar."""
  out = df.copy()
  out["Tarih"] = out["Tarih"].astype(str)  # date nesneleri yerine metin
  conn.update(worksheet=WORKSHEET, data=out)
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
        "Sigorta": [
            "Kasko",
            "Trafik Sigortası",
            "Konut / DASK",
            "Sağlık Sigortası",
            "Hayat / Bireysel Emeklilik",
        ],
        "Vergi": [
            "Motorlu Taşıtlar Vergisi (MTV)",
            "Emlak Vergisi",
            "Harç & Damga Vergisi",
            "Vergi Cezası / Gecikme",
        ],
        "Kira & Aidat": [
            "Aidat",
            "Site / Bina Yönetim Gideri",
            "Depozito",
        ],
        "Fatura": [
            "Elektrik",
            "Su",
            "Doğalgaz",
            "İnternet",
            "Cep Telefonu",
            "Sabit Hat / TV",
        ],
        "Abonelik": [
            "Dijital Platformlar (Netflix, Spotify vb.)",
            "Uygulama & Oyun",
            "Dergi / Gazete / Üyelik",
            "Spor Salonu Üyeliği",
        ],
        "Giyim": [
            "Ezo",
            "Myy",
            "Fatih Çınar",
            "Göktürk",
        ],
        "Diğer": ["Diğer Gider", "Muhtelif / Tanımsız"],
    },
    "Gelir": {
        "Maaş": ["Aylık Maaş", "İkramiye / Prim", "Tazminat / Mesai"],
        "Ek Ödeme": [
            "Serbest Çalışan / Ek İş",
            "Kira Geliri",
            "Satış / İkinci El",
            "Uzlaşma Ücreti",
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

  year, month = dt_val.year, dt_val.month

  if dt_val.day >= 15:
    start_year, start_month = year, month
  elif month == 1:
    start_year, start_month = year - 1, 12
  else:
    start_year, start_month = year, month - 1

  return f"{start_year}-{start_month:02d} Dönemi (15'i Başlangıçlı)"


# ==========================================
# 3. ARAYÜZ
# ==========================================
st.title("⚔️ Bütçe Savaşları: Kim Daha Harcadı? 💸")

if "ipucu" not in st.session_state:
  st.session_state["ipucu"] = random.choice(BUTCE_IPUCLARI)
st.info(st.session_state["ipucu"])

try:
  df = load_data()
except Exception as e:
  st.error(
      "Google E-Tablo'ya bağlanılamadı. Secrets ayarlarını, e-tablo paylaşım"
      " iznini ve sayfa adını (Sayfa1) kontrol edin."
  )
  st.exception(e)
  st.stop()

current_period = get_financial_period(today_tr())

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "➕ Yeni Kayıt Ekle",
    "📊 Mevcut Dönem Özeti",
    "🏆 Kişi Bazlı Müsabaka & Analiz",
    "📁 Geçmiş Dönem Raporları",
    "✏️ Kayıt Düzenle / Sil",
    ""🎙️ Sesli Kayıt",
])

# ------------------------------------------
# SEKME 1: YENİ KAYIT EKLE
# ------------------------------------------
with tab1:
  st.subheader("Yeni Gelir / Gider Ekle")

  # NOT: Kategori seçimleri birbirine bağlı olduğu için st.form DIŞINDA.
  # st.form içindeki widget'lar "Kaydet"e basılana kadar sayfayı yenilemez,
  # bu yüzden alt kategori listesi güncellenmezdi.
  col1, col2, col3 = st.columns(3)

  with col1:
    kisi = st.selectbox("Harcamayı / Geliri Yapan", [EZO, MYY, "Ortak"])
    tarih = st.date_input("Tarih", today_tr())
    tur = st.selectbox("Tür", ["Gider", "Gelir"])

  with col2:
    ust_kat = st.selectbox("Üst Kategori", list(CATEGORIES[tur].keys()))
    alt_kat = st.selectbox("Alt Kategori", CATEGORIES[tur][ust_kat])

  with col3:
    tutar = st.number_input("Tutar (TL)", min_value=0.0, step=10.0)
    aciklama = st.text_input("Açıklama")

  if st.button("💾 Kaydet", type="primary"):
    if tutar <= 0:
      st.warning("Tutar 0'dan büyük olmalı.")
    else:
      ids = pd.to_numeric(df["ID"], errors="coerce").dropna()
      next_id = int(ids.max()) + 1 if not ids.empty else 1

      new_row = {
          "ID": next_id,
          "Harcamayı Yapan Kim": kisi,
          "Tarih": tarih,
          "Tür": tur,
          "Üst Kategori": ust_kat,
          "Alt Kategori": alt_kat,
          "Tutar": float(tutar),
          "Açıklama": aciklama,
          "Dönem": get_financial_period(tarih),
      }

      # Yazma anında en güncel veriyi tekrar çek (iki kişi aynı anda
      # kullanırsa birbirinin kaydını ezmesin diye)
      fresh = load_data()
      ids = pd.to_numeric(fresh["ID"], errors="coerce").dropna()
      new_row["ID"] = int(ids.max()) + 1 if not ids.empty else 1
      df = pd.concat([fresh, pd.DataFrame([new_row])], ignore_index=True)

      try:
        save_data(df)
      except Exception as e:
        st.error("Kayıt yazılamadı. Servis hesabının e-tabloda 'Editör' yetkisi olmalı.")
        st.exception(e)
        st.stop()

      if tur == "Gelir":
        st.balloons()
        st.success(
            f"🎉 {random.choice(GELIR_MESAJLARI)}\n\n**Eklenen Tutar:** {tutar:,.2f} TL | **Yapan:** {kisi}",
            icon="💵",
        )
      elif kisi == EZO:
        st.error(
            f"💥 {random.choice(EZO_ASIRI_GIDER_MESAJLARI)}\n\n**Harcama:** {tutar:,.2f} TL | **Kategori:** {ust_kat}",
            icon="🚨",
        )
      elif kisi == MYY:
        st.info(
            f"☕ {random.choice(MYY_SOFT_GIDER_MESAJLARI)}\n\n**Harcama:** {tutar:,.2f} TL | **Kategori:** {ust_kat}",
            icon="😌",
        )
      else:
        st.warning(
            f"⚠️ Ortak harcama kaydedildi ({tutar:,.2f} TL - {ust_kat}). Bölüşüyoruz!",
            icon="🤝",
        )

# Kayıt sonrası güncel df ile devam
current_df = df[df["Dönem"] == current_period]

# ------------------------------------------
# SEKME 2: MEVCUT DÖNEM ÖZETİ
# ------------------------------------------
with tab2:
  st.subheader(f"🗓️ Aktif Dönem Özeti: {current_period}")

  if current_df.empty:
    st.info("Bu döneme ait henüz bir kayıt bulunmuyor.")
  else:
    toplam_gelir = current_df[current_df["Tür"] == "Gelir"]["Tutar"].sum()
    toplam_gider = current_df[current_df["Tür"] == "Gider"]["Tutar"].sum()
    kalan_bakiye = toplam_gelir - toplam_gider

    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} TL")
    c2.metric("Toplam Gider", f"{toplam_gider:,.2f} TL")
    c3.metric(
        "Net Kalan Bakiye",
        f"{kalan_bakiye:,.2f} TL",
        delta=f"{kalan_bakiye:,.2f} TL",
    )

    gider_df = current_df[current_df["Tür"] == "Gider"]
    if not gider_df.empty:
      st.markdown("---")
      st.write("### 📊 Kategori Bazlı Harcama Dağılımı")
      st.bar_chart(gider_df.groupby("Üst Kategori")["Tutar"].sum())

    st.markdown("---")
    st.write("### Dönem İşlem Listesi")
    st.dataframe(current_df)

# ------------------------------------------
# SEKME 3: KİŞİ BAZLI MÜSABAKA & ANALİZ
# ------------------------------------------
with tab3:
  st.subheader(f"👥 Kişi Bazlı Harcama Analizi & Şampiyonluk ({current_period})")

  if current_df.empty:
    st.info("Bu dönemde henüz kaydedilmiş bir harcama bulunmuyor.")
  else:
    gider_df = current_df[current_df["Tür"] == "Gider"]
    ezo_df = gider_df[gider_df["Harcamayı Yapan Kim"] == EZO]
    myy_df = gider_df[gider_df["Harcamayı Yapan Kim"] == MYY]
    ezo_toplam = ezo_df["Tutar"].sum()
    myy_toplam = myy_df["Tutar"].sum()

    if ezo_toplam > 0 or myy_toplam > 0:
      if ezo_toplam < myy_toplam:
        st.success(f"🏆 **AYIN TASARRUF ŞAMPİYONU:** {EZO} (Daha az harcama yaptı! Tebrikler! 🎉)")
      elif myy_toplam < ezo_toplam:
        st.success(f"🏆 **AYIN TASARRUF ŞAMPİYONU:** {MYY} (Ekonomi Bakanı koltuğunu koruyor! 😎)")
      else:
        st.info("🤝 **DURUM EŞİT!** İki taraf da aynı tutarda harcama yaptı.")

    col_p1, col_p2 = st.columns(2)
    for col, isim, toplam, kdf in (
        (col_p1, EZO, ezo_toplam, ezo_df),
        (col_p2, MYY, myy_toplam, myy_df),
    ):
      with col:
        st.markdown(f"### {isim}")
        st.metric("Toplam Harcama", f"{toplam:,.2f} TL")
        if not kdf.empty:
          st.write("#### Üst Kategori Dağılımı")
          st.dataframe(kdf.groupby("Üst Kategori")["Tutar"].sum().reset_index())
        else:
          st.info("Bu dönem harcaması yok.")

# ------------------------------------------
# SEKME 4: GEÇMİŞ DÖNEM RAPORLARI
# ------------------------------------------
with tab4:
  st.subheader("📁 Geçmiş Dönem Raporları ve Arşiv")

  donemler = df["Dönem"].dropna().unique().tolist()
  if not donemler:
    st.info("Henüz geçmiş veri bulunmamaktadır.")
  else:
    secilen_donem = st.selectbox(
        "İncelemek İstediğiniz Dönemi Seçin", sorted(donemler, reverse=True)
    )
    donem_df = df[df["Dönem"] == secilen_donem]

    g_toplam = donem_df[donem_df["Tür"] == "Gelir"]["Tutar"].sum()
    h_toplam = donem_df[donem_df["Tür"] == "Gider"]["Tutar"].sum()

    st.write(
        f"**{secilen_donem} Özeti:** Toplam Gelir: **{g_toplam:,.2f} TL** |"
        f" Toplam Gider: **{h_toplam:,.2f} TL**"
    )

    st.write("#### Üst Kategori Bazlı Dağılım")
    st.table(donem_df.groupby(["Tür", "Üst Kategori"])["Tutar"].sum().reset_index())

    st.write("#### Detaylı İşlem Listesi")
    st.dataframe(donem_df)
# ------------------------------------------
# SEKME 5: KAYIT DÜZENLE / SİL
# ------------------------------------------
with tab5:
  st.subheader("✏️ Kayıt Düzenle / Sil")

  donemler5 = df["Dönem"].dropna().unique().tolist()
  if not donemler5:
    st.info("Düzenlenecek kayıt bulunmuyor.")
  else:
    sec = st.selectbox(
        "Dönem", sorted(donemler5, reverse=True), key="duzenle_donem"
    )
    kaynak = (
        df[df["Dönem"] == sec]
        .sort_values("Tarih", ascending=False)
        .reset_index(drop=True)
    )
    orijinal_idler = set(kaynak["ID"].dropna().astype(int))

    # Listelerde eski/yeniden adlandırılmış kategoriler de görünsün
    tum_ust = sorted(
        {k for t in CATEGORIES.values() for k in t}
        | set(df["Üst Kategori"].dropna())
    )
    tum_alt = sorted(
        {a for t in CATEGORIES.values() for v in t.values() for a in v}
        | set(df["Alt Kategori"].dropna())
    )

    st.caption(
        "Hücreye çift tıklayıp düzenleyin. Satır silmek için satırı seçip"
        " çöp kutusuna basın. Bitince 'Değişiklikleri Kaydet'e basın."
    )

    duzenlenmis = st.data_editor(
        kaynak.drop(columns=["Dönem"]),
        key=f"editor_{sec}",
        num_rows="dynamic",
        hide_index=True,
        disabled=["ID"],
        column_config={
            "Harcamayı Yapan Kim": st.column_config.SelectboxColumn(
                options=[EZO, MYY, "Ortak"], required=True
            ),
            "Tarih": st.column_config.DateColumn(
                format="DD.MM.YYYY", required=True
            ),
            "Tür": st.column_config.SelectboxColumn(
                options=["Gider", "Gelir"], required=True
            ),
            "Üst Kategori": st.column_config.SelectboxColumn(
                options=tum_ust, required=True
            ),
            "Alt Kategori": st.column_config.SelectboxColumn(
                options=tum_alt, required=True
            ),
            "Tutar": st.column_config.NumberColumn(
                min_value=0.0, format="%.2f", required=True
            ),
        },
    )

    if st.button("💾 Değişiklikleri Kaydet", type="primary", key="duzenle_kaydet"):
      yeni = duzenlenmis.copy().reset_index(drop=True)
      hatalar = []

      zorunlu = [
          "Harcamayı Yapan Kim", "Tarih", "Tür",
          "Üst Kategori", "Alt Kategori", "Tutar",
      ]
      if yeni[zorunlu].isna().any().any():
        hatalar.append("Boş hücre var. Zorunlu alanları doldurun.")
      else:
        orig = kaynak.set_index("ID")
        for _, r in yeni.iterrows():
          rid = r["ID"]
          degisti = (
              pd.isna(rid)
              or rid not in orig.index
              or any(
                  r[c] != orig.loc[rid, c]
                  for c in ("Tür", "Üst Kategori", "Alt Kategori")
              )
          )
          uygun = CATEGORIES.get(r["Tür"], {}).get(r["Üst Kategori"], [])
          if degisti and r["Alt Kategori"] not in uygun:
            hatalar.append(
                f"'{r['Üst Kategori']}' altında '{r['Alt Kategori']}' yok."
                " Alt kategoriyi üst kategoriye uygun seçin."
            )

      if hatalar:
        for h in hatalar:
          st.error(h)
      else:
        # Yazmadan hemen önce taze veriyi çek
        fresh = load_data()
        rest = fresh[~fresh["ID"].isin(orijinal_idler)]

        mevcut = pd.to_numeric(fresh["ID"], errors="coerce").dropna()
        sonraki = int(mevcut.max()) + 1 if not mevcut.empty else 1
        for i in yeni.index:
          if pd.isna(yeni.at[i, "ID"]):
            yeni.at[i, "ID"] = sonraki
            sonraki += 1
        yeni["ID"] = yeni["ID"].astype(int)
        yeni["Dönem"] = yeni["Tarih"].apply(get_financial_period)
        yeni = yeni[COLUMNS]

        sonuc = pd.concat([rest[COLUMNS], yeni], ignore_index=True)
        try:
          save_data(sonuc)
        except Exception as e:
          st.error("Kayıt yazılamadı.")
          st.exception(e)
          st.stop()

        st.toast("Değişiklikler kaydedildi ✅")
        st.rerun()
# ------------------------------------------
# SEKME 6: SESLİ KAYIT
# (app.py'nin EN SONUNA ekleyin)
# Klavye mikrofonuyla yazılan cümleyi çözer, önizleme gösterir, onayla kaydeder.
# ------------------------------------------
import re
from datetime import timedelta

# Klavyenin kişi adlarını nasıl yazdığına göre buraya yazım ekleyebilirsiniz
EZO_ADLARI = ("ezo",)
MYY_ADLARI = ("myy", "mıy", "miy")

GELIR_KELIMELERI = (
    "gelir", "maaş", "maas", "ikramiye", "prim", "yattı", "temettü",
    "harçlık", "tazminat", "mesai", "kazandı",
)

# anahtar kelime -> (üst kategori, alt kategori ipucu)
SES_ANAHTAR = {
    "Gider": {
        "market": ("Market", None),
        "bakkal": ("Market", None),
        "şarküteri": ("Market", None),
        "manav": ("Market", "manav"),
        "sebze": ("Market", "manav"),
        "meyve": ("Market", "manav"),
        "temizlik": ("Market", "temizlik"),
        "benzin": ("Akaryakıt", "benzin"),
        "motorin": ("Akaryakıt", "motorin"),
        "mazot": ("Akaryakıt", "motorin"),
        "lpg": ("Akaryakıt", "lpg"),
        "akaryakıt": ("Akaryakıt", None),
        "yakıt": ("Akaryakıt", None),
        "eczane": ("Sağlık", "eczane"),
        "ilaç": ("Sağlık", "eczane"),
        "doktor": ("Sağlık", "muayene"),
        "hastane": ("Sağlık", "muayene"),
        "diş": ("Sağlık", "diş"),
        "otopark": ("Ulaşım", "otopark"),
        "taksi": ("Ulaşım", "taksi"),
        "hgs": ("Ulaşım", "otoban"),
        "köprü": ("Ulaşım", "otoban"),
        "otoban": ("Ulaşım", "otoban"),
        "otobüs": ("Ulaşım", "toplu"),
        "metro": ("Ulaşım", "toplu"),
        "tamir": ("Bakım Onarım", None),
        "tadilat": ("Bakım Onarım", "tadilat"),
        "okul": ("Eğitim", "okul"),
        "kreş": ("Eğitim", "okul"),
        "kurs": ("Eğitim", "kurs"),
        "kitap": ("Eğitim", "kitap"),
        "kırtasiye": ("Eğitim", "kitap"),
        "restoran": ("Sosyal Faaliyetler", "dışarıda"),
        "lokanta": ("Sosyal Faaliyetler", "dışarıda"),
        "kafe": ("Sosyal Faaliyetler", "dışarıda"),
        "kahve": ("Sosyal Faaliyetler", "dışarıda"),
        "yemek": ("Sosyal Faaliyetler", "dışarıda"),
        "sinema": ("Sosyal Faaliyetler", "sinema"),
        "tatil": ("Sosyal Faaliyetler", "gezi"),
        "hediye": ("Sosyal Faaliyetler", "hediye"),
        "sigorta": ("Sigorta", None),
        "kasko": ("Sigorta", "kasko"),
        "dask": ("Sigorta", "dask"),
        "vergi": ("Vergi", None),
        "mtv": ("Vergi", "mtv"),
        "kira": ("Kira & Aidat", "kira"),
        "aidat": ("Kira & Aidat", "aidat"),
        "elektrik": ("Fatura", "elektrik"),
        "doğalgaz": ("Fatura", "doğalgaz"),
        "internet": ("Fatura", "internet"),
        "fatura": ("Fatura", None),
        "netflix": ("Abonelik", "dijital"),
        "spotify": ("Abonelik", "dijital"),
        "abonelik": ("Abonelik", None),
        "bez": ("Çocuk", "bez"),
        "mama": ("Çocuk", "bez"),
        "oyuncak": ("Çocuk", "oyuncak"),
        "aşı": ("Çocuk", "aşı"),
        "çocuk": ("Çocuk", None),
        "bebek": ("Çocuk", None),
        "giyim": ("Giyim", None),
        "kıyafet": ("Giyim", None),
        "elbise": ("Giyim", None),
        "ayakkabı": ("Giyim", None),
        "borç": ("Borç & Kredi", None),
        "kredi": ("Borç & Kredi", None),
        "taksit": ("Borç & Kredi", "taksit"),
    },
    "Gelir": {
        "maaş": ("Maaş", "aylık"),
        "maas": ("Maaş", "aylık"),
        "ikramiye": ("Maaş", "ikramiye"),
        "prim": ("Maaş", "ikramiye"),
        "mesai": ("Maaş", "tazminat"),
        "tazminat": ("Maaş", "tazminat"),
        "kira": ("Ek Ödeme", "kira geliri"),
        "serbest": ("Ek Ödeme", "serbest"),
        "satış": ("Ek Ödeme", "satış"),
        "harçlık": ("Aile Desteği", "harçlık"),
        "temettü": ("Borsa", "temettü"),
        "hisse": ("Borsa", "hisse"),
    },
}

DURAK = {"diğer", "gider", "gelir", "muhtelif", "tanımsız", "ve", "vb"}

_BIR = {"sıfır": 0, "bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5,
        "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9}
_ON = {"on": 10, "yirmi": 20, "otuz": 30, "kırk": 40, "elli": 50,
       "altmış": 60, "yetmiş": 70, "seksen": 80, "doksan": 90}
_SAYI = re.compile(
    r"₺?\s*(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)\s*(lira|liralık|tl|₺)?"
)


def _kucuk(s):
  """Türkçe'ye uygun küçük harfe çevirme."""
  return s.replace("İ", "i").replace("I", "ı").lower()


def _kelime_var(tokens, kelime):
  if len(kelime) < 4:
    return kelime in tokens
  return any(k.startswith(kelime) for k in tokens)


def _ad_var(tokens, adlar):
  return any(
      k == a or (len(k) <= len(a) + 4 and k.startswith(a))
      for a in adlar for k in tokens
  )


def _yaziyla_sayi(tokens):
  """'dört yüz elli lira' -> 450 (yalnızca 'lira/tl' ile bitiyorsa)."""
  i = 0
  while i < len(tokens):
    toplam = cur = 0
    j = i
    while j < len(tokens):
      tok = tokens[j]
      if tok in _BIR:
        cur += _BIR[tok]
      elif tok in _ON:
        cur += _ON[tok]
      elif tok == "yüz":
        cur = (cur or 1) * 100
      elif tok == "bin":
        toplam += (cur or 1) * 1000
        cur = 0
      else:
        break
      j += 1
    if j > i:
      deger = toplam + cur
      if deger > 0 and j < len(tokens) and tokens[j] in ("lira", "liralık", "tl"):
        return float(deger)
      i = j
    else:
      i += 1
  return None


def _tutar_bul(t, tokens):
  adaylar = list(_SAYI.finditer(t))
  if adaylar:
    secilen = next((m for m in adaylar if m.group(2)), adaylar[0])
    s = secilen.group(1)
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", s):
      s = s.replace(".", "").replace(",", ".")
    else:
      s = s.replace(",", ".")
    return float(s), secilen.span()
  return _yaziyla_sayi(tokens), None


def _kategori_bul(tur, tokens):
  katlar = CATEGORIES[tur]
  ust = ipucu = None
  for kelime, (u, ip) in SES_ANAHTAR[tur].items():
    if u in katlar and _kelime_var(tokens, kelime):
      ust, ipucu = u, ip
      break
  if ust is None:  # kategori adından otomatik eşleştirme
    for u in katlar:
      for w in re.findall(r"[a-zçğıöşü]+", _kucuk(u)):
        if len(w) >= 4 and w not in DURAK and _kelime_var(tokens, w):
          ust = u
          break
      if ust:
        break
  if ust is None:
    return None, None

  altlar = katlar[ust]
  alt = None
  if ipucu:
    for a in altlar:
      if ipucu in _kucuk(a):
        alt = a
        break
  if alt is None:
    for a in altlar:
      for w in re.findall(r"[a-zçğıöşü]+", _kucuk(a)):
        if len(w) >= 3 and w not in DURAK and _kelime_var(tokens, w):
          alt = a
          break
      if alt:
        break
  return ust, (alt or altlar[0])


def ses_coz(metin):
  orijinal = metin.strip()
  t = _kucuk(orijinal)
  tokens = re.findall(r"[a-zçğıöşü0-9]+", t)

  # Kişi
  ezo = _ad_var(tokens, EZO_ADLARI)
  myy = _ad_var(tokens, MYY_ADLARI) or "myy" in t.replace(" ", "")
  if ezo and not myy:
    kisi = EZO
  elif myy and not ezo:
    kisi = MYY
  elif "ortak" in tokens:
    kisi = "Ortak"
  else:
    kisi = None

  # Tür
  tur = "Gider"
  if any(k.startswith(g) for k in tokens for g in GELIR_KELIMELERI):
    tur = "Gelir"
  if "vergi" in tokens and not any(k.startswith("iade") for k in tokens):
    tur = "Gider"

  # Tarih
  tarih = today_tr()
  if "dün" in tokens:
    tarih = tarih - timedelta(days=1)
  elif "evvelsi" in tokens or "önceki" in tokens:
    tarih = tarih - timedelta(days=2)

  tutar, span = _tutar_bul(t, tokens)
  ust, alt = _kategori_bul(tur, tokens)

  # Açıklama: tutar ve kişi adlarını çıkar
  acik = orijinal
  if span:
    acik = acik[: span[0]] + " " + acik[span[1]:]
  acik = re.sub(
      r"\b(ezo|myy|ortak)\b(?:['’]\w+)?", " ", acik, flags=re.IGNORECASE
  )
  acik = re.sub(r"\s+", " ", acik).strip(" ,.-")

  return {
      "metin": orijinal,
      "kisi": kisi,
      "tur": tur,
      "tarih": tarih,
      "ust": ust,
      "alt": alt,
      "tutar": tutar,
      "aciklama": acik or orijinal,
  }


with tab6:
  st.subheader("🎙️ Sesli Kayıt")
  st.caption(
      "Kutuya dokunun, klavyedeki 🎤 ile konuşun. Örnek: 'market harcaması"
      " MYY 450 lira haftalık alışveriş'. Sonra Çöz'e basın."
  )

  with st.form("ses_form", clear_on_submit=True):
    metin = st.text_area(
        "Komut",
        height=100,
        placeholder="market harcaması MYY 450 lira haftalık alışveriş",
    )
    coz = st.form_submit_button("🔍 Çöz")

  if coz:
    if metin.strip():
      st.session_state["ses_sonuc"] = ses_coz(metin)
      st.session_state["ses_id"] = st.session_state.get("ses_id", 0) + 1
    else:
      st.warning("Önce bir komut söyleyin ya da yazın.")

  sonuc = st.session_state.get("ses_sonuc")
  if sonuc:
    sid = st.session_state["ses_id"]
    st.info(f"🗣️ Anlaşılan: {sonuc['metin']}")
    if sonuc["kisi"] is None:
      st.warning("Kişi anlaşılamadı, lütfen seçin.")
    if sonuc["tutar"] is None:
      st.warning("Tutar anlaşılamadı, lütfen girin.")
    if sonuc["ust"] is None:
      st.warning("Kategori anlaşılamadı, lütfen seçin.")

    kisiler = [EZO, MYY, "Ortak"]
    c1, c2 = st.columns(2)
    with c1:
      kisi_s = st.selectbox(
          "Kim",
          kisiler,
          index=kisiler.index(sonuc["kisi"]) if sonuc["kisi"] in kisiler else None,
          placeholder="Seçin",
          key=f"ses_kisi_{sid}",
      )
      tur_s = st.selectbox(
          "Tür",
          ["Gider", "Gelir"],
          index=0 if sonuc["tur"] == "Gider" else 1,
          key=f"ses_tur_{sid}",
      )
      tarih_s = st.date_input("Tarih", sonuc["tarih"], key=f"ses_tarih_{sid}")
    with c2:
      usts = list(CATEGORIES[tur_s].keys())
      v_ust = sonuc["ust"] if sonuc["tur"] == tur_s and sonuc["ust"] in usts else usts[0]
      ust_s = st.selectbox(
          "Üst Kategori",
          usts,
          index=usts.index(v_ust),
          key=f"ses_ust_{sid}_{tur_s}",
      )
      altlar = CATEGORIES[tur_s][ust_s]
      v_alt = (
          sonuc["alt"]
          if sonuc["tur"] == tur_s and sonuc["ust"] == ust_s and sonuc["alt"] in altlar
          else altlar[0]
      )
      alt_s = st.selectbox(
          "Alt Kategori",
          altlar,
          index=altlar.index(v_alt),
          key=f"ses_alt_{sid}_{tur_s}_{ust_s}",
      )

    tutar_s = st.number_input(
        "Tutar (TL)",
        min_value=0.0,
        step=10.0,
        value=float(sonuc["tutar"] or 0.0),
        key=f"ses_tutar_{sid}",
    )
    acik_s = st.text_input(
        "Açıklama", value=sonuc["aciklama"], key=f"ses_acik_{sid}"
    )

    b1, b2 = st.columns(2)
    if b2.button("❌ Vazgeç", key=f"ses_vazgec_{sid}"):
      st.session_state["ses_sonuc"] = None
      st.rerun()

    if b1.button("✅ Onayla ve Kaydet", type="primary", key=f"ses_kaydet_{sid}"):
      if kisi_s is None:
        st.error("Lütfen kişiyi seçin.")
      elif tutar_s <= 0:
        st.error("Tutar 0'dan büyük olmalı.")
      else:
        fresh = load_data()
        ids = pd.to_numeric(fresh["ID"], errors="coerce").dropna()
        yeni_id = int(ids.max()) + 1 if not ids.empty else 1
        satir = {
            "ID": yeni_id,
            "Harcamayı Yapan Kim": kisi_s,
            "Tarih": tarih_s,
            "Tür": tur_s,
            "Üst Kategori": ust_s,
            "Alt Kategori": alt_s,
            "Tutar": float(tutar_s),
            "Açıklama": acik_s,
            "Dönem": get_financial_period(tarih_s),
        }
        try:
          save_data(pd.concat([fresh, pd.DataFrame([satir])], ignore_index=True))
        except Exception as e:
          st.error("Kayıt yazılamadı.")
          st.exception(e)
          st.stop()

        st.session_state["ses_sonuc"] = None
        st.toast(f"Kaydedildi: {tur_s} {tutar_s:,.2f} TL ✅")
        st.rerun()

