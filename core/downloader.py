import os
import subprocess
import json
import re
from pathlib import Path
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from database.manager import VideoDatabase, get_video_metadata

def extract_video_id_from_filename(filename: str) -> str:
    """Extrait l'ID de la vidéo depuis le nom de fichier"""
    # Format attendu: video_id.extension
    match = re.match(r'^([a-zA-Z0-9_-]+)\.', filename)
    return match.group(1) if match else None

def get_file_info(file_path: str) -> dict:
    """Récupère les informations d'un fichier"""
    if not os.path.exists(file_path):
        return {}
    
    stat = os.stat(file_path)
    return {
        'file_size': stat.st_size,
        'exists': True
    }

def download_all_channel_audios(channel_url, output_dir="datas/audios_En", download_videos=False):
    """Télécharge tous les audios d'une chaîne et les enregistre dans la base de données"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Créer aussi le dossier pour les vidéos si nécessaire
    if download_videos:
        videos_dir = "datas/downloads"
        os.makedirs(videos_dir, exist_ok=True)
    
    # Initialiser la base de données
    db = VideoDatabase()
    
    # Extraire l'ID de la chaîne depuis l'URL
    channel_id_match = re.search(r'@([^/]+)', channel_url)
    channel_id = channel_id_match.group(1) if channel_id_match else "unknown"
    
    # Ajouter la chaîne à la base de données
    db.add_channel(channel_id, f"Chaîne {channel_id}", channel_url)
    
    print(f"🎯 Téléchargement de la chaîne: {channel_url}")
    print(f"📁 Dossier de sortie: {output_dir}")
    
    # Commande de téléchargement avec métadonnées JSON
    command = [
        "yt-dlp",
        "--yes-playlist",              # Télécharge toutes les vidéos
        "-x",                          # Extrait l'audio
        "--audio-format", "mp3",       # Format de sortie
        "--write-auto-sub",            # Récupère aussi les sous-titres auto
        "--sub-lang", "en",            # Langue des sous-titres
        "--write-info-json",           # Sauvegarde les métadonnées en JSON
        "--skip-download",             # Ne télécharge pas encore, juste les infos
        "-o", os.path.join(output_dir, "%(id)s.%(ext)s"),
        channel_url
    ]
    
    print(f"📋 Récupération des informations de la chaîne...")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Récupération des métadonnées...", total=None)
        
        try:
            # D'abord, récupérer la liste des vidéos
            list_command = [
                "yt-dlp",
                "--flat-playlist",
                "--get-id",
                channel_url
            ]
            
            result = subprocess.run(list_command, capture_output=True, text=True, check=True)
            video_ids = result.stdout.strip().split('\n')
            
            progress.update(task, description=f"Trouvé {len(video_ids)} vidéos")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de la récupération de la liste des vidéos: {e}")
            return
    
    print(f"✅ {len(video_ids)} vidéos trouvées")
    
    # Maintenant télécharger chaque vidéo avec ses métadonnées
    for i, video_id in enumerate(video_ids, 1):
        if not video_id.strip():
            continue
            
        print(f"\n📹 Vidéo {i}/{len(video_ids)}: {video_id}")
        
        # Récupérer les métadonnées de la vidéo
        metadata = get_video_metadata(video_id)
        if not metadata:
            print(f"⚠️ Impossible de récupérer les métadonnées pour {video_id}")
            continue
        
        # Ajouter la vidéo à la base de données
        video_data = {
            'video_id': video_id,
            'title': metadata.get('title', 'Titre inconnu'),
            'description': metadata.get('description', ''),
            'duration': metadata.get('duration'),
            'upload_date': metadata.get('upload_date'),
            'view_count': metadata.get('view_count'),
            'channel_id': channel_id
        }
        
        if db.add_video(video_data):
            print(f"✅ Vidéo ajoutée à la base de données: {metadata.get('title', 'Titre inconnu')}")
        
        # Télécharger l'audio et les sous-titres
        if download_videos:
            # Télécharger la vidéo complète
            video_download_command = [
                "yt-dlp",
                "--format", "best[height<=720]",  # Qualité 720p max
                "--write-auto-sub",            # Récupère les sous-titres auto
                "--sub-lang", "en",            # Langue des sous-titres
                "-o", os.path.join(videos_dir, "%(id)s.%(ext)s"),
                f"https://www.youtube.com/watch?v={video_id}"
            ]
            
            try:
                subprocess.run(video_download_command, check=True, capture_output=True)
                print(f"✅ Vidéo téléchargée: {video_id}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Erreur lors du téléchargement vidéo de {video_id}: {e}")
        
        # Télécharger l'audio
        download_command = [
            "yt-dlp",
            "-x",                          # Extrait l'audio
            "--audio-format", "mp3",       # Format de sortie
            "--write-auto-sub",            # Récupère les sous-titres auto
            "--sub-lang", "en",            # Langue des sous-titres
            "-o", os.path.join(output_dir, "%(id)s.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        try:
            subprocess.run(download_command, check=True, capture_output=True)
            
            # Enregistrer les fichiers dans la base de données
            audio_file = os.path.join(output_dir, f"{video_id}.mp3")
            subtitle_file = os.path.join(output_dir, f"{video_id}.en.vtt")
            
            # Ajouter le fichier audio
            if os.path.exists(audio_file):
                file_info = get_file_info(audio_file)
                db.add_audio_file(
                    video_id=video_id,
                    file_path=audio_file,
                    file_size=file_info.get('file_size'),
                    duration=metadata.get('duration'),
                    format="mp3"
                )
                print(f"✅ Audio enregistré: {audio_file}")
            
            # Ajouter le fichier de sous-titres
            if os.path.exists(subtitle_file):
                db.add_subtitle_file(
                    video_id=video_id,
                    file_path=subtitle_file,
                    language="en",
                    is_auto_generated=True
                )
                print(f"✅ Sous-titres enregistrés: {subtitle_file}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors du téléchargement de {video_id}: {e}")
            continue
    
    print(f"\n🎉 Téléchargement terminé!")
    print(f"📊 Affichage de la base de données:")
    db.display_videos_table()

def scan_existing_files(output_dir="datas/audios_En"):
    """Scanne les fichiers existants et les ajoute à la base de données"""
    print(f"🔍 Scan des fichiers existants dans {output_dir}")
    
    if not os.path.exists(output_dir):
        print(f"❌ Le dossier {output_dir} n'existe pas")
        return
    
    db = VideoDatabase()
    
    # Scanner les fichiers MP3
    mp3_files = list(Path(output_dir).glob("*.mp3"))
    vtt_files = list(Path(output_dir).glob("*.vtt"))
    
    print(f"📁 Trouvé {len(mp3_files)} fichiers MP3 et {len(vtt_files)} fichiers VTT")
    
    for mp3_file in mp3_files:
        video_id = extract_video_id_from_filename(mp3_file.name)
        if not video_id:
            continue
        
        print(f"📹 Traitement de {video_id}")
        
        # Récupérer les métadonnées
        metadata = get_video_metadata(video_id)
        if metadata:
            # Ajouter la vidéo
            video_data = {
                'video_id': video_id,
                'title': metadata.get('title', 'Titre inconnu'),
                'description': metadata.get('description', ''),
                'duration': metadata.get('duration'),
                'upload_date': metadata.get('upload_date'),
                'view_count': metadata.get('view_count'),
                'channel_id': metadata.get('channel_id', 'unknown')
            }
            db.add_video(video_data)
            
            # Ajouter le fichier audio
            file_info = get_file_info(str(mp3_file))
            db.add_audio_file(
                video_id=video_id,
                file_path=str(mp3_file),
                file_size=file_info.get('file_size'),
                duration=metadata.get('duration'),
                format="mp3"
            )
            
            # Chercher le fichier de sous-titres correspondant
            vtt_file = mp3_file.with_suffix('.en.vtt')
            if vtt_file.exists():
                db.add_subtitle_file(
                    video_id=video_id,
                    file_path=str(vtt_file),
                    language="en",
                    is_auto_generated=True
                )
                print(f"✅ Fichiers ajoutés pour {video_id}")
    
    print(f"\n📊 Base de données mise à jour:")
    db.display_videos_table()

def main():
    """Interface principale du module de téléchargement"""
    print("🎵 Gestionnaire de téléchargement YouTube avec base de données")
    print("=" * 60)
    
    choice = input("""
Choisissez une option:
1. Télécharger une nouvelle chaîne
2. Scanner les fichiers existants
3. Afficher la base de données
4. Rechercher des vidéos

Votre choix (1-4): """).strip()
    
    if choice == "1":
        url = input("👉 URL de la chaîne ou playlist YouTube : ").strip()
        if url:
            download_all_channel_audios(url)
        else:
            # URL par défaut
            url = "https://www.youtube.com/@DailyMotivates-1"
            download_all_channel_audios(url)
    
    elif choice == "2":
        scan_existing_files()
    
    elif choice == "3":
        db = VideoDatabase()
        db.display_videos_table()
    
    elif choice == "4":
        search_term = input("🔍 Terme de recherche : ").strip()
        if search_term:
            db = VideoDatabase()
            results = db.search_videos(search_term)
            if results:
                print(f"\n🔍 Résultats pour '{search_term}':")
                for result in results:
                    print(f"📹 {result[0]} - {result[1]}")
            else:
                print("❌ Aucun résultat trouvé")
    
    else:
        print("❌ Choix invalide")

if __name__ == "__main__":
    main()
