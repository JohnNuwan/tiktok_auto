#!/usr/bin/env python3
"""
Module de Génération Automatique de Shorts
Génère automatiquement des shorts viraux pour TikTok, YouTube Shorts, Instagram Reels
Inspiré de Remakeit et Opus pour la monétisation
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import subprocess
import shutil
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.manager import VideoDatabase
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from montage.clip_finder import find_potential_clips
from translation.whisper_simple import WhisperTranscriber
from translation.text_translator import TextTranslator
from translation.tts_simple import TTSSimple

class ShortsGenerator:
    """Générateur automatique de shorts viraux"""
    
    def __init__(self, output_dir: str = "datas/shorts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Créer la structure de dossiers organisée
        self.final_dir = self.output_dir / "final"
        self.temp_dir = self.output_dir / "temp"
        self.thumbnails_dir = self.output_dir / "thumbnails"
        self.platforms_dir = self.output_dir / "platforms"
        
        # Créer les sous-dossiers pour chaque plateforme
        self.tiktok_dir = self.platforms_dir / "tiktok"
        self.youtube_dir = self.platforms_dir / "youtube"
        self.instagram_dir = self.platforms_dir / "instagram"
        
        # Créer tous les dossiers
        for dir_path in [self.final_dir, self.temp_dir, self.thumbnails_dir, 
                        self.platforms_dir, self.tiktok_dir, self.youtube_dir, self.instagram_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.db = VideoDatabase()
        self.console = Console()
        
        # Initialiser les modules
        self.whisper = WhisperTranscriber()
        self.translator = TextTranslator()
        self.tts = TTSSimple()
        
        # Créer un TTS spécial pour les CTA avec Bark (gratuit)
        self.cta_tts = TTSSimple()
        self.cta_tts.tts_engine = "bark"  # Forcer l'utilisation de Bark pour les CTA
        
        # Vérifier FFmpeg
        self.ffmpeg_available = self._check_ffmpeg()
        
        # Templates pour différentes plateformes
        self.platform_templates = {
            'tiktok': {
                'aspect_ratio': '9:16',   # Corrigé : format 9:16 pour TikTok
                'duration_limit': 60,     # 60 secondes max pour un short
                'min_duration': 70,       # 70 secondes minimum (1min10)
                'subtitle_style': 'tiktok',
                'effects': ['zoom', 'text_animations', 'transitions', 'filters'],
                'output_dir': self.tiktok_dir
            },
            'youtube_shorts': {
                'aspect_ratio': '9:16',   # Format vertical pour YouTube Shorts
                'duration_limit': 60,     # 60 secondes max
                'min_duration': 70,       # 70 secondes minimum (1min10)
                'subtitle_style': 'youtube',
                'effects': ['zoom', 'text_animations', 'transitions'],
                'output_dir': self.youtube_dir
            },
            'instagram_reels': {
                'aspect_ratio': '9:16',   # Format vertical pour Instagram Reels
                'duration_limit': 90,     # 90 secondes max
                'min_duration': 70,       # 70 secondes minimum (1min10)
                'subtitle_style': 'instagram',
                'effects': ['zoom', 'text_animations', 'transitions', 'filters'],
                'output_dir': self.instagram_dir
            }
        }
    
    def _check_ffmpeg(self) -> bool:
        """Vérifie si FFmpeg est disponible"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def find_viral_moments(self, video_id: str) -> List[Dict]:
        """Trouve les moments viraux dans une vidéo"""
        try:
            # Récupérer la transcription
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT translated_text FROM whisper_texts 
                    WHERE video_id = ?
                ''', (video_id,))
                result = cursor.fetchone()
                
                if not result:
                    print(f"❌ Transcription non trouvée pour {video_id}")
                    return []
                
                text = result[0]
                
                # Diviser le texte en segments de 70-90 secondes (pour les shorts)
                segments = self._split_text_into_segments(text, max_duration=90)
                
                # Analyser chaque segment pour le potentiel viral
                viral_moments = []
                current_time = 0
                for i, segment in enumerate(segments):
                    if self._is_viral_potential(segment):
                        # Calculer la durée estimée du segment
                        estimated_duration = len(segment.split()) / 2.5  # ~2.5 mots par seconde
                        estimated_duration = max(estimated_duration, 70)  # Min 70 secondes
                        estimated_duration = min(estimated_duration, 90)  # Max 90 secondes
                        
                        viral_moments.append({
                            'title': f"Segment {i+1}",
                            'start_time': current_time,
                            'end_time': current_time + estimated_duration,
                            'text': segment,
                            'justification': "Segment avec potentiel viral détecté"
                        })
                    
                    # Avancer le temps pour le prochain segment
                    segment_duration = len(segment.split()) / 2.5
                    current_time += segment_duration
                
                return viral_moments
                
        except Exception as e:
            print(f"❌ Erreur lors de la recherche de moments viraux: {e}")
            return []
    
    def _split_text_into_segments(self, text: str, max_duration: int = 90) -> List[str]:
        """Divise le texte en segments de durée maximale"""
        words = text.split()
        segments = []
        current_segment = []
        current_length = 0
        
        for word in words:
            current_segment.append(word)
            current_length += len(word) + 1
            
            # Estimer la durée (environ 150 mots par minute)
            estimated_duration = (current_length / 150) * 60
            
            if estimated_duration >= max_duration:
                segments.append(' '.join(current_segment))
                current_segment = []
                current_length = 0
        
        if current_segment:
            segments.append(' '.join(current_segment))
        
        return segments
    
    def _is_viral_potential(self, text: str) -> bool:
        """Détermine si un segment a un potentiel viral"""
        # Mots-clés viraux
        viral_keywords = [
            'secret', 'révélation', 'choc', 'incroyable', 'jamais', 'toujours',
            'erreur', 'succès', 'échec', 'transformation', 'méthode', 'technique',
            'astuce', 'conseil', 'truc', 'hack', 'lifehack', 'productivité',
            'argent', 'richesse', 'succès', 'bonheur', 'amour', 'relation'
        ]
        
        text_lower = text.lower()
        viral_score = sum(1 for keyword in viral_keywords if keyword in text_lower)
        
        # Score basé sur la longueur et les mots-clés
        length_score = min(len(text.split()) / 50, 1.0)  # Normalisé à 1
        keyword_score = min(viral_score / 3, 1.0)  # Normalisé à 1
        
        total_score = (length_score + keyword_score) / 2
        return total_score > 0.3  # Seuil de potentiel viral
    
    def generate_subtitles(self, text: str, style: str = 'tiktok') -> str:
        """Génère des sous-titres stylisés"""
        # Créer un fichier SRT temporaire dans le bon répertoire
        subtitle_dir = Path("datas/subtitles")
        subtitle_dir.mkdir(parents=True, exist_ok=True)
        subtitle_path = subtitle_dir / f"subtitles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt"
        
        # Diviser le texte en phrases
        sentences = text.split('. ')
        
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            for i, sentence in enumerate(sentences, 1):
                if sentence.strip():
                    # Estimer le timing (environ 2 secondes par phrase)
                    start_time = i * 2
                    end_time = start_time + 3
                    
                    f.write(f"{i}\n")
                    f.write(f"{self._format_time(start_time)} --> {self._format_time(end_time)}\n")
                    f.write(f"{sentence.strip()}\n\n")
        
        return str(subtitle_path)
    
    def _debug_subtitles(self, subtitle_path: str):
        """Debug les sous-titres générés"""
        try:
            if os.path.exists(subtitle_path):
                print(f"🔍 Debug des sous-titres: {subtitle_path}")
                with open(subtitle_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print("📄 Contenu des sous-titres:")
                    print(content)
                    
                    # Vérifier les CTA
                    cta_count = content.count('🔥') + content.count('💯') + content.count('🚀') + content.count('⭐')
                    print(f"🎯 Nombre de CTA détectés: {cta_count}")
                    
                    # Vérifier le timing
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if '-->' in line:
                            print(f"⏰ Timing ligne {i+1}: {line.strip()}")
            else:
                print(f"❌ Fichier sous-titres non trouvé: {subtitle_path}")
        except Exception as e:
            print(f"❌ Erreur lors du debug des sous-titres: {e}")

    def generate_cta_subtitles(self, text: str, style: str = 'tiktok', audio_path: str = None) -> str:
        """Génère des sous-titres avec CTA pour inciter à s'abonner"""
        # Créer un fichier SRT temporaire dans le bon répertoire
        subtitle_dir = Path("datas/subtitles")
        subtitle_dir.mkdir(parents=True, exist_ok=True)
        subtitle_path = subtitle_dir / f"cta_subtitles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt"
        
        # Diviser le texte en phrases
        sentences = text.split('. ')
        
        # Récupérer la durée de l'audio TTS si disponible
        audio_duration = 0.0
        if audio_path and os.path.exists(audio_path):
            audio_duration = self._get_audio_duration(audio_path)
            print(f"🔊 Durée audio TTS: {audio_duration:.1f}s")
        
        # Si pas de durée audio, estimer (environ 2.5 mots par seconde)
        if audio_duration == 0.0:
            word_count = len(text.split())
            audio_duration = word_count / 2.5
            print(f"🔊 Durée audio estimée: {audio_duration:.1f}s")
        
        # CTA à ajouter à la fin
        cta_texts = {
            'tiktok': [
                "🔥 Abonne-toi pour plus de contenu comme ça !",
                "💯 Suis-moi pour du contenu exclusif !",
                "🚀 Abonne-toi et active la cloche !",
                "⭐ Like et abonne-toi pour plus !"
            ],
            'youtube_shorts': [
                "🔔 Abonne-toi et active la cloche !",
                "👍 Like et abonne-toi pour plus de contenu !",
                "💎 Rejoins la communauté !",
                "🎯 Abonne-toi pour ne rien manquer !"
            ],
            'instagram_reels': [
                "✨ Suis-moi pour plus de contenu !",
                "🔥 Abonne-toi et active les notifications !",
                "💫 Double tap et abonne-toi !",
                "🌟 Suis-moi pour du contenu exclusif !"
            ]
        }
        
        cta_list = cta_texts.get(style, cta_texts['tiktok'])
        
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            subtitle_count = 1
            
            # Calculer le timing pour chaque phrase
            total_sentences = len([s for s in sentences if s.strip()])
            if total_sentences > 0:
                # Réserver 50% du temps pour les CTA (la moitié de la vidéo)
                cta_time = min(audio_duration * 0.5, 35.0)  # Max 35 secondes pour les CTA
                content_time = audio_duration - cta_time
                time_per_sentence = content_time / total_sentences
                
                # Ajouter les phrases du contenu principal
                current_time = 0.0
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        start_time = current_time
                        end_time = current_time + time_per_sentence
                        
                        f.write(f"{subtitle_count}\n")
                        f.write(f"{self._format_time(start_time)} --> {self._format_time(end_time)}\n")
                        f.write(f"{sentence.strip()}\n\n")
                        subtitle_count += 1
                        current_time += time_per_sentence
                
                # Ajouter les CTA à la fin avec plus de temps et plus tôt
                cta_duration = cta_time / len(cta_list)
                cta_start_time = content_time
                
                # S'assurer que les CTA ne dépassent pas la durée de la vidéo
                max_video_duration = 70.0  # Durée maximale des shorts
                if cta_start_time + cta_time > max_video_duration:
                    # Ajuster le timing pour que les CTA s'affichent dans la durée de la vidéo
                    cta_start_time = max_video_duration - cta_time
                    if cta_start_time < 0:
                        cta_start_time = 0
                        cta_duration = max_video_duration / len(cta_list)
                
                # S'assurer que les CTA commencent au moins à 35 secondes
                if cta_start_time > 35:
                    cta_start_time = 35
                    cta_duration = (max_video_duration - cta_start_time) / len(cta_list)
                
                for cta in cta_list:
                    f.write(f"{subtitle_count}\n")
                    f.write(f"{self._format_time(cta_start_time)} --> {self._format_time(cta_start_time + cta_duration)}\n")
                    f.write(f"{cta}\n\n")
                    subtitle_count += 1
                    cta_start_time += cta_duration
        
        return str(subtitle_path)
    
    def _format_time(self, seconds: float) -> str:
        """Formate le temps au format SRT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def apply_visual_effects(self, video_path: str, output_path: str, effects: List[str]) -> bool:
        """Applique des effets visuels à la vidéo"""
        try:
            if not self.ffmpeg_available:
                print("⚠️ FFmpeg non disponible, pas d'effets appliqués")
                return False
            
            # Pour l'instant, on copie simplement la vidéo pour éviter les problèmes de durée
            # TODO: Implémenter des effets qui préservent la durée
            print("⚠️ Effets visuels temporairement désactivés pour préserver la durée")
            cmd = [
                'ffmpeg', '-i', video_path,
                '-c:v', 'libx264', '-c:a', 'aac',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Erreur lors de l'application des effets: {e}")
            return False
    
    def generate_thumbnail(self, video_path: str, title: str) -> Optional[str]:
        """Génère une thumbnail pour la vidéo"""
        try:
            if not self.ffmpeg_available:
                return None
            
            thumbnail_path = self.thumbnails_dir / f"thumbnail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            
            # Extraire une frame au milieu de la vidéo
            cmd = [
                'ffmpeg', '-i', video_path, '-ss', '00:00:05', 
                '-vframes', '1', '-y', str(thumbnail_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return str(thumbnail_path)
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération de thumbnail: {e}")
            return None
    
    def create_short(self, video_id: str, platform: str = 'tiktok') -> Optional[str]:
        """Crée un short complet pour une plateforme spécifique"""
        try:
            print(f"🎬 Création d'un short {platform} pour {video_id}")
            
            # Initialiser les variables
            trimmed_video_path = None
            
            # Récupérer les données de la vidéo
            video_data = self._get_video_data(video_id)
            if not video_data:
                return None
            
            # Vérifier la durée de la vidéo
            video_duration = self._get_video_duration(video_data['video_path'])
            min_duration = self.platform_templates[platform]['min_duration']
            max_duration = self.platform_templates[platform]['duration_limit']
            
            # Trouver les moments viraux
            viral_moments = self.find_viral_moments(video_id)
            if not viral_moments:
                print(f"❌ Aucun moment viral trouvé pour {video_id}")
                return None
            
            # Prendre le premier moment viral
            moment = viral_moments[0]
            
            # Déterminer la durée du short basée sur le moment viral ou la durée minimale
            moment_duration = moment['end_time'] - moment['start_time']
            if video_duration < min_duration:
                # Pour les vidéos courtes, utiliser la durée minimale
                short_duration = min_duration
            else:
                # Pour les vidéos longues, utiliser la durée du moment viral
                short_duration = min(max_duration, moment_duration)
                if short_duration < min_duration:
                    short_duration = min_duration
            
            # S'assurer que le start_time ne dépasse pas la durée de la vidéo
            if moment['start_time'] >= video_duration:
                moment['start_time'] = 0
                short_duration = min(max_duration, video_duration)
            
            # S'assurer que start_time + duration ne dépasse pas la durée de la vidéo
            if moment['start_time'] + short_duration > video_duration:
                moment['start_time'] = max(0, video_duration - short_duration)
                short_duration = min(short_duration, video_duration - moment['start_time'])
            
            # S'assurer que la durée minimale est respectée
            if short_duration < min_duration:
                print(f"⚠️ Durée trop courte ({short_duration}s), extension à {min_duration}s")
                short_duration = min_duration
                # Ajuster le start_time si nécessaire
                if moment['start_time'] + short_duration > video_duration:
                    moment['start_time'] = max(0, video_duration - short_duration)
            
            print(f"📏 Durée du moment viral: {moment_duration:.1f}s")
            print(f"📏 Durée du short: {short_duration:.1f}s (min: {min_duration}s, max: {max_duration}s)")
            print(f"📏 Start time: {moment['start_time']:.1f}s")
            
            # TOUJOURS découper la vidéo pour créer un short
            print(f"✂️ Découpage de la vidéo de {video_duration}s à {short_duration}s")
            trimmed_video_path = str(self.temp_dir / f"trimmed_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
            
            # Si la vidéo est trop courte, l'étendre d'abord
            if video_duration < short_duration:
                extended_video_path = str(self.temp_dir / f"extended_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                if not self._extend_short_video(video_data['video_path'], short_duration, extended_video_path):
                    print("❌ Échec de l'extension de la vidéo")
                    return None
                video_data['video_path'] = extended_video_path
                video_duration = short_duration
            
            if not self._trim_video_for_short(video_data['video_path'], moment['start_time'], short_duration, trimmed_video_path):
                print("❌ Échec du découpage de la vidéo")
                return None
            video_data['video_path'] = trimmed_video_path
            
            # Générer les CTA audio et les ajouter à l'audio original
            print("🎤 Génération des CTA audio...")
            cta_audio_path = self.generate_cta_audio(self.platform_templates[platform]['subtitle_style'])
            
            if cta_audio_path:
                # Concaténer l'audio original avec les CTA
                final_audio_path = str(self.temp_dir / f"audio_with_cta_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.aac")
                
                if self._concatenate_audio_with_cta(video_data['audio_path'], cta_audio_path, final_audio_path):
                    video_data['audio_path'] = final_audio_path
                    print(f"✅ Audio avec CTA généré: {final_audio_path}")
                else:
                    print("⚠️ Échec de la concaténation audio, utilisation de l'audio original")
            else:
                print("⚠️ Échec de la génération des CTA audio, utilisation de l'audio original")
            
            # Générer les sous-titres simples (sans CTA)
            subtitle_path = self.generate_subtitles(moment['text'], self.platform_templates[platform]['subtitle_style'])
            
            # Debug des sous-titres
            self._debug_subtitles(subtitle_path)
            
            # Créer le short final dans le dossier de la plateforme
            platform_output_dir = self.platform_templates[platform]['output_dir']
            output_path = platform_output_dir / f"short_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            
            # Construire la commande FFmpeg avec le format vertical 9:16
            subtitle_path_escaped = subtitle_path.replace('\\', '/').replace(':', '\\:')
            
            # Commande FFmpeg améliorée pour les sous-titres
            cmd = [
                'ffmpeg', '-i', video_data['video_path'],
                '-i', video_data['audio_path'],
                '-vf', f'subtitles={subtitle_path_escaped}:force_style=\'FontSize=28,PrimaryColour=&Hffffff&,OutlineColour=&H000000&,BorderStyle=3,Alignment=2\',scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2',
                '-c:v', 'libx264', '-c:a', 'aac',
                '-map', '0:v:0', '-map', '1:a:0',  # Mapper vidéo et audio séparément
                '-shortest', '-y', str(output_path)
            ]
            
            if self.ffmpeg_available:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    # Appliquer les effets visuels
                    final_path = self.final_dir / f"final_{platform}_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                    if self.apply_visual_effects(str(output_path), str(final_path), self.platform_templates[platform]['effects']):
                        # Générer la thumbnail
                        thumbnail_path = self.generate_thumbnail(str(final_path), moment['title'])
                        
                        # Sauvegarder dans la base de données
                        self._save_short_record(video_id, str(final_path), platform, moment, thumbnail_path)
                        
                        # Tracker dans l'analytics
                        self._track_analytics(video_id, platform, str(final_path), short_duration)
                        
                        print(f"✅ Short {platform} créé ({short_duration:.1f}s): {final_path}")
                        return str(final_path)
                    else:
                        print(f"✅ Short {platform} créé (sans effets): {output_path}")
                        return str(output_path)
                else:
                    print(f"❌ Erreur lors de la création du short: {result.stderr}")
                    return None
            else:
                print("❌ FFmpeg non disponible")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de la création du short: {e}")
            return None
        finally:
            # Nettoyer le fichier temporaire
            if trimmed_video_path and os.path.exists(trimmed_video_path):
                try:
                    os.remove(trimmed_video_path)
                except:
                    pass
    
    def _get_video_data(self, video_id: str) -> Optional[Dict]:
        """Récupère les données de la vidéo"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT v.title, tts.audio_path
                    FROM videos v
                    INNER JOIN tts_outputs tts ON v.video_id = tts.video_id
                    WHERE v.video_id = ?
                ''', (video_id,))
                
                result = cursor.fetchone()
                if result:
                    title, audio_path = result
                    video_path = self._find_video_file(video_id)
                    
                    if video_path and audio_path:
                        return {
                            'title': title,
                            'video_path': video_path,
                            'audio_path': audio_path
                        }
                
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des données: {e}")
            return None
    
    def _find_video_file(self, video_id: str) -> Optional[str]:
        """Trouve le fichier vidéo"""
        # Chercher dans différents emplacements possibles
        possible_paths = [
            f"datas/videos/{video_id}.mp4",
            f"assets/videos/{video_id}.mp4",
            f"output/{video_id}.mp4",
            f"datas/final_videos/{video_id}.mp4",
            f"datas/final_videos/final_{video_id}.mp4"  # Ajout du préfixe final_
        ]
        
        # Chercher dans les dossiers de thèmes
        theme_dirs = [
            "assets/videos/motivation",
            "assets/videos/success", 
            "assets/videos/business",
            "assets/videos/health",
            "assets/videos/mindset",
            "assets/videos/leadership",
            "assets/videos/failure",
            "assets/videos/growth",
            "assets/videos/discipline",
            "assets/videos/philosophy"
        ]
        
        # Vérifier les chemins directs
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Chercher dans les dossiers de thèmes
        for theme_dir in theme_dirs:
            if os.path.exists(theme_dir):
                for file in os.listdir(theme_dir):
                    if file.startswith(video_id) and file.endswith('.mp4'):
                        return os.path.join(theme_dir, file)
        
        # Chercher récursivement dans tous les dossiers
        search_dirs = ["datas", "assets", "output"]
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if (file.startswith(video_id) or file.startswith(f"final_{video_id}")) and file.endswith('.mp4'):
                            return os.path.join(root, file)
        
        return None
    
    def _save_short_record(self, video_id: str, short_path: str, platform: str, moment: Dict, thumbnail_path: Optional[str] = None):
        """Sauvegarde l'enregistrement du short dans la base de données"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO shorts (
                        video_id, platform, short_path, thumbnail_path, 
                        title, start_time, end_time, justification, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ''', (
                    video_id, platform, short_path, thumbnail_path,
                    moment['title'], moment['start_time'], moment['end_time'],
                    moment['justification']
                ))
                conn.commit()
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
    
    def batch_create_shorts(self, platform: str = 'tiktok', limit: int = 10):
        """Crée des shorts en lot"""
        try:
            # Récupérer les vidéos avec TTS
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT v.video_id, v.title
                    FROM videos v
                    INNER JOIN tts_outputs tts ON v.video_id = tts.video_id
                    LEFT JOIN shorts s ON v.video_id = s.video_id AND s.platform = ?
                    WHERE s.video_id IS NULL
                    ORDER BY v.created_at DESC
                    LIMIT ?
                ''', (platform, limit))
                
                videos = cursor.fetchall()
            
            if not videos:
                print(f"✅ Toutes les vidéos ont déjà des shorts {platform}")
                return
            
            print(f"🎬 Création de {len(videos)} shorts {platform}...")
            
            success_count = 0
            for video_id, title in videos:
                print(f"🎬 Traitement: {title[:50]}...")
                if self.create_short(video_id, platform):
                    success_count += 1
            
            print(f"✅ Shorts créés: {success_count}/{len(videos)}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création en lot: {e}")

    def _get_audio_duration(self, audio_path: str) -> float:
        """Récupère la durée d'un fichier audio en secondes"""
        try:
            if not self.ffmpeg_available:
                return 0.0
            
            # Utiliser FFprobe pour récupérer la durée
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return duration
            else:
                print(f"⚠️ Impossible de récupérer la durée de {audio_path}")
                return 0.0
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération de la durée audio: {e}")
            return 0.0

    def _get_video_duration(self, video_path: str) -> float:
        """Récupère la durée d'une vidéo en secondes"""
        try:
            if not self.ffmpeg_available:
                return 0.0
            
            # Utiliser FFprobe pour récupérer la durée
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return duration
            else:
                print(f"⚠️ Impossible de récupérer la durée de {video_path}")
                return 0.0
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération de la durée: {e}")
            return 0.0

    def _track_analytics(self, video_id: str, platform: str, short_path: str, duration: float):
        """Track la création d'un short dans l'analytics"""
        try:
            from montage.analytics import ShortsAnalytics
            analytics = ShortsAnalytics()
            
            # Calculer la taille du fichier
            file_size = os.path.getsize(short_path) if os.path.exists(short_path) else 0
            
            analytics.track_short_creation(video_id, platform, short_path, duration, file_size)
            
        except Exception as e:
            print(f"⚠️ Erreur lors du tracking analytics: {e}")

    def _trim_video_for_short(self, video_path: str, start_time: float, duration: float, output_path: str) -> bool:
        """Découpe une vidéo pour créer un short de la durée spécifiée"""
        try:
            if not self.ffmpeg_available:
                return False
            
            print(f"🔧 Découpage: {video_path} de {start_time}s à {start_time + duration}s (durée: {duration}s)")
            
            # Commande FFmpeg pour découper la vidéo
            cmd = [
                'ffmpeg', '-i', video_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c:v', 'libx264', '-c:a', 'aac',
                '-avoid_negative_ts', 'make_zero',
                '-y', output_path
            ]
            
            print(f"🔧 Commande FFmpeg: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Erreur FFmpeg: {result.stderr}")
                return False
            
            # Vérifier la durée du fichier créé
            if os.path.exists(output_path):
                check_cmd = [
                    'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                    '-of', 'csv=p=0', output_path
                ]
                check_result = subprocess.run(check_cmd, capture_output=True, text=True)
                if check_result.returncode == 0:
                    actual_duration = float(check_result.stdout.strip())
                    print(f"✅ Vidéo découpée: {actual_duration:.1f}s (attendue: {duration:.1f}s)")
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erreur lors du découpage de la vidéo: {e}")
            return False

    def _extend_short_video(self, video_path: str, target_duration: float, output_path: str) -> bool:
        """Étend une vidéo courte en répétant le contenu"""
        try:
            if not self.ffmpeg_available:
                return False
            
            print(f"🔧 Extension de la vidéo à {target_duration}s")
            
            # Calculer combien de fois répéter la vidéo
            current_duration = self._get_video_duration(video_path)
            repeat_count = int(target_duration / current_duration) + 1
            
            # Créer une liste de fichiers pour la concaténation
            concat_file = str(self.temp_dir / f"concat_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            # Utiliser des chemins absolus
            video_path_absolute = os.path.abspath(video_path).replace('\\', '/')
            
            with open(concat_file, 'w', encoding='utf-8') as f:
                for _ in range(repeat_count):
                    f.write(f"file '{video_path_absolute}'\n")
            
            # Commande FFmpeg pour concaténer et découper à la durée cible
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', concat_file,
                '-t', str(target_duration),
                '-c:v', 'libx264', '-c:a', 'aac',
                '-y', output_path
            ]
            
            print(f"🔧 Commande FFmpeg: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Erreur FFmpeg: {result.stderr}")
            
            # Nettoyer le fichier temporaire
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extension de la vidéo: {e}")
            return False

    def generate_cta_audio(self, style: str = 'tiktok') -> Optional[str]:
        """Génère un fichier audio avec les CTA pour inciter à s'abonner"""
        try:
            # CTA audio à ajouter à la fin
            cta_texts = {
                'tiktok': [
                    "Abonne-toi pour plus de contenu comme ça !",
                    "Suis-moi pour du contenu exclusif !",
                    "Abonne-toi et active la cloche !",
                    "Like et abonne-toi pour plus !"
                ],
                'youtube_shorts': [
                    "Abonne-toi et active la cloche !",
                    "Like et abonne-toi pour plus de contenu !",
                    "Rejoins la communauté !",
                    "Abonne-toi pour ne rien manquer !"
                ],
                'instagram_reels': [
                    "Suis-moi pour plus de contenu !",
                    "Abonne-toi et active les notifications !",
                    "Double tap et abonne-toi !",
                    "Suis-moi pour du contenu exclusif !"
                ]
            }
            
            cta_list = cta_texts.get(style, cta_texts['tiktok'])
            
            # Créer le dossier pour les CTA audio
            cta_dir = Path("datas/cta_audio")
            cta_dir.mkdir(parents=True, exist_ok=True)
            
            # Générer l'audio pour chaque CTA
            cta_audio_files = []
            for i, cta in enumerate(cta_list):
                # Utiliser TTS pour générer l'audio du CTA
                cta_audio_path = self.cta_tts.generate_audio_from_text(cta)
                if cta_audio_path:
                    cta_audio_files.append(cta_audio_path)
                    print(f"🎤 CTA audio généré: {cta}")
                else:
                    print(f"❌ Échec de la génération audio pour: {cta}")
            
            if not cta_audio_files:
                print("❌ Aucun CTA audio généré")
                return None
            
            # Concaténer tous les CTA audio
            final_cta_path = cta_dir / f"final_cta_{style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.aac"
            
            if len(cta_audio_files) == 1:
                # Si un seul CTA, juste le copier
                import shutil
                shutil.copy2(cta_audio_files[0], final_cta_path)
            else:
                # Créer une liste de fichiers pour la concaténation
                concat_file = cta_dir / f"cta_concat_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                with open(concat_file, 'w', encoding='utf-8') as f:
                    for audio_file in cta_audio_files:
                        # Utiliser des chemins absolus
                        audio_path_absolute = os.path.abspath(audio_file).replace('\\', '/')
                        f.write(f"file '{audio_path_absolute}'\n")
                
                # Commande FFmpeg pour concaténer les CTA
                cmd = [
                    'ffmpeg', '-f', 'concat', '-safe', '0',
                    '-i', str(concat_file),
                    '-c:a', 'aac',  # Convertir en AAC pour la compatibilité
                    '-y', str(final_cta_path)
                ]
                
                print(f"🔧 Concaténation des CTA audio...")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"❌ Erreur lors de la concaténation des CTA: {result.stderr}")
                    return None
                
                # Nettoyer le fichier temporaire
                if concat_file.exists():
                    concat_file.unlink()
            
            # Nettoyer les fichiers CTA individuels
            for audio_file in cta_audio_files:
                try:
                    os.remove(audio_file)
                except:
                    pass
            
            print(f"✅ CTA audio final généré: {final_cta_path}")
            return str(final_cta_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération des CTA audio: {e}")
            return None

    def _concatenate_audio_with_cta(self, original_audio_path: str, cta_audio_path: str, output_path: str) -> bool:
        """Concatène l'audio original avec les CTA audio"""
        try:
            if not self.ffmpeg_available:
                return False
            
            print(f"🔧 Concaténation audio original + CTA...")
            
            # Créer une liste de fichiers pour la concaténation
            concat_file = str(self.temp_dir / f"audio_concat_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            # Utiliser des chemins absolus
            original_audio_absolute = os.path.abspath(original_audio_path).replace('\\', '/')
            cta_audio_absolute = os.path.abspath(cta_audio_path).replace('\\', '/')
            
            with open(concat_file, 'w', encoding='utf-8') as f:
                f.write(f"file '{original_audio_absolute}'\n")
                f.write(f"file '{cta_audio_absolute}'\n")
            
            # Commande FFmpeg pour concaténer
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', concat_file,
                '-c:a', 'aac',  # Convertir en AAC pour la compatibilité
                '-y', output_path
            ]
            
            print(f"🔧 Commande FFmpeg: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Erreur FFmpeg: {result.stderr}")
                return False
            
            # Nettoyer le fichier temporaire
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la concaténation audio: {e}")
            return False

    def cleanup_temp_files(self):
        """Nettoie les fichiers temporaires"""
        try:
            print("🧹 Nettoyage des fichiers temporaires...")
            temp_files = list(self.temp_dir.glob("*"))
            cleaned_count = 0
            
            for file_path in temp_files:
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        cleaned_count += 1
                except Exception as e:
                    print(f"⚠️ Impossible de supprimer {file_path}: {e}")
            
            print(f"✅ {cleaned_count} fichiers temporaires supprimés")
            
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage: {e}")
    
    def list_shorts(self, platform: str = None):
        """Liste les shorts créés de manière organisée"""
        try:
            console = Console()
            
            if platform:
                # Lister les shorts d'une plateforme spécifique
                platform_dir = self.platform_templates.get(platform, {}).get('output_dir')
                if not platform_dir or not platform_dir.exists():
                    print(f"❌ Aucun short trouvé pour {platform}")
                    return
                
                shorts = list(platform_dir.glob("*.mp4"))
                if not shorts:
                    print(f"❌ Aucun short trouvé pour {platform}")
                    return
                
                table = Table(title=f"📊 Shorts {platform.upper()}")
                table.add_column("Fichier", style="cyan")
                table.add_column("Taille", style="green")
                table.add_column("Date", style="yellow")
                
                for short in sorted(shorts, key=lambda x: x.stat().st_mtime, reverse=True):
                    size_mb = short.stat().st_size / (1024 * 1024)
                    date = datetime.fromtimestamp(short.stat().st_mtime)
                    table.add_row(
                        short.name,
                        f"{size_mb:.1f} MB",
                        date.strftime("%Y-%m-%d %H:%M")
                    )
                
                console.print(table)
                
            else:
                # Lister tous les shorts par plateforme
                table = Table(title="📊 Shorts par Plateforme")
                table.add_column("Plateforme", style="cyan")
                table.add_column("Nombre", style="green")
                table.add_column("Dernier", style="yellow")
                
                for platform_name, template in self.platform_templates.items():
                    platform_dir = template['output_dir']
                    if platform_dir.exists():
                        shorts = list(platform_dir.glob("*.mp4"))
                        if shorts:
                            latest = max(shorts, key=lambda x: x.stat().st_mtime)
                            latest_date = datetime.fromtimestamp(latest.stat().st_mtime)
                            table.add_row(
                                platform_name.upper(),
                                str(len(shorts)),
                                latest_date.strftime("%Y-%m-%d %H:%M")
                            )
                        else:
                            table.add_row(platform_name.upper(), "0", "-")
                    else:
                        table.add_row(platform_name.upper(), "0", "-")
                
                console.print(table)
                
        except Exception as e:
            print(f"❌ Erreur lors de la liste des shorts: {e}")
    
    def get_short_stats(self) -> Dict:
        """Retourne les statistiques des shorts"""
        try:
            stats = {
                'total_shorts': 0,
                'by_platform': {},
                'total_size_mb': 0,
                'latest_short': None
            }
            
            for platform_name, template in self.platform_templates.items():
                platform_dir = template['output_dir']
                if platform_dir.exists():
                    shorts = list(platform_dir.glob("*.mp4"))
                    platform_size = sum(short.stat().st_size for short in shorts)
                    
                    stats['by_platform'][platform_name] = {
                        'count': len(shorts),
                        'size_mb': platform_size / (1024 * 1024)
                    }
                    stats['total_shorts'] += len(shorts)
                    stats['total_size_mb'] += platform_size / (1024 * 1024)
                    
                    if shorts:
                        latest = max(shorts, key=lambda x: x.stat().st_mtime)
                        if not stats['latest_short'] or latest.stat().st_mtime > stats['latest_short']['mtime']:
                            stats['latest_short'] = {
                                'platform': platform_name,
                                'file': latest.name,
                                'mtime': latest.stat().st_mtime,
                                'date': datetime.fromtimestamp(latest.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Erreur lors du calcul des statistiques: {e}")
            return {}

def create_shorts_table():
    """Crée la table shorts dans la base de données"""
    try:
        db = VideoDatabase()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shorts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    short_path TEXT NOT NULL,
                    thumbnail_path TEXT,
                    title TEXT,
                    start_time REAL,
                    end_time REAL,
                    justification TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            conn.commit()
            print("✅ Table shorts créée")
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table: {e}")

def main():
    """Interface CLI pour le générateur de shorts"""
    console = Console()
    title = Panel.fit("🎬 Générateur de Shorts Automatiques", style="bold blue")
    console.print(title)
    
    generator = ShortsGenerator()
    
    while True:
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="white")
        table.add_row("1", "🎬 Créer un short TikTok")
        table.add_row("2", "📺 Créer un short YouTube")
        table.add_row("3", "📱 Créer un Reel Instagram")
        table.add_row("4", "🔄 Création en lot")
        table.add_row("5", "📊 Afficher les shorts créés")
        table.add_row("6", "🧹 Nettoyer les fichiers temporaires")
        table.add_row("7", "📈 Statistiques des shorts")
        table.add_row("0", "❌ Quitter")
        console.print(table)
        
        choice = input("\n🎯 Votre choix (0-7): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            video_id = input("🎬 ID de la vidéo: ").strip()
            generator.create_short(video_id, 'tiktok')
        elif choice == "2":
            video_id = input("🎬 ID de la vidéo: ").strip()
            generator.create_short(video_id, 'youtube_shorts')
        elif choice == "3":
            video_id = input("🎬 ID de la vidéo: ").strip()
            generator.create_short(video_id, 'instagram_reels')
        elif choice == "4":
            platform = input("🎬 Plateforme (tiktok/youtube_shorts/instagram_reels): ").strip()
            limit = int(input("🎬 Nombre de shorts (défaut: 10): ").strip() or "10")
            generator.batch_create_shorts(platform, limit)
        elif choice == "5":
            platform = input("🎬 Plateforme spécifique (laissez vide pour toutes): ").strip()
            if platform:
                generator.list_shorts(platform)
            else:
                generator.list_shorts()
        elif choice == "6":
            generator.cleanup_temp_files()
        elif choice == "7":
            stats = generator.get_short_stats()
            if stats:
                console.print(f"\n📈 Statistiques des Shorts:")
                console.print(f"Total: {stats['total_shorts']} shorts")
                console.print(f"Taille totale: {stats['total_size_mb']:.1f} MB")
                if stats['latest_short']:
                    console.print(f"Dernier: {stats['latest_short']['platform']} - {stats['latest_short']['file']} ({stats['latest_short']['date']})")
                
                for platform, data in stats['by_platform'].items():
                    console.print(f"{platform.upper()}: {data['count']} shorts ({data['size_mb']:.1f} MB)")
            else:
                console.print("❌ Aucune statistique disponible")
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    create_shorts_table()
    main() 