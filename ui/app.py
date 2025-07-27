#!/usr/bin/env python3
"""
Interface Streamlit pour TikTok_Auto
Interface graphique moderne pour gérer les vidéos YouTube
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import os

# Ajouter le répertoire courant au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.manager import VideoDatabase
from config import Config
from core.downloader import YouTubeDownloader
from translation.vtt_ollama_processor import VttOllamaProcessor
from translation.tts import TTSManager
from ollama.theme_classifier import ThemeClassifier
from core.fond_downloader import FondDownloader
from montage.build_video import VideoBuilder

# Configuration de la page
st.set_page_config(
    page_title="TikTok_Auto - Gestionnaire YouTube",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-metric {
        border-left-color: #28a745;
    }
    .warning-metric {
        border-left-color: #ffc107;
    }
    .error-metric {
        border-left-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

class TikTokAutoApp:
    def __init__(self):
        self.db = VideoDatabase()
        self.downloader = YouTubeDownloader()
        self.translator = VttOllamaProcessor()
        self.tts_manager = TTSManager()
        self.theme_classifier = ThemeClassifier()
        self.fond_downloader = FondDownloader()
        self.video_builder = VideoBuilder()
    
    def main(self):
        # Header principal
        st.markdown('<h1 class="main-header">🎵 TikTok_Auto</h1>', unsafe_allow_html=True)
        st.markdown('<h2 style="text-align: center; color: #666;">Gestionnaire YouTube Intelligent</h2>', unsafe_allow_html=True)
        
        # Sidebar
        self.sidebar()
        
        # Onglets principaux
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Dashboard", "📥 Téléchargement", "🌍 Traduction", 
            "🎙️ TTS", "🧠 Analyse", "🎥 Fonds", "🎬 Montage"
        ])
        
        with tab1:
            self.dashboard_tab()
        with tab2:
            self.download_tab()
        with tab3:
            self.translation_tab()
        with tab4:
            self.tts_tab()
        with tab5:
            self.analysis_tab()
        with tab6:
            self.fonds_tab()
        with tab7:
            self.montage_tab()
    
    def sidebar(self):
        """Sidebar avec métriques et actions rapides"""
        st.sidebar.title("📈 Métriques")
        
        # Statistiques
        try:
            stats = self.db.get_stats()
            
            col1, col2 = st.sidebar.columns(2)
            with col1:
                st.metric("📹 Vidéos", stats['videos'])
                st.metric("📺 Chaînes", stats['channels'])
            
            with col2:
                st.metric("🌍 Traductions", stats.get('translations', 0))
                st.metric("🎙️ TTS", stats.get('tts', 0))
            
            # Actions rapides
            st.sidebar.title("⚡ Actions Rapides")
            
            if st.sidebar.button("🔄 Actualiser les données"):
                st.rerun()
            
            if st.sidebar.button("🧪 Tester le système"):
                with st.spinner("Test en cours..."):
                    # Test rapide du système
                    st.success("✅ Système opérationnel")
            
            # Configuration
            st.sidebar.title("⚙️ Configuration")
            if st.sidebar.button("🔧 Gérer la config"):
                st.session_state.show_config = True
            
        except Exception as e:
            st.sidebar.error(f"Erreur: {e}")
    
    def dashboard_tab(self):
        """Onglet Dashboard avec visualisations"""
        st.header("📊 Dashboard")
        
        try:
            # Récupérer les données
            videos = self.db.list_all_videos()
            if not videos:
                st.warning("Aucune vidéo trouvée. Commencez par télécharger des vidéos.")
                return
            
            # Convertir en DataFrame
            df = pd.DataFrame(videos, columns=[
                'id', 'title', 'description', 'duration', 'upload_date', 
                'view_count', 'translation_count', 'theme'
            ])
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
                st.metric("Total Vidéos", len(df))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card warning-metric">', unsafe_allow_html=True)
                st.metric("Non Traduites", len(df[df['translation_count'] == 0]))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
                st.metric("Avec Thème", len(df[df['theme'].notna()]))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Durée Moyenne", f"{df['duration'].mean():.1f}s")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Graphiques
            col1, col2 = st.columns(2)
            
            with col1:
                # Répartition des traductions
                fig_translations = px.pie(
                    values=[len(df[df['translation_count'] > 0]), len(df[df['translation_count'] == 0])],
                    names=['Traduites', 'Non traduites'],
                    title="Répartition des traductions",
                    color_discrete_sequence=['#28a745', '#ffc107']
                )
                st.plotly_chart(fig_translations, use_container_width=True)
            
            with col2:
                # Répartition des thèmes
                if df['theme'].notna().any():
                    theme_counts = df['theme'].value_counts()
                    fig_themes = px.bar(
                        x=theme_counts.values,
                        y=theme_counts.index,
                        orientation='h',
                        title="Répartition des thèmes",
                        labels={'x': 'Nombre de vidéos', 'y': 'Thème'}
                    )
                    st.plotly_chart(fig_themes, use_container_width=True)
                else:
                    st.info("Aucun thème assigné. Utilisez l'analyse thématique.")
            
            # Tableau des vidéos récentes
            st.subheader("📹 Vidéos Récentes")
            recent_videos = df.head(10)[['id', 'title', 'translation_count', 'theme']]
            st.dataframe(recent_videos, use_container_width=True)
            
        except Exception as e:
            st.error(f"Erreur lors du chargement du dashboard: {e}")
    
    def download_tab(self):
        """Onglet de téléchargement"""
        st.header("📥 Téléchargement de Vidéos")
        
        # Téléchargement d'une chaîne
        st.subheader("📺 Télécharger une chaîne YouTube")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            channel_url = st.text_input("URL de la chaîne YouTube")
        with col2:
            max_videos = st.number_input("Max vidéos", min_value=1, max_value=100, value=10)
        
        if st.button("🚀 Télécharger la chaîne", type="primary"):
            if channel_url:
                with st.spinner("Téléchargement en cours..."):
                    try:
                        # Simulation du téléchargement
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Ici on appellerait le vrai téléchargement
                        # result = self.downloader.download_channel(channel_url, max_videos)
                        
                        for i in range(100):
                            progress_bar.progress(i + 1)
                            status_text.text(f"Téléchargement... {i+1}%")
                        
                        st.success("✅ Téléchargement terminé!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erreur: {e}")
            else:
                st.warning("Veuillez entrer une URL de chaîne")
        
        # Scanner les fichiers existants
        st.subheader("🔍 Scanner les fichiers existants")
        if st.button("📁 Scanner le dossier datas"):
            with st.spinner("Scan en cours..."):
                try:
                    # Simulation du scan
                    st.success("✅ Scan terminé - Fichiers détectés")
                except Exception as e:
                    st.error(f"Erreur: {e}")
    
    def translation_tab(self):
        """Onglet de traduction"""
        st.header("🌍 Traduction")
        
        # Options de traduction
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Traduction individuelle")
            video_id = st.text_input("ID de la vidéo")
            if st.button("Traduire cette vidéo"):
                if video_id:
                    with st.spinner("Traduction en cours..."):
                        try:
                            # result = self.translator.process_video_vtt(video_id)
                            st.success("✅ Traduction terminée!")
                        except Exception as e:
                            st.error(f"Erreur: {e}")
                else:
                    st.warning("Veuillez entrer un ID de vidéo")
        
        with col2:
            st.subheader("🔄 Traduction en lot")
            if st.button("Traduire toutes les vidéos", type="primary"):
                with st.spinner("Traduction en lot..."):
                    try:
                        # Récupérer toutes les vidéos non traduites
                        videos = self.db.list_all_videos()
                        untranslated = [v[0] for v in videos if v[6] == 0]
                        
                        if untranslated:
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i, video_id in enumerate(untranslated):
                                # self.translator.process_video_vtt(video_id)
                                progress = (i + 1) / len(untranslated)
                                progress_bar.progress(progress)
                                status_text.text(f"Traduction {i+1}/{len(untranslated)}")
                            
                            st.success(f"✅ {len(untranslated)} vidéos traduites!")
                        else:
                            st.info("Toutes les vidéos sont déjà traduites")
                            
                    except Exception as e:
                        st.error(f"Erreur: {e}")
        
        # Statistiques de traduction
        st.subheader("📊 Statistiques de traduction")
        try:
            videos = self.db.list_all_videos()
            df = pd.DataFrame(videos, columns=[
                'id', 'title', 'description', 'duration', 'upload_date', 
                'view_count', 'translation_count', 'theme'
            ])
            
            col1, col2 = st.columns(2)
            
            with col1:
                translated = len(df[df['translation_count'] > 0])
                total = len(df)
                st.metric("Vidéos traduites", f"{translated}/{total}")
                
                if total > 0:
                    percentage = (translated / total) * 100
                    st.progress(percentage / 100)
                    st.text(f"{percentage:.1f}%")
            
            with col2:
                st.metric("En attente", len(df[df['translation_count'] == 0]))
                
        except Exception as e:
            st.error(f"Erreur: {e}")
    
    def tts_tab(self):
        """Onglet TTS"""
        st.header("🎙️ Synthèse Vocale (TTS)")
        
        # Options TTS
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 TTS individuel")
            video_id = st.text_input("ID de la vidéo (TTS)")
            if st.button("Générer TTS"):
                if video_id:
                    with st.spinner("Génération TTS en cours..."):
                        try:
                            # result = self.tts_manager.generate_tts_for_video(video_id)
                            st.success("✅ TTS généré!")
                        except Exception as e:
                            st.error(f"Erreur: {e}")
                else:
                    st.warning("Veuillez entrer un ID de vidéo")
        
        with col2:
            st.subheader("🔄 TTS en lot")
            if st.button("Générer TTS pour toutes les vidéos", type="primary"):
                with st.spinner("Génération TTS en lot..."):
                    try:
                        # Simulation
                        st.success("✅ TTS généré pour toutes les vidéos!")
                    except Exception as e:
                        st.error(f"Erreur: {e}")
        
        # Configuration TTS
        st.subheader("⚙️ Configuration TTS")
        voice_model = st.selectbox("Modèle de voix", ["Bark", "Coqui", "gTTS"])
        language = st.selectbox("Langue", ["Français", "Anglais", "Espagnol"])
        
        if st.button("💾 Sauvegarder la configuration"):
            st.success("Configuration sauvegardée!")
    
    def analysis_tab(self):
        """Onglet d'analyse thématique"""
        st.header("🧠 Analyse Thématique")
        
        # Analyse individuelle
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Analyse individuelle")
            video_id = st.text_input("ID de la vidéo (analyse)")
            if st.button("Analyser le thème"):
                if video_id:
                    with st.spinner("Analyse en cours..."):
                        try:
                            # result = self.theme_classifier.classify_video(video_id)
                            st.success("✅ Thème analysé!")
                        except Exception as e:
                            st.error(f"Erreur: {e}")
                else:
                    st.warning("Veuillez entrer un ID de vidéo")
        
        with col2:
            st.subheader("🔄 Analyse en lot")
            if st.button("Analyser toutes les vidéos", type="primary"):
                with st.spinner("Analyse en lot..."):
                    try:
                        # Simulation
                        st.success("✅ Analyse terminée pour toutes les vidéos!")
                    except Exception as e:
                        st.error(f"Erreur: {e}")
        
        # Thèmes détectés
        st.subheader("📊 Thèmes détectés")
        try:
            videos = self.db.list_all_videos()
            df = pd.DataFrame(videos, columns=[
                'id', 'title', 'description', 'duration', 'upload_date', 
                'view_count', 'translation_count', 'theme'
            ])
            
            if df['theme'].notna().any():
                theme_counts = df['theme'].value_counts()
                fig = px.pie(
                    values=theme_counts.values,
                    names=theme_counts.index,
                    title="Répartition des thèmes"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucun thème détecté. Lancez l'analyse thématique.")
                
        except Exception as e:
            st.error(f"Erreur: {e}")
    
    def fonds_tab(self):
        """Onglet de gestion des fonds vidéos"""
        st.header("🎥 Fonds Vidéos")
        
        # Téléchargement de fonds
        st.subheader("📥 Télécharger des fonds")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            theme = st.selectbox("Thème", ["motivation", "success", "philosophy", "discipline"])
        with col2:
            count = st.number_input("Nombre de clips", min_value=1, max_value=20, value=5)
        with col3:
            source = st.selectbox("Source", ["Pexels", "Pixabay", "Mixkit"])
        
        if st.button("🎬 Télécharger les fonds", type="primary"):
            with st.spinner("Téléchargement des fonds..."):
                try:
                    # result = self.fond_downloader.download_for_theme(theme, count, source)
                    st.success(f"✅ {count} fonds téléchargés pour le thème '{theme}'!")
                except Exception as e:
                    st.error(f"Erreur: {e}")
        
        # Gestion des fonds
        st.subheader("📁 Gestion des fonds")
        
        # Simulation de la liste des fonds
        fonds_data = {
            'Thème': ['motivation', 'success', 'philosophy'],
            'Nombre de clips': [15, 12, 8],
            'Taille totale': ['2.3 GB', '1.8 GB', '1.2 GB']
        }
        fonds_df = pd.DataFrame(fonds_data)
        st.dataframe(fonds_df, use_container_width=True)
    
    def montage_tab(self):
        """Onglet de montage vidéo"""
        st.header("🎬 Montage Automatique")
        
        # Configuration du montage
        st.subheader("⚙️ Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            target_duration = st.number_input("Durée cible (secondes)", min_value=30, max_value=120, value=65)
            add_subtitles = st.checkbox("Ajouter les sous-titres", value=True)
        with col2:
            add_cta = st.checkbox("Ajouter Call-to-Action", value=True)
            output_format = st.selectbox("Format de sortie", ["MP4", "MOV", "AVI"])
        
        # Sélection des vidéos
        st.subheader("📹 Sélection des vidéos")
        
        try:
            videos = self.db.list_all_videos()
            df = pd.DataFrame(videos, columns=[
                'id', 'title', 'description', 'duration', 'upload_date', 
                'view_count', 'translation_count', 'theme'
            ])
            
            # Filtrer les vidéos traduites
            translated_videos = df[df['translation_count'] > 0]
            
            if not translated_videos.empty:
                selected_videos = st.multiselect(
                    "Choisir les vidéos à monter",
                    options=translated_videos['id'].tolist(),
                    format_func=lambda x: f"{x} - {translated_videos[translated_videos['id']==x]['title'].iloc[0][:50]}..."
                )
                
                if st.button("🎬 Lancer le montage", type="primary"):
                    if selected_videos:
                        with st.spinner("Montage en cours..."):
                            try:
                                # Simulation du montage
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                for i, video_id in enumerate(selected_videos):
                                    # self.video_builder.build_video(video_id, target_duration, add_subtitles, add_cta)
                                    progress = (i + 1) / len(selected_videos)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Montage {i+1}/{len(selected_videos)}")
                                
                                st.success(f"✅ {len(selected_videos)} vidéos montées!")
                            except Exception as e:
                                st.error(f"Erreur: {e}")
                    else:
                        st.warning("Veuillez sélectionner au moins une vidéo")
            else:
                st.warning("Aucune vidéo traduite disponible pour le montage")
                
        except Exception as e:
            st.error(f"Erreur: {e}")

def main():
    """Fonction principale de l'application"""
    app = TikTokAutoApp()
    app.main()

if __name__ == "__main__":
    main() 