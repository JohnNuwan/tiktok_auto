import os
import subprocess
import json
import re
from pathlib import Path
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from database.manager import VideoDatabase, get_video_metadata

class Downloader:
    def __init__(self, output_dir="datas/audios_En"):
        self.output_dir = Path(output_dir)
        self.db = VideoDatabase()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_audio(self, urls: list) -> list:
        """
        Télécharge l'audio d'une ou plusieurs URL YouTube et l'ajoute à la BDD.
        Retourne une liste d'informations sur les vidéos téléchargées.
        """
        downloaded_videos_info = []
        for url in urls:
            try:
                # Utiliser yt-dlp pour obtenir les informations de la vidéo sans télécharger
                info_command = ["yt-dlp", "--dump-json", "--skip-download", url]
                result = subprocess.run(info_command, capture_output=True, text=True, check=True, encoding='utf-8')
                metadata = json.loads(result.stdout)

                video_id = metadata.get('id')
                if not video_id:
                    print(f"❌ Impossible d'obtenir l'ID pour l'URL: {url}")
                    continue

                if self.db.video_exists(video_id):
                    print(f"🟡 Vidéo {video_id} déjà dans la base de données. Sautée.")
                    continue

                # Télécharger l'audio
                audio_path = self.output_dir / f"{video_id}.mp3"
                download_command = [
                    "yt-dlp",
                    "-x",
                    "--audio-format", "mp3",
                    "-o", str(self.output_dir / '%(id)s.%(ext)s'),
                    url
                ]
                subprocess.run(download_command, check=True, capture_output=True)

                # Ajouter à la base de données
                video_data = {
                    'video_id': video_id,
                    'title': metadata.get('title', 'Titre inconnu'),
                    'url': url,
                    'channel_name': metadata.get('channel', 'Chaîne inconnue'),
                    'status': 'downloaded'
                }
                self.db.add_video(**video_data)

                video_info = {
                    'id': video_id,
                    'audio_path': str(audio_path),
                    'channel': metadata.get('channel', 'Chaîne inconnue')
                }
                downloaded_videos_info.append(video_info)
                print(f"✅ Vidéo ajoutée à la base de données: {metadata.get('title')}")

            except subprocess.CalledProcessError as e:
                print(f"❌ Erreur lors du téléchargement de {url}: {e.stderr}")
            except Exception as e:
                print(f"❌ Erreur inattendue pour {url}: {e}")
        
        return downloaded_videos_info

# --- Fonctions existantes pour la compatibilité --- #

def extract_video_id_from_filename(filename: str) -> str:
    match = re.match(r'^([a-zA-Z0-9_-]+)\.', filename)
    return match.group(1) if match else None

def get_file_info(file_path: str) -> dict:
    if not os.path.exists(file_path): return {}
    stat = os.stat(file_path)
    return {'file_size': stat.st_size, 'exists': True}

def download_all_channel_audios(channel_url, output_dir="datas/audios_En", download_videos=False):
    # ... (le code de cette fonction reste inchangé)
    pass

def scan_existing_files(output_dir="datas/audios_En"):
    # ... (le code de cette fonction reste inchangé)
    pass

def main():
    # ... (le code de cette fonction reste inchangé)
    pass

if __name__ == "__main__":
    main()
