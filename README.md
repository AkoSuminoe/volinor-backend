# Volinor Backend

Bu proje Volinor web uygulamasının backend (sunucu tarafı) kısmıdır ve **Django** framework'ü kullanılarak geliştirilmiştir. 

Aşağıdaki adımları izleyerek projeyi kendi bilgisayarınızda çalıştırabilirsiniz.

## 🚀 Başlangıç ve Kurulum

Backend projesini çalıştırmak için sanal ortam (virtual environment) kullanılması gereklidir. Son aldığınız `ModuleNotFoundError: No module named 'django'` hatasının sebebi sanal ortamın aktif olmamasıdır.

### 1. Terminali Açın ve Proje Dizinine Gidin
Eğer proje ana dizinindeyseniz (`volinor-web`), backend klasörüne girin:
```powershell
cd volinor-backend
```

### 2. Sanal Ortamı (Virtual Environment) Aktif Edin
Bağımlılıkların sisteminize değil, bu projeye özel kurulması için sanal ortamı çalıştırmanız gerekir. Windows/PowerShell kullanıyorsanız şu komutu girin:
```powershell
.\venv\Scripts\activate
```
*(Başarılı olduğunda komut satırının başında `(venv)` ibaresini göreceksiniz.)*

### 3. Gerekli Paketleri Yükleyin (Gerekirse)
Projenin ihtiyaç duyduğu kütüphaneleri indirmek için (daha önce yaptıysanız atlayabilirsiniz):
```powershell
pip install -r requirements.txt
```

### 4. Veritabanı Göçlerini (Migrations) Uygulayın
Veritabanı tablolarının oluşturulması ve güncel kalması için:
```powershell
python manage.py migrate
```

### 5. Sunucuyu Çalıştırın
Tüm adımlar tamamsa, geliştirme sunucusunu başlatabilirsiniz:
```powershell
python manage.py runserver
```

Sunucu başarıyla çalıştığında, konsolda `BACKEND AKTİF!` mesajını göreceksiniz ve API'ye tarayıcı üzerinden `http://127.0.0.1:8000/` adresinden erişebileceksiniz.
