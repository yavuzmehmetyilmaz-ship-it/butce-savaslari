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

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Yeni Kayıt Ekle",
    "📊 Mevcut Dönem Özeti",
    "🏆 Kişi Bazlı Müsabaka & Analiz",
    "📁 Geçmiş Dönem Raporları",
    "✏️ Kayıt Düzenle / Sil",
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
