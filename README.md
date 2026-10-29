# Broadlink Climate (Arçelik / LG) for Home Assistant

Bu bileşen, Arçelik (LG altyapılı) klimaları Broadlink kızılötesi vericileri (`remote.send_command`) üzerinden kontrol eden yerel Home Assistant entegrasyonudur.

## Özellikler

- **Yerel ve Bağımsız:** Herhangi bir harici bulut servisine veya SmartIR indirme mekanizmasına ihtiyaç duymaz.
- **Doğrudan Base64 IR:** Doğrulanmış Broadlink kodlarıyla güvenilir sinyal iletimi.
- **Modlar:** Soğutma (`cool`), Nem Alma (`dry`) ve Kapatma (`off`).
- **Fan Kademeleri:** Düşük (`low`), Orta (`medium`), Yüksek (`high`).
- **Sıcaklık Aralığı:** 18°C - 30°C.
- **İsteğe Bağlı Sıcaklık Sensörü:** Odanın gerçek sıcaklığını göstermek için harici sensör bağlama imkanı (`temperature_sensor`).

## Kurulum

### HACS ile Kurulum
1. Home Assistant arayüzünde **HACS** > **Entegrasyonlar** sekmesine gidin.
2. Sağ üstteki üç noktaya tıklayıp **Özel depolar (Custom repositories)** seçeneğini açın.
3. Depo URL: `https://github.com/ismailpolatt/broadlink-climate`
4. Kategori: `Integration` (Entegrasyon)
5. **Ekle** butonuna tıklayın, listelenen entegrasyonu indirin ve Home Assistant'ı yeniden başlatın.

### Manuel Kurulum
`custom_components/oturma_klima` klasörünü Home Assistant'ın `/config/custom_components/` dizinine kopyalayın ve sistemi yeniden başlatın.

## Yapılandırma

`configuration.yaml` dosyanıza ekleyin:

```yaml
climate:
  - platform: oturma_klima
    name: "Oturma Klima"
    unique_id: oturma_klima_ir
    remote_entity: remote.broadlink_rm4_pro
    code_file: arcelik_klima.json
    # İsteğe bağlı: Odadaki sıcaklık sensörünüzün entity_id'si
    # temperature_sensor: sensor.oturma_th_temperature
```

## Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.
