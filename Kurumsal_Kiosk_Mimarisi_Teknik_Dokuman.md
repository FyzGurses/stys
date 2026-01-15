# KURUMSAL KİOSK MİMARİSİ

## Sağlık Sektörü Sterilizasyon Takip Sistemi

### Teknik Mimari ve Teknoloji Seçim Dokümanı

---

|              |            |
| ------------ | ---------- |
| **Versiyon** | 1.0        |
| **Tarih**    | Ocak 2025  |
| **Durum**    | Taslak     |
| **Gizlilik** | Şirket İçi |

---

## İÇİNDEKİLER

1. [Yönetici Özeti](#1-yönetici-özeti)
2. [Proje Kapsamı ve Gereksinimler](#2-proje-kapsamı-ve-gereksinimler)
3. [Mimari Genel Bakış](#3-mimari-genel-bakış)
4. [Katman Bazlı Teknoloji Seçimleri](#4-katman-bazlı-teknoloji-seçimleri)
5. [Alternatif Teknoloji Değerlendirmesi](#5-alternatif-teknoloji-değerlendirmesi)
6. [Güvenlik Mimarisi](#6-güvenlik-mimarisi)
7. [Yüksek Erişilebilirlik ve Felaket Kurtarma](#7-yüksek-erişilebilirlik-ve-felaket-kurtarma)
8. [Uygulama Yol Haritası](#8-uygulama-yol-haritası)
9. [Maliyet Analizi](#9-maliyet-analizi)
10. [Sonuç ve Öneriler](#10-sonuç-ve-öneriler)
11. [Kurulum Rehberi](#11-kurulum-rehberi)
12. [Yazılım İçeriği](#12-yazılım-içeriği)

---

## 1. YÖNETİCİ ÖZETİ

Bu doküman, sağlık sektöründe sterilizasyon ekipman takibi için geliştirilecek kiosk tabanlı sistemin teknik mimarisini tanımlamaktadır. Sistem, ATM benzeri bir kullanıcı deneyimi sunacak, 7/24 kesintisiz çalışacak ve kurumsal güvenlik standartlarını karşılayacak şekilde tasarlanmıştır.

Önerilen mimari, açık kaynak teknolojiler üzerine kurulu olup **sıfır lisans maliyeti** hedeflemektedir. Debian tabanlı minimal işletim sistemi, OverlayFS ile korunan dosya sistemi ve PySide6 ile geliştirilecek native uygulama katmanı, sistemin temel bileşenlerini oluşturmaktadır.

### 1.1 Temel Hedefler

- Sıfır yazılım lisans maliyeti ile kurumsal çözüm
- 7/24 kesintisiz, güvenilir operasyon
- Elektrik kesintisi ve donanım arızalarına dayanıklılık
- Merkezi yönetim ve uzaktan güncelleme kapasitesi
- KVKK ve sağlık sektörü regülasyonlarına uyumluluk

---

## 2. PROJE KAPSAMI VE GEREKSİNİMLER

### 2.1 Fonksiyonel Gereksinimler

| Gereksinim       | Açıklama                                    | Öncelik |
| ---------------- | ------------------------------------------- | ------- |
| Barkod Tarama    | USB ve kablosuz barkod okuyucu desteği      | Kritik  |
| Ekipman Takibi   | Sterilizasyon durumu, geçmiş, sonraki tarih | Kritik  |
| Offline Çalışma  | Ağ kesintisinde yerel veritabanı ile devam  | Yüksek  |
| Etiket Yazdırma  | Termal yazıcı ile sterilizasyon etiketi     | Yüksek  |
| Raporlama        | Günlük, haftalık, aylık istatistikler       | Orta    |
| HIS Entegrasyonu | Hastane Bilgi Sistemi ile veri alışverişi   | Orta    |

### 2.2 Teknik Gereksinimler

| Kategori     | Gereksinim        | Hedef Değer         |
| ------------ | ----------------- | ------------------- |
| Performans   | Boot süresi       | < 30 saniye         |
| Performans   | Uygulama başlatma | < 5 saniye          |
| Güvenilirlik | Uptime            | > %99.9             |
| Güvenilirlik | MTBF              | > 8760 saat (1 yıl) |
| Kaynak       | RAM kullanımı     | < 512 MB            |
| Kaynak       | Disk kullanımı    | < 4 GB              |
| Güvenlik     | Şifreleme         | AES-256             |
| Ağ           | Bant genişliği    | < 1 Mbps ortalama   |

### 2.3 Operasyonel Gereksinimler

- Sistem, yetkisiz kullanıcıların işletim sistemine erişimini tamamen engelleyecektir.
- Ani elektrik kesintilerinde veri kaybı yaşanmayacak, sistem otomatik kurtarılacaktır.
- Uzaktan güncelleme sırasında başarısızlık durumunda otomatik geri dönüş sağlanacaktır.
- Merkezi yönetim konsolu üzerinden tüm cihazlar izlenebilecek ve yönetilebilecektir.

---

## 3. MİMARİ GENEL BAKIŞ

Önerilen mimari, katmanlı bir yapıda tasarlanmış olup her katman belirli bir sorumluluğu üstlenmektedir. Bu yaklaşım, bileşenlerin bağımsız olarak güncellenebilmesini ve test edilebilmesini sağlamaktadır.

### 3.1 Mimari Katmanlar

| Katman                 | Teknoloji                   | Seçim Gerekçesi                                          |
| ---------------------- | --------------------------- | -------------------------------------------------------- |
| İşletim Sistemi        | Debian 13 Minimal           | Stabil, güvenli, uzun dönem destek (LTS), geniş topluluk |
| Dosya Sistemi Koruması | OverlayFS + A/B Partition   | Elektrik kesintisine karşı koruma, güvenli güncelleme    |
| Display Server         | Xorg (X11)                  | Wayland'a göre kiosk kullanımında daha olgun             |
| Window Manager         | Openbox                     | Ultra hafif (<10MB RAM), tam konfigüre edilebilir        |
| Uygulama Katmanı       | Python 3.11 + PySide6       | Donanım kontrolü güçlü, LGPL lisans                      |
| Yerel Veritabanı       | SQLite 3                    | Sıfır konfigürasyon, güvenilir, hızlı                    |
| Uzaktan Yönetim        | Ansible + AutoSSH           | Agentless, güvenli, ölçeklenebilir                       |
| Merkezi Veritabanı     | PostgreSQL 16               | ACID uyumlu, ücretsiz, kurumsal seviye                   |
| İzleme                 | Prometheus + Grafana + Loki | Açık kaynak, endüstri standardı                          |
| VPN                    | WireGuard                   | Modern, hızlı, düşük overhead                            |

### 3.2 Sistem Topolojisi

Sistem, merkez-kenar (hub-spoke) topolojisinde çalışacaktır. Kiosk cihazları (kenar) WireGuard VPN üzerinden merkez sunucuya bağlanacak, veriler çift yönlü senkronize edilecektir.

```
┌────────────────────────────────────────────────────────────────┐
│                        KIOSK CİHAZI                            │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Debian 13 Minimal + CIS Hardening                       │  │
│  │  ├── OverlayFS (read-only root)                          │  │
│  │  ├── A/B Partitions (güvenli güncelleme)                 │  │
│  │  └── LUKS (data şifreleme)                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Xorg + Openbox (minimal display)                        │  │
│  │  └── PySide6 Uygulaması                                  │  │
│  │      ├── SQLite (offline cache)                          │  │
│  │      ├── Barkod / Yazıcı / Sensör                        │  │
│  │      └── WireGuard → Merkez                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Servisler                                               │  │
│  │  ├── Systemd Watchdog                                    │  │
│  │  ├── Promtail (log shipping)                             │  │
│  │  ├── AutoSSH (reverse tunnel)                            │  │
│  │  └── Sync Service (DB senkronizasyon)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              │
                              │ WireGuard VPN
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                      MERKEZ SUNUCU                             │
├────────────────────────────────────────────────────────────────┤
│  PostgreSQL │ Grafana/Loki │ Ansible │ RAUC Server │ REST API  │
└────────────────────────────────────────────────────────────────┘
```

Her kiosk cihazı bağımsız çalışabilecek şekilde tasarlanmıştır. Ağ bağlantısı koptuğunda yerel SQLite veritabanı üzerinden operasyonlar kesintisiz devam edecek, bağlantı yeniden kurulduğunda otomatik senkronizasyon gerçekleşecektir.

---

## 4. KATMAN BAZLI TEKNOLOJİ SEÇİMLERİ

### 4.1 İşletim Sistemi: Debian 13 (Trixie) Minimal

#### Seçim Gerekçesi

Debian, sunucu ve gömülü sistemlerde kanıtlanmış stabilitesi ile öne çıkmaktadır. Minimal kurulum yaklaşık 200 MB disk alanı kaplamakta ve gereksiz servisleri içermemektedir.

| Kriter           | Debian 13  | Ubuntu 24.04 | Alpine Linux   |
| ---------------- | ---------- | ------------ | -------------- |
| Stabilite        | Çok Yüksek | Yüksek       | Yüksek         |
| LTS Süresi       | 5 yıl      | 5 yıl        | 2 yıl          |
| Minimal Boyut    | 200 MB     | 400 MB       | 50 MB          |
| Paket Deposu     | 59.000+    | 60.000+      | 20.000+        |
| Topluluk Desteği | Çok Geniş  | Çok Geniş    | Orta           |
| Systemd Desteği  | Evet       | Evet         | Hayır (OpenRC) |
| Glibc/Musl       | glibc      | glibc        | musl           |
| Kurumsal Tercih  | Yüksek     | Yüksek       | Düşük          |

#### Alpine Linux Neden Seçilmedi?

Alpine Linux daha minimal olmasına rağmen **musl libc** kullanması nedeniyle bazı Python paketleri ve özellikle PySide6/PyQt6 ile uyumluluk sorunları yaşanabilmektedir. Kurumsal ortamda bu risk kabul edilemez düzeydedir.

---

### 4.2 Dosya Sistemi Koruması: OverlayFS + A/B Partition

#### OverlayFS Nedir ve Neden Kritik?

OverlayFS, Linux çekirdeğinin bir parçası olan union mount dosya sistemidir. İki veya daha fazla dizini tek bir birleşik görünüm altında birleştirir. Alt katman (lower) salt-okunur, üst katman (upper) yazılabilir olarak yapılandırılır.

| Özellik           | Açıklama                              | Fayda                  |
| ----------------- | ------------------------------------- | ---------------------- |
| Salt-Okunur Root  | Sistem dosyaları değiştirilemez       | Bozulmaya karşı koruma |
| RAM Tabanlı Yazma | Değişiklikler tmpfs'e yazılır         | Disk ömrü uzar         |
| Temiz Boot        | Her açılışta fabrika ayarlarına döner | Tutarsızlık önlenir    |
| Hızlı Kurtarma    | Reboot = temiz sistem                 | Downtime minimize      |

#### A/B Partition Şeması

Android ve Tesla gibi sistemlerin kullandığı A/B partition şeması, güvenli güncelleme için kritik öneme sahiptir. Aktif olmayan partition'a güncelleme yazılır, doğrulama sonrası geçiş yapılır. Başarısızlık durumunda otomatik rollback gerçekleşir.

| Partition | Boyut  | Kullanım                  | Mount               |
| --------- | ------ | ------------------------- | ------------------- |
| Boot      | 100 MB | Bootloader, kernel        | /boot               |
| Root A    | 2 GB   | Aktif sistem              | / (OverlayFS lower) |
| Root B    | 2 GB   | Yedek / Güncelleme hedefi | Unmounted           |
| Data      | Kalan  | Kalıcı veriler (şifreli)  | /data               |

---

### 4.3 Display Server: Xorg (X11)

#### Seçim Gerekçesi

Wayland, modern masaüstü sistemler için tasarlanmış olmasına rağmen kiosk senaryolarında X11 hala daha olgun ve sorunsuz çalışmaktadır. Özellikle dokunmatik ekran kalibrasyonu, ekran döndürme ve legacy uygulama desteği konularında X11 avantajlıdır.

| Kriter             | Xorg (X11)       | Wayland            | Değerlendirme     |
| ------------------ | ---------------- | ------------------ | ----------------- |
| Olgunluk           | 40+ yıl          | 12 yıl             | X11 daha stabil   |
| Kiosk Desteği      | Mükemmel         | Gelişiyor          | X11 tercih        |
| Touch Kalibrasyonu | xinput ile kolay | Compositor bağımlı | X11 tercih        |
| Donanım Uyumu      | Çok geniş        | Modern donanım     | X11 daha geniş    |
| Güvenlik           | Eski model       | Modern izolasyon   | Wayland avantajlı |
| Kaynak Kullanımı   | Orta             | Düşük              | Wayland avantajlı |

#### Wayland Alternatifi: Cage

İleride Wayland'a geçiş düşünülürse, **Cage** compositor değerlendirilmelidir. Cage, tek uygulama çalıştırmak için tasarlanmış minimal bir Wayland compositor olup kiosk senaryoları için idealdir. Ancak mevcut durumda X11 + Openbox kombinasyonu daha güvenli bir seçimdir.

---

### 4.4 Window Manager: Openbox

#### Seçim Gerekçesi

Openbox, LXDE masaüstü ortamının varsayılan window manager'ıdır. 10 MB'dan az RAM tüketimi, tam konfigüre edilebilir autostart, menü ve keybinding sistemi ile kiosk uygulamaları için ideal bir seçimdir.

| Window Manager | RAM Kullanımı | Konfigürasyon      | Kiosk Uygunluğu  |
| -------------- | ------------- | ------------------ | ---------------- |
| **Openbox**    | ~5 MB         | XML tabanlı, esnek | Mükemmel         |
| i3wm           | ~10 MB        | Config dosyası     | İyi              |
| GNOME Shell    | ~300 MB       | Dconf/gsettings    | Uygun değil      |
| KDE Plasma     | ~400 MB       | KConfig            | Uygun değil      |
| Yok (sadece X) | ~0 MB         | Yok                | Uygulamaya bağlı |

---

### 4.5 Uygulama Katmanı: Python 3.11 + PySide6

#### Python Seçim Gerekçesi

Python, donanım entegrasyonu gerektiren projelerde güçlü kütüphane ekosistemi ile öne çıkmaktadır. Seri port iletişimi (pyserial), USB cihaz kontrolü (pyusb), ve veritabanı işlemleri için native destek sunmaktadır.

| Kriter            | Python + PySide6 | Electron           | C++ / Qt    | Java / JavaFX |
| ----------------- | ---------------- | ------------------ | ----------- | ------------- |
| Geliştirme Hızı   | Yüksek           | Yüksek             | Düşük       | Orta          |
| RAM Kullanımı     | 50-100 MB        | 300-500 MB         | 30-50 MB    | 100-200 MB    |
| Donanım Erişimi   | Kolay            | Zor (native modül) | Kolay       | Orta          |
| Lisans            | LGPL (ücretsiz)  | MIT (ücretsiz)     | GPL/Ticari  | GPL/Ticari    |
| Tek Dosya Dağıtım | PyInstaller      | electron-builder   | Static link | JAR           |
| Öğrenme Eğrisi    | Düşük            | Düşük              | Yüksek      | Orta          |

#### PyQt6 vs PySide6 Karşılaştırması

Her iki kütüphane de Qt 6 için Python binding sağlamaktadır. API'ları neredeyse aynıdır. **Kritik fark lisanslama modelindedir.**

| Kriter          | PySide6            | PyQt6                  | Tercih      |
| --------------- | ------------------ | ---------------------- | ----------- |
| Lisans          | LGPL               | GPL veya Ticari        | **PySide6** |
| Sahip           | Qt Company (resmi) | Riverbank Computing    | **PySide6** |
| Ticari Kullanım | Ücretsiz           | Ücretli lisans gerekli | **PySide6** |
| API Uyumu       | Qt'ye %100 uyumlu  | %99 uyumlu             | Eşit        |
| Dökümantasyon   | Qt dokümanları     | Ayrı doküman           | **PySide6** |
| Performans      | Aynı               | Aynı                   | Eşit        |

#### Electron Neden Seçilmedi?

Electron, web teknolojileri (HTML/CSS/JavaScript) ile masaüstü uygulama geliştirmeyi mümkün kılar. Hızlı prototipleme için uygundur ancak kurumsal kiosk sistemleri için aşağıdaki dezavantajları bulunmaktadır:

- **Yüksek RAM tüketimi** (Chromium tabanlı): 300-500 MB baseline
- **Chromium'un potansiyel memory leak sorunları** uzun süreli çalışmada
- **Donanım erişimi için native modül derleme** karmaşıklığı
- **Büyük güvenlik saldırı yüzeyi** (Chromium güvenlik açıkları)

---

### 4.6 Veritabanı Mimarisi

#### Yerel Katman: SQLite 3

SQLite, kiosk cihazlarında yerel veri depolama için kullanılacaktır. Sıfır konfigürasyon gerektirmesi, tek dosya formatı ve ACID uyumluluğu ile gömülü sistemler için ideal bir seçimdir.

| Özellik       | Değer                    | Fayda              |
| ------------- | ------------------------ | ------------------ |
| Boyut         | ~600 KB                  | Minimal footprint  |
| Konfigürasyon | Sıfır                    | Bakım gerektirmez  |
| Eşzamanlılık  | Tek yazar, çoklu okuyucu | Kiosk için yeterli |
| ACID          | Tam destek               | Veri bütünlüğü     |
| Şifreleme     | SQLCipher ile            | KVKK uyumu         |

#### Merkezi Katman: PostgreSQL 16

PostgreSQL, merkezi veri deposu olarak kullanılacaktır. ACID uyumluluğu, gelişmiş JSON desteği ve replikasyon özellikleri ile kurumsal ihtiyaçları karşılamaktadır.

#### Senkronizasyon Stratejisi

```
┌─────────────┐         ┌─────────────────┐
│   Kiosk     │         │  Merkez Sunucu  │
│             │   sync  │                 │
│  SQLite     │ ◄─────► │  PostgreSQL     │
│  (offline)  │         │  (master)       │
└─────────────┘         └─────────────────┘
```

Çift yönlü senkronizasyon için last-write-wins veya conflict resolution mekanizması uygulanacaktır. Her kayıt için timestamp ve device_id tutularak çakışmalar çözümlenecektir. Ağ kesintisinde kiosk yerel veritabanı ile çalışmaya devam edecek, bağlantı kurulduğunda delta senkronizasyonu gerçekleşecektir.

---

### 4.7 Uzaktan Yönetim: Ansible + AutoSSH

#### Ansible Seçim Gerekçesi

Ansible, agentless mimarisi ile kiosk cihazlarında ek kaynak tüketmeden merkezi konfigürasyon yönetimi sağlar. YAML tabanlı playbook'lar ile tüm cihazlar tek komutla güncellenebilir.

| Araç        | Mimari     | Agent     | Öğrenme Eğrisi | Tercih      |
| ----------- | ---------- | --------- | -------------- | ----------- |
| **Ansible** | Push-based | Yok (SSH) | Düşük          | **Seçildi** |
| Puppet      | Pull-based | Gerekli   | Yüksek         | -           |
| Chef        | Pull-based | Gerekli   | Yüksek         | -           |
| SaltStack   | Her ikisi  | Opsiyonel | Orta           | -           |

#### AutoSSH ile Reverse Tunnel

Kiosk cihazları NAT arkasında bulunabilir ve doğrudan erişilemeyebilir. AutoSSH, merkez sunucuya kalıcı reverse SSH tunnel kurarak bu sorunu çözer. Bağlantı koptuğunda otomatik yeniden bağlanır.

---

## 5. ALTERNATİF TEKNOLOJİ DEĞERLENDİRMESİ

### 5.1 Değerlendirilen ve Reddedilen Alternatifler

| Teknoloji              | Değerlendirme              | Red Gerekçesi                                           |
| ---------------------- | -------------------------- | ------------------------------------------------------- |
| Windows IoT Enterprise | Lisans maliyeti yüksek     | Maliyet hedefine uyumsuz (~$100-200/cihaz)              |
| Android Kiosk          | Dokunmatik odaklı UI       | Barkod/yazıcı entegrasyonu zor, özelleştirme kısıtlı    |
| Chrome OS Flex         | Web tabanlı, hafif         | Offline çalışma kısıtlı, donanım erişimi yok            |
| Ubuntu Core (Snap)     | Transactional updates      | Snap sandbox kısıtlamaları, öğrenme eğrisi              |
| Yocto Project          | Tam özelleştirilmiş image  | Geliştirme süresi çok yüksek, küçük proje için overkill |
| Flutter Desktop        | Çapraz platform UI         | Linux desteği henüz olgunlaşmamış                       |
| Tauri                  | Electron alternatifi, Rust | Ekosistem henüz yeterli değil                           |

### 5.2 Gelecekte Değerlendirilebilecek Teknolojiler

| Teknoloji         | Potansiyel Kullanım           | Değerlendirme Zamanı          |
| ----------------- | ----------------------------- | ----------------------------- |
| Wayland + Cage    | Display server modernizasyonu | 2026 sonrası                  |
| Podman/Containers | Uygulama izolasyonu           | Faz 3 sonrası                 |
| RAUC              | A/B güncelleme yönetimi       | Faz 2                         |
| Mender            | OTA güncelleme platformu      | 50+ cihaz sonrası             |
| EdgeX Foundry     | IoT gateway entegrasyonu      | Sensör entegrasyonu gerekirse |

---

## 6. GÜVENLİK MİMARİSİ

### 6.1 Güvenlik Katmanları

| Katman              | Uygulama                 | Teknoloji      | KVKK Maddesi |
| ------------------- | ------------------------ | -------------- | ------------ |
| Ağ Güvenliği        | Şifreli tünel            | WireGuard VPN  | Madde 12     |
| Disk Şifreleme      | Veri partition şifreleme | LUKS (AES-256) | Madde 12     |
| Erişim Kontrolü     | USB cihaz kısıtlama      | USBGuard       | Madde 12     |
| Firewall            | Port kısıtlama           | nftables       | Madde 12     |
| Denetim İzi         | Tüm işlem logları        | auditd         | Madde 12     |
| Sistem Sertleştirme | CIS Benchmark            | Lynis          | Madde 12     |

### 6.2 WireGuard VPN Seçim Gerekçesi

WireGuard, modern kriptografi kullanarak minimum overhead ile güvenli bağlantı sağlar. OpenVPN ve IPSec'e kıyasla daha hızlı, daha basit ve daha az kod satırı içermektedir (güvenlik denetimi kolaylığı).

| Kriter              | WireGuard     | OpenVPN   | IPSec        |
| ------------------- | ------------- | --------- | ------------ |
| Kod Satırı          | ~4.000        | ~100.000  | ~400.000     |
| Performans          | Çok Yüksek    | Orta      | Yüksek       |
| Konfigürasyon       | Basit         | Karmaşık  | Çok Karmaşık |
| Mobil Desteği       | Mükemmel      | İyi       | Değişken     |
| Kernel Entegrasyonu | Native (5.6+) | Userspace | Native       |

### 6.3 USBGuard ile Cihaz Kontrolü

Sağlık sektöründe yetkisiz USB cihazları üzerinden veri sızıntısı veya malware bulaşması kritik bir risktir. USBGuard, whitelist tabanlı USB cihaz politikası uygulayarak sadece onaylı barkod okuyucu ve yazıcıların bağlanmasına izin verir.

---

## 7. YÜKSEK ERİŞİLEBİLİRLİK VE FELAKET KURTARMA

### 7.1 Watchdog Mekanizmaları

| Watchdog Türü         | Kapsam            | Aksiyon           | Timeout    |
| --------------------- | ----------------- | ----------------- | ---------- |
| Hardware Watchdog     | Sistem donması    | Donanımsal reboot | 60 saniye  |
| Systemd Watchdog      | Uygulama donması  | Servis restart    | 30 saniye  |
| Application Heartbeat | İş mantığı hatası | Uygulama restart  | 10 saniye  |
| Network Watchdog      | Bağlantı kaybı    | Interface restart | 120 saniye |

### 7.2 Otomatik Kurtarma Senaryoları

| Senaryo           | Tespit         | Otomatik Aksiyon               | RTO     |
| ----------------- | -------------- | ------------------------------ | ------- |
| Uygulama crash    | Systemd        | Restart (max 5 deneme)         | < 10 sn |
| Sistem donması    | HW Watchdog    | Hard reboot                    | < 90 sn |
| Disk doluluğu     | Monit          | Log temizleme + alert          | < 5 dk  |
| Ağ kesintisi      | NetworkManager | Interface restart, offline mod | < 30 sn |
| Güncelleme hatası | A/B boot       | Önceki partition'a rollback    | < 2 dk  |

---

## 8. UYGULAMA YOL HARİTASI

### 8.1 Faz Planlaması

| Faz                     | Kapsam                                | Süre    | Çıktı               |
| ----------------------- | ------------------------------------- | ------- | ------------------- |
| **Faz 1: MVP**          | Temel uygulama, SQLite, kiosk modu    | 6 hafta | Çalışır prototip    |
| **Faz 2: Stabilite**    | OverlayFS, Watchdog, USB kilitleme    | 4 hafta | Güvenilir sistem    |
| **Faz 3: Ölçekleme**    | Ansible, PostgreSQL sync, VPN         | 6 hafta | Çoklu cihaz desteği |
| **Faz 4: Kurumsal**     | Grafana, HIS entegrasyonu, A/B update | 8 hafta | Production-ready    |
| **Faz 5: Optimizasyon** | Performans iyileştirme, dokümantasyon | 4 hafta | Final release       |

### 8.2 Faz 1 Detay: MVP

1. Debian 13 minimal kurulum ve temel konfigürasyon
2. Xorg + Openbox kurulumu ve autostart yapılandırması
3. PySide6 uygulama iskeleti ve temel UI
4. SQLite veritabanı şeması ve CRUD operasyonları
5. Barkod okuyucu entegrasyonu
6. Temel kiosk kilitleme (klavye kısayolları)

### 8.3 Faz 2 Detay: Stabilite

1. OverlayFS yapılandırması (read-only root)
2. Hardware watchdog entegrasyonu
3. Systemd service hardening
4. USBGuard politika oluşturma
5. Temel logging altyapısı (rsyslog)
6. Otomatik kurtarma scriptleri

### 8.4 Faz 3 Detay: Ölçekleme

1. Ansible playbook'ları hazırlama
2. WireGuard VPN kurulumu
3. AutoSSH reverse tunnel
4. PostgreSQL merkezi veritabanı
5. Senkronizasyon servisi geliştirme
6. Çoklu cihaz test ortamı

---

## 9. MALİYET ANALİZİ

### 9.1 Yazılım Lisans Maliyetleri

| Bileşen     | Lisans                   | Birim Maliyet | 10 Cihaz | 50 Cihaz |
| ----------- | ------------------------ | ------------- | -------- | -------- |
| Debian 13   | Ücretsiz (GPL)           | 0 ₺           | 0 ₺      | 0 ₺      |
| PySide6     | Ücretsiz (LGPL)          | 0 ₺           | 0 ₺      | 0 ₺      |
| PostgreSQL  | Ücretsiz (PostgreSQL)    | 0 ₺           | 0 ₺      | 0 ₺      |
| SQLite      | Ücretsiz (Public Domain) | 0 ₺           | 0 ₺      | 0 ₺      |
| Grafana OSS | Ücretsiz (AGPL)          | 0 ₺           | 0 ₺      | 0 ₺      |
| WireGuard   | Ücretsiz (GPL)           | 0 ₺           | 0 ₺      | 0 ₺      |
| Ansible     | Ücretsiz (GPL)           | 0 ₺           | 0 ₺      | 0 ₺      |
| **TOPLAM**  | -                        | **0 ₺**       | **0 ₺**  | **0 ₺**  |

### 9.2 Alternatif Maliyet Karşılaştırması (Windows Tabanlı)

| Bileşen                | Lisans Türü        | Birim Maliyet | 10 Cihaz      | 50 Cihaz       |
| ---------------------- | ------------------ | ------------- | ------------- | -------------- |
| Windows IoT Enterprise | OEM/Retail         | ~3.000 ₺      | 30.000 ₺      | 150.000 ₺      |
| SQL Server Express     | Ücretsiz (sınırlı) | 0 ₺           | 0 ₺           | 0 ₺            |
| .NET Runtime           | Ücretsiz           | 0 ₺           | 0 ₺           | 0 ₺            |
| **TOPLAM**             | -                  | **~3.000 ₺**  | **~30.000 ₺** | **~150.000 ₺** |

> **Not:** Önerilen açık kaynak stack ile 50 cihazlık bir projede yaklaşık **150.000 ₺ lisans maliyetinden tasarruf** sağlanmaktadır.

---

## 10. SONUÇ VE ÖNERİLER

### 10.1 Özet

Bu dokümanda tanımlanan mimari, sağlık sektöründe sterilizasyon ekipman takibi için kurumsal seviyede, güvenilir ve maliyet-etkin bir kiosk sistemi sunmaktadır. Debian tabanlı minimal işletim sistemi, OverlayFS koruması, PySide6 uygulama katmanı ve açık kaynak izleme araçları, sıfır lisans maliyeti ile kurumsal gereksinimleri karşılamaktadır.

### 10.2 Kritik Başarı Faktörleri

- OverlayFS ve A/B partition ile sistem güvenilirliği sağlanmalıdır.
- Hardware watchdog ile kesintisiz operasyon garanti altına alınmalıdır.
- Merkezi yönetim altyapısı baştan planlanmalıdır.
- KVKK uyumluluk gereksinimleri tüm fazlarda gözetilmelidir.

### 10.3 Sonraki Adımlar

1. Mimari onayı ve paydaş geri bildirimi
2. Pilot cihaz üzerinde Faz 1 implementasyonu
3. Kullanıcı kabul testleri ve geri bildirim
4. Aşamalı yaygınlaştırma planı

### 10.4 Karar Özeti

| Karar               | Seçilen        | Alternatif      | Gerekçe                      |
| ------------------- | -------------- | --------------- | ---------------------------- |
| İşletim Sistemi     | Debian 13      | Ubuntu, Alpine  | Stabilite, LTS, glibc        |
| GUI Framework       | PySide6        | Electron, PyQt6 | RAM, lisans, donanım erişimi |
| Display             | Xorg + Openbox | Wayland         | Olgunluk, kiosk desteği      |
| Veritabanı (yerel)  | SQLite         | -               | Sıfır konfigürasyon          |
| Veritabanı (merkez) | PostgreSQL     | MySQL, MariaDB  | ACID, JSON, ücretsiz         |
| VPN                 | WireGuard      | OpenVPN, IPSec  | Performans, basitlik         |
| Config Management   | Ansible        | Puppet, Chef    | Agentless, öğrenme eğrisi    |
| Disk Koruması       | OverlayFS      | -               | Elektrik kesintisi koruması  |

---

## 11. KURULUM REHBERİ

### 11.1 Debian 13 Minimal Kurulum

1. Debian 13 (Trixie) netinst ISO'dan boot et
2. **Install** (text mode) seç
3. Dil, klavye, timezone ayarlarını yap
4. Hostname: `kiosk01`
5. Root şifresi belirle
6. Partitioning: "Guided - use entire disk" → "All files in one partition"
7. Software selection:
   - ❌ Desktop environment **SEÇİLMESİN**
   - ✅ SSH server
   - ✅ Standard system utilities
8. GRUB'ı `/dev/sda`'ya yükle

### 11.2 Temel Sistem Yapılandırması

#### Root SSH Erişimi Açma

```bash
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
systemctl restart sshd
```

#### GRUB Timeout Kapatma (Hızlı Boot)

```bash
sed -i 's/GRUB_TIMEOUT=5/GRUB_TIMEOUT=0/' /etc/default/grub
echo 'GRUB_TIMEOUT_STYLE=hidden' >> /etc/default/grub
update-grub
```

### 11.3 Kiosk Ortamı Kurulumu

#### Temel Paketler

```bash
apt update && apt upgrade -y
apt install -y \
    xorg openbox xterm x11-xserver-utils xinput unclutter \
    python3 python3-pip python3-venv python3-dev \
    fonts-dejavu fonts-liberation fontconfig \
    curl wget git vim htop usbutils openssh-server
```

#### Qt6/PySide6 Bağımlılıkları

```bash
apt install -y \
    libgl1 libegl1 libxkbcommon0 libdbus-1-3 \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
    libxcb-xfixes0 libxcb-xinerama0 libxcb-cursor0 \
    libxcb-xinput0 libxcb-xkb1 libxkbcommon-x11-0
```

#### VMware/VirtualBox için (Opsiyonel)

```bash
# VMware
apt install -y open-vm-tools open-vm-tools-desktop

# VirtualBox
apt install -y virtualbox-guest-x11
```

### 11.4 Kiosk Kullanıcısı Oluşturma

```bash
useradd -m -s /bin/bash -c "Kiosk User" kiosk
usermod -aG tty,video kiosk

mkdir -p /home/kiosk/{app,data,logs}
mkdir -p /home/kiosk/.config/openbox
chown -R kiosk:kiosk /home/kiosk
```

### 11.5 Display Manager Kurulumu (nodm)

```bash
apt install -y nodm

cat > /etc/default/nodm << 'EOF'
NODM_ENABLED=true
NODM_USER=kiosk
NODM_FIRST_VT=7
NODM_XSESSION=/home/kiosk/.xsession
NODM_X_OPTIONS='-nolisten tcp'
NODM_MIN_SESSION_TIME=60
EOF

cat > /home/kiosk/.xsession << 'EOF'
#!/bin/bash
xset s off
xset -dpms
exec /home/kiosk/app/venv/bin/python /home/kiosk/app/main.py
EOF

chmod +x /home/kiosk/.xsession
chown kiosk:kiosk /home/kiosk/.xsession

systemctl enable nodm
```

### 11.6 Python Ortamı ve Uygulama Kurulumu

```bash
# Virtual environment
su - kiosk -c "python3 -m venv /home/kiosk/app/venv"

# PySide6 kurulumu
su - kiosk -c "/home/kiosk/app/venv/bin/pip install --upgrade pip"
su - kiosk -c "/home/kiosk/app/venv/bin/pip install PySide6 pyserial python-dateutil"

# Uygulama dosyalarını kopyala
cp main.py database.py /home/kiosk/app/
chown kiosk:kiosk /home/kiosk/app/*.py
```

### 11.7 X Server İzin Ayarları

```bash
echo "allowed_users=anybody" > /etc/X11/Xwrapper.config
chmod 666 /dev/tty0
```

### 11.8 Gereksiz Servisleri Devre Dışı Bırakma

```bash
systemctl disable --now cups.service 2>/dev/null || true
systemctl disable --now avahi-daemon.service 2>/dev/null || true
systemctl disable --now bluetooth.service 2>/dev/null || true
systemctl disable --now ModemManager.service 2>/dev/null || true
```

### 11.9 Sistem Başlatma ve Test

```bash
reboot
```

Sistem yeniden başladığında:
- GRUB menüsü görünmeden boot edecek
- nodm otomatik olarak X başlatacak
- Kiosk uygulaması tam ekran açılacak

### 11.10 Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| SSH root erişimi yok | `PermitRootLogin yes` ekle, sshd restart |
| Qt xcb plugin hatası | `libxcb-cursor0` ve diğer xcb paketlerini kur |
| X server izin hatası | `Xwrapper.config` ve `/dev/tty0` izinlerini ayarla |
| Mouse çalışmıyor (VM) | `open-vm-tools-desktop` kur |
| GRUB menüsü geliyor | `GRUB_TIMEOUT=0` ayarla, `update-grub` çalıştır |

---

## 12. YAZILIM İÇERİĞİ

Butik Çalışma Sistemi
Cerrahi Alet Envanterinin Düzgün Tutulması
Düzenli Set Listelerinin Oluşturulması
Cerrahi Aletlerin İstatistikî Verilerin Sağlanması
Bakım Süresi Hatırlatma
Parçalı Aletlerin, Parçalarının Takip Edilmesi
Kullanım Tipi Ayrımları
Setlerin Bölüm veya Doktorlar Özelleştirilmesi
Bohçaya Sarılı Set Takip Edilmesi
Bohça Takibi Yapılabilinmesi
Sterilizasyon Makineleri Test sonuçları
Cerrahi Alet Kayıp ve Hasar Durumları
Konsinye Firma Setlerinin Takibi
Özel Rapor Menüsü
Biyomedikal İşlemleri

_— Doküman Sonu —_
