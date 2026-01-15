# Kiosk MVP - Sterilizasyon Takip Sistemi

Sağlık sektöründe sterilizasyon ekipman takibi için kiosk tabanlı sistem.

## Gereksinimler

- Debian 13 (Trixie) Minimal (netinst)
- Minimum 2GB RAM
- Minimum 8GB Disk
- Ağ bağlantısı (kurulum için)

## Tek Komutla Kurulum

### 1. Debian 13 Minimal Kurulum

1. [Debian netinst ISO](https://www.debian.org/distrib/netinst) indir
2. VM oluştur ve ISO'dan boot et
3. **Install** (text mode) seç
4. Software selection:
   - ❌ Desktop environment **SEÇİLMESİN**
   - ✅ SSH server
   - ✅ Standard system utilities

### 2. Dosyaları VM'e Kopyala

```powershell
# Windows PowerShell / CMD
scp -r scripts app root@<VM_IP>:/root/kiosk-mvp/
```

### 3. Kurulumu Başlat

```bash
ssh root@<VM_IP>
cd /root/kiosk-mvp/scripts
chmod +x *.sh
./00_install_all.sh
```

**Tek komut, tam kurulum!** Sistem otomatik reboot edecek ve uygulama açılacak.

## Dizin Yapısı

```
kiosk-mvp/
├── app/
│   ├── main.py          # Ana uygulama (PySide6 GUI)
│   └── database.py      # SQLite veritabanı modülü
├── scripts/
│   ├── 00_install_all.sh    # Tek komutla tam kurulum
│   ├── 01_base_setup.sh     # Temel paketler + nodm
│   ├── 02_kiosk_user.sh     # Kullanıcı + X yapılandırması
│   ├── 03_pyside6_setup.sh  # Python/PySide6
│   ├── 04_deploy_app.sh     # Uygulama deployment
│   └── 05_system_config.sh  # GRUB + güvenlik
└── README.md
```

## Kurulum Sonrası

### SSH ile Erişim

```bash
ssh root@<VM_IP>
```

### Veritabanı

```
/home/kiosk/data/sterilizasyon.db
```

### Log Dosyaları

```
/home/kiosk/logs/app_YYYYMMDD.log
```

## Uygulama Modülleri

| Modül | Açıklama |
|-------|----------|
| Dashboard | İstatistikler, hızlı barkod tarama |
| Alet Envanteri | Cerrahi alet yönetimi |
| Set Yönetimi | Set oluşturma ve düzenleme |
| Bohça Takip | Bohça hazırlama ve takip |
| Sterilizasyon | Sterilizasyon kaydı |
| Makineler | Sterilizasyon makineleri |
| Raporlar | Çeşitli raporlar |
| Kayıp/Hasar | Olay kayıtları |

## Demo Veriler

Kurulum sonrası otomatik yüklenir:

| Tür | Örnekler |
|-----|----------|
| Aletler | ALT001-ALT010 (Makas, Forseps, vb.) |
| Setler | SET001-SET004 (Cerrahi setler) |
| Makineler | 4 adet (Steam, ETO, Plazma) |
| Bölümler | Ameliyathane, Endoskopi, vb. |

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| SSH bağlanamıyor | `PermitRootLogin yes` kontrol et |
| Uygulama açılmıyor | `journalctl -u nodm` ile log kontrol |
| Mouse çalışmıyor | `apt install open-vm-tools-desktop` |
| Siyah ekran | SSH ile bağlan, `/home/kiosk/logs/` kontrol et |

## Klavye Kısayolları

| Tuş | İşlev |
|-----|-------|
| ESC | Geri / Çıkış dialogu |
| Enter | Barkod onaylama |
