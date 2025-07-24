import requests
import gzip
import json
from typing import Dict, List

def fetch_compressed_json() -> Dict:
    """GitHub'dan sıkıştırılmış JSON verisini çeker"""
    url = "https://raw.githubusercontent.com/TVGarden/tv-garden-channel-list/main/channels/compressed/categories/all-channels.json"
    headers = {
        'User-Agent': 'iTunes-AppleTV/15.0',
        'Referer': 'https://tv.garden/',
        'Origin': 'https://tv.garden'
    }
    
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return gzip.decompress(response.content).decode('utf-8')

def parse_channels(json_data: str) -> List[Dict]:
    """JSON verisinden kanal bilgilerini ayrıştırır"""
    channels = []
    data = json.loads(json_data)
    
    for category in data.get('categories', []):
        for channel in category.get('channels', []):
            if channel.get('iptv_urls'):
                channels.append({
                    'name': channel['name'],
                    'url': channel['iptv_urls'][0],  # İlk URL'yi al
                    'group': category['name']  # Ülke/Kategori adı
                })
    return channels

def generate_m3u(channels: List[Dict]) -> str:
    """M3U playlist oluşturur"""
    m3u_content = ["#EXTM3U"]
    
    for channel in channels:
        m3u_content.extend([
            f'#EXTINF:-1 group-title="{channel["group"]}",{channel["name"]}',
            channel['url']
        ])
    
    return '\n'.join(m3u_content)

def main():
    try:
        # Veriyi çek ve işle
        json_data = fetch_compressed_json()
        channels = parse_channels(json_data)
        
        # M3U oluştur ve kaydet
        with open('tv-garden.m3u', 'w', encoding='utf-8') as f:
            f.write(generate_m3u(channels))
        
        print(f"Başarıyla {len(channels)} kanal eklendi!")
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        raise

if __name__ == "__main__":
    main()
