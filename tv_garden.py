import requests
import gzip
import json
import re
import emoji
from typing import List, Dict
from collections import defaultdict

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

def flag_to_country(flag_emoji: str) -> str:
    """Bayrak emojisini ülke ismine çevirir"""
    try:
        # Emoji kütüphanesi ile ülke adını al
        country_name = emoji.demojize(flag_emoji).replace('flag_for_', '').replace('_', ' ').title()
        return country_name
    except:
        return flag_emoji  # Tanımlanamazsa emojiyi olduğu gibi döndür

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
                
            name = channel.get('name', '')
            urls = channel.get('iptv_urls', [])
            
            if name and urls:
                # Bayrak emojisini bul
                flag_match = re.match(r'^(\U0001F1E6-\U0001F1FF\s*)', name)
                country = "Diğer"
                
                if flag_match:
                    flag = flag_match.group(1).strip()
                    country = flag_to_country(flag)
                    # Orijinal isimden bayrağı kaldır
                    name = re.sub(r'^\U0001F1E6-\U0001F1FF\s*', '', name).strip()
                
                channels.append({
                    'name': name,
                    'url': urls[0],
                    'group': country
                })
                country_stats[country] += 1
        
        # Ülke istatistiklerini yazdır
        print("\nÜlke Dağılımı:")
        for country, count in sorted(country_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"{country}: {count} kanal")
            
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
        
        print(f"\nToplam {len(channels)} kanal bulundu")
        
        with open('tv-garden.m3u', 'w', encoding='utf-8') as f:
            f.write(generate_m3u(channels))
            
        print("M3U dosyası başarıyla oluşturuldu!")
    except Exception as e:
        print(f"\nKritik hata: {str(e)}")
        raise

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Gerekli kütüphaneleri kontrol et
    try:
        import emoji
    except ImportError:
        print("\nemoji kütüphanesi yükleniyor...")
        import subprocess
        subprocess.run(["pip", "install", "emoji"], check=True)
        import emoji
    
    main()
