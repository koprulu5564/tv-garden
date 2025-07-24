import requests
import gzip
import json
from typing import List, Dict
from collections import defaultdict
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_compressed_json() -> bytes:
    """GitHub'dan sıkıştırılmış JSON verisini çeker"""
    url = "https://raw.githubusercontent.com/TVGarden/tv-garden-channel-list/main/channels/compressed/categories/all-channels.json"
    headers = {
        'User-Agent': 'iTunes-AppleTV/15.0',
        'Referer': 'https://tv.garden/',
        'Origin': 'https://tv.garden'
    }
    response = requests.get(url, headers=headers, verify=False, timeout=30)
    response.raise_for_status()
    return response.content

def parse_channels(compressed_data: bytes) -> List[Dict]:
    """JSON verisinden kanal bilgilerini ayrıştırır"""
    try:
        # Veriyi aç ve JSON'a dönüştür
        json_data = gzip.decompress(compressed_data).decode('utf-8')
        data = json.loads(json_data)
        
        channels = []
        category_stats = defaultdict(int)
        
        # JSON yapısını kontrol et
        if not isinstance(data, dict) or 'categories' not in data:
            raise ValueError("Beklenen JSON yapısı bulunamadı!")
        
        for category in data['categories']:
            category_name = category.get('name', 'Diğer')
            for channel in category.get('channels', []):
                if channel.get('iptv_urls'):
                    channels.append({
                        'name': channel['name'],
                        'url': channel['iptv_urls'][0],
                        'group': category_name
                    })
                    category_stats[category_name] += 1
        
        # İstatistikleri yazdır
        print("\n⚠️ Kategori Dağılımı:")
        for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"▸ {category}: {count} kanal")
            
        return channels
        
    except Exception as e:
        print(f"\n❌ JSON Ayrıştırma Hatası: {str(e)}")
        print("ℹ️ JSON yapısını kontrol etmek için:")
        print(json.dumps(data[:2], indent=2) if 'data' in locals() else "Veri yüklenemedi!")
        raise

def generate_m3u(channels: List[Dict]) -> str:
    """M3U playlist oluşturur"""
    m3u_content = ["#EXTM3U x-tvg-url=\"\""]
    for channel in channels:
        m3u_content.extend([
            f'#EXTINF:-1 tvg-id="{channel["name"].replace(" ", "_")}" group-title="{channel["group"]}",{channel["name"]}',
            channel['url']
        ])
    return '\n'.join(m3u_content)

def main():
    try:
        print("🔍 Veri çekiliyor...")
        compressed_data = fetch_compressed_json()
        
        print("🔧 Kanal bilgileri ayrıştırılıyor...")
        channels = parse_channels(compressed_data)
        
        print(f"\n✅ Toplam {len(channels)} kanal bulundu")
        
        with open('tv-garden.m3u', 'w', encoding='utf-8') as f:
            f.write(generate_m3u(channels))
            
        print("🎉 M3U dosyası başarıyla oluşturuldu!")
    except Exception as e:
        print(f"\n🔥 Kritik Hata: {str(e)}")
        raise

if __name__ == "__main__":
    main()
