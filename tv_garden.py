import requests
import gzip
import json
from typing import List, Dict
from collections import defaultdict
import urllib3
from pycountry import countries

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

def get_country_name(country_code: str) -> str:
    """Ülke kodundan ismini alır (ör: kr -> Güney Kore)"""
    try:
        country = countries.get(alpha_2=country_code)
        return country.name if country else country_code.upper()
    except:
        return country_code.upper()

def parse_channels(compressed_data: bytes) -> List[Dict]:
    """JSON verisinden kanal bilgilerini ayrıştırır"""
    try:
        json_data = gzip.decompress(compressed_data).decode('utf-8')
        data = json.loads(json_data)
        
        channels = []
        country_stats = defaultdict(int)
        
        for channel in data:
            if not isinstance(channel, dict):
                continue
                
            # Kanal bilgilerini çıkar
            name = channel.get('name', '').strip()
            urls = channel.get('iptv_urls', [])
            country_code = channel.get('country', '').lower()
            
            if name and urls:
                country = get_country_name(country_code) if country_code else 'Diğer'
                channels.append({
                    'name': name,
                    'url': urls[0],
                    'group': country
                })
                country_stats[country] += 1
        
        # İstatistikleri yazdır
        print("\n🌍 Ülke Dağılımı:")
        for country, count in sorted(country_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"▸ {country}: {count} kanal")
            
        return channels
        
    except Exception as e:
        print(f"\n❌ JSON Ayrıştırma Hatası: {str(e)}")
        if 'data' in locals():
            print("ℹ️ JSON Örneği:", json.dumps(data[:2], indent=2))
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
