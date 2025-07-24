import requests
import gzip
import json
from typing import List, Dict

def fetch_compressed_json() -> bytes:
    """GitHub'dan sıkıştırılmış JSON verisini çeker"""
    url = "https://raw.githubusercontent.com/TVGarden/tv-garden-channel-list/main/channels/compressed/categories/all-channels.json"
    headers = {
        'User-Agent': 'iTunes-AppleTV/15.0',
        'Referer': 'https://tv.garden/',
        'Origin': 'https://tv.garden'
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.content

def parse_channels(compressed_data: bytes) -> List[Dict]:
    """JSON verisinden kanal bilgilerini ayrıştırır"""
    try:
        # Gzip verisini aç ve JSON'a dönüştür
        json_data = gzip.decompress(compressed_data).decode('utf-8')
        data = json.loads(json_data)
        
        # JSON yapısını kontrol et
        if not isinstance(data, list):
            raise ValueError("Beklenen JSON yapısı list tipinde değil")
            
        channels = []
        for channel in data:
            if not isinstance(channel, dict):
                continue
                
            # Kanal bilgilerini çıkar
            name = channel.get('name')
            urls = channel.get('iptv_urls', [])
            group = channel.get('group', 'Diğer')
            
            if name and urls:
                channels.append({
                    'name': name,
                    'url': urls[0],  # İlk geçerli URL
                    'group': group
                })
        return channels
        
    except Exception as e:
        print(f"JSON ayrıştırma hatası: {str(e)}")
        raise

def generate_m3u(channels: List[Dict]) -> str:
    """M3U playlist oluşturur"""
    m3u_content = ["#EXTM3U"]
    for channel in channels:
        m3u_content.append(f'#EXTINF:-1 group-title="{channel["group"]}",{channel["name"]}')
        m3u_content.append(channel['url'])
    return '\n'.join(m3u_content)

def main():
    try:
        print("Veri çekiliyor...")
        compressed_data = fetch_compressed_json()
        
        print("Kanal bilgileri ayrıştırılıyor...")
        channels = parse_channels(compressed_data)
        
        print(f"Toplam {len(channels)} kanal bulundu")
        
        with open('tv-garden.m3u', 'w', encoding='utf-8') as f:
            f.write(generate_m3u(channels))
            
        print("M3U dosyası başarıyla oluşturuldu!")
    except Exception as e:
        print(f"Kritik hata: {str(e)}")
        raise

if __name__ == "__main__":
    main()
