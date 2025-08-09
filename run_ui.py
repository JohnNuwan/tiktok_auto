import customtkinter as ctk
import threading
import os
import sys
import ffmpeg
import uuid
import json
from tkinter import ttk
from contextlib import redirect_stdout
import io
import sqlite3

# --- Ajout des chemins pour les imports ---
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config
from core.downloader import Downloader
from translation.whisper_simple import WhisperTranscriber
from montage.clip_finder import find_potential_clips
from database.manager import VideoDatabase
from scripts.auto_pipeline_complete import main as pipeline_main

class ClipSelectionWindow(ctk.CTkToplevel):
    """Fenêtre pop-up pour la sélection d'un clip."""
    def __init__(self, master, clips):
        super().__init__(master)
        self.title("Sélectionnez une Pépite")
        self.geometry("800x600")
        self.transient(master) # Reste au-dessus de la fenêtre principale
        self.grab_set() # Modal

        self.selected_clip = None

        self.label = ctk.CTkLabel(self, text="L'IA a identifié les clips suivants. Choisissez-en un.", font=ctk.CTkFont(size=16, weight="bold"))
        self.label.pack(padx=20, pady=20)

        scrollable_frame = ctk.CTkScrollableFrame(self)
        scrollable_frame.pack(expand=True, fill="both", padx=20, pady=10)

        for i, clip in enumerate(clips):
            clip_frame = ctk.CTkFrame(scrollable_frame, border_width=1)
            clip_frame.pack(fill="x", padx=10, pady=10)
            
            title = clip.get('title', 'N/A')
            duration = clip.get('end_time', 0) - clip.get('start_time', 0)
            justification = clip.get('justification', 'N/A')

            header = f"{i+1}. {title} ({duration:.2f}s)"
            ctk.CTkLabel(clip_frame, text=header, font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
            ctk.CTkLabel(clip_frame, text=justification, wraplength=700, justify="left").pack(anchor="w", padx=10, pady=5)
            
            select_button = ctk.CTkButton(clip_frame, text=f"Choisir ce clip", command=lambda c=clip: self.select_and_close(c))
            select_button.pack(anchor="e", padx=10, pady=10)

    def select_and_close(self, clip):
        self.selected_clip = clip
        self.destroy()

    def get_selection(self):
        self.master.wait_window(self) # Attend que la fenêtre soit détruite
        return self.selected_clip

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TikTok Auto - Studio d'Automatisation")
        self.geometry("1200x800")

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_tabs()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="TikTok Auto", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        buttons_info = {
            "Extraire Clips": self.show_clip_extractor_tab,
            "Pipeline Complet": self.show_pipeline_tab,
            "Base de Données": self.show_db_tab,
            "Paramètres": self.show_settings_tab
        }

        for i, (text, command) in enumerate(buttons_info.items()):
            button = ctk.CTkButton(self.sidebar_frame, text=text, command=command)
            button.grid(row=i + 1, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Thème:", anchor="w")
        self.appearance_mode_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                command=ctk.set_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

    def create_main_tabs(self):
        self.tab_view = ctk.CTkTabview(self, width=250)
        self.tab_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.tab_view.add("Extraire Clips")
        self.tab_view.add("Pipeline Complet")
        self.tab_view.add("Base de Données")
        self.tab_view.add("Paramètres")

        self.tab_view._segmented_button.grid_forget()

        self.create_clip_extractor_tab()
        self.create_pipeline_tab()
        self.create_db_tab()
        self.create_settings_tab()
        
        self.tab_view.set("Extraire Clips")

    def show_clip_extractor_tab(self): self.tab_view.set("Extraire Clips")
    def show_pipeline_tab(self): self.tab_view.set("Pipeline Complet")
    def show_db_tab(self): 
        self.tab_view.set("Base de Données")
        self.refresh_db_view()
    def show_settings_tab(self): 
        self.tab_view.set("Paramètres")
        self.load_settings()

    def create_clip_extractor_tab(self):
        tab = self.tab_view.tab("Extraire Clips")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        input_frame = ctk.CTkFrame(tab)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(input_frame, text="URL Vidéo Longue:").grid(row=0, column=0, padx=10, pady=10)
        self.url_entry = ctk.CTkEntry(input_frame, placeholder_text="https://www.youtube.com/watch?v=...")
        self.url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.extract_button = ctk.CTkButton(input_frame, text="Lancer l'Extraction", command=self.start_extraction_thread)
        self.extract_button.grid(row=0, column=2, padx=10, pady=10)

        self.log_console = ctk.CTkTextbox(tab, state="disabled", wrap="word", font=("Courier New", 12))
        self.log_console.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def create_pipeline_tab(self):
        tab = self.tab_view.tab("Pipeline Complet")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(tab, text="Lance le pipeline complet sur toutes les vidéos avec le statut 'downloaded'.", font=ctk.CTkFont(size=14)).grid(row=0, column=0, pady=20, padx=20)
        self.run_pipeline_button = ctk.CTkButton(tab, text="Lancer le Pipeline", command=self.start_pipeline_thread)
        self.run_pipeline_button.grid(row=1, column=0, pady=10, padx=20)
        self.pipeline_log_console = ctk.CTkTextbox(tab, state="disabled", wrap="word", font=("Courier New", 12))
        self.pipeline_log_console.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")

    def create_db_tab(self):
        tab = self.tab_view.tab("Base de Données")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        tree_frame = ctk.CTkFrame(tab)
        tree_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#343638", borderwidth=0)
        style.map('Treeview', background=[('selected', '#22559b')])
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[('active', '#343638')])

        self.db_tree = ttk.Treeview(tree_frame, columns=("ID", "Titre", "Statut", "Thème"), show='headings')
        self.db_tree.heading("ID", text="ID Vidéo")
        self.db_tree.heading("Titre", text="Titre")
        self.db_tree.heading("Statut", text="Statut")
        self.db_tree.heading("Thème", text="Thème")
        self.db_tree.grid(row=0, column=0, sticky="nsew")

        button_frame = ctk.CTkFrame(tab)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        ctk.CTkButton(button_frame, text="Supprimer la sélection", command=self.delete_selected_video).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Rafraîchir", command=self.refresh_db_view).pack(side="left", padx=5)

    def create_settings_tab(self):
        tab = self.tab_view.tab("Paramètres")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Configuration des Clés API et Paramètres", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        
        self.settings_entries = {}
        settings = [
            "PEXELS_API_KEY", "PIXABAY_API_KEY", "ELEVENLABS_API_KEY", 
            "OLLAMA_HOST", "OLLAMA_MODEL", "DEFAULT_TTS_ENGINE"
        ]
        for i, setting in enumerate(settings):
            ctk.CTkLabel(tab, text=setting).grid(row=i+1, column=0, padx=20, pady=(10,0), sticky="w")
            entry = ctk.CTkEntry(tab, width=400)
            entry.grid(row=i+2, column=0, padx=20, pady=(0,10), sticky="ew")
            self.settings_entries[setting] = entry

        ctk.CTkButton(tab, text="Sauvegarder", command=self.save_settings).grid(row=len(settings)+3, column=0, padx=20, pady=20, sticky="e")

    def log(self, message, console='main'):
        textbox = self.log_console if console == 'main' else self.pipeline_log_console
        def _log():
            textbox.configure(state="normal")
            textbox.insert("end", message + "\n")
            textbox.configure(state="disabled")
            textbox.see("end")
        self.after(0, _log)

    def refresh_db_view(self):
        for i in self.db_tree.get_children(): 
            self.db_tree.delete(i)
        db = VideoDatabase()
        videos = db.list_all_videos()
        for video in videos:
            # video est un tuple: (video_id, title, duration, channel_name, audio_count, subtitle_count, translation_count, tts_count)
            video_id, title, duration, channel_name, audio_count, subtitle_count, translation_count, tts_count = video
            
            # Déterminer le statut basé sur les fichiers disponibles
            if tts_count > 0:
                status = "TTS généré"
            elif translation_count > 0:
                status = "Traduit"
            elif subtitle_count > 0:
                status = "Transcrit"
            elif audio_count > 0:
                status = "Audio extrait"
            else:
                status = "Nouveau"
            
            # Pour le thème, on utilise N/A pour l'instant
            theme = "N/A"
            
            self.db_tree.insert("", "end", values=(video_id, title, status, theme))

    def delete_selected_video(self):
        selected_item = self.db_tree.focus()
        if not selected_item: 
            self.log("❌ Veuillez sélectionner une vidéo à supprimer.")
            return
        video_id = self.db_tree.item(selected_item)['values'][0]
        db = VideoDatabase()
        
        # Supprimer la vidéo et tous ses fichiers associés
        try:
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                # Supprimer dans l'ordre pour respecter les contraintes de clés étrangères
                cursor.execute('DELETE FROM tts_files WHERE video_id = ?', (video_id,))
                cursor.execute('DELETE FROM translations WHERE video_id = ?', (video_id,))
                cursor.execute('DELETE FROM subtitle_files WHERE video_id = ?', (video_id,))
                cursor.execute('DELETE FROM audio_files WHERE video_id = ?', (video_id,))
                cursor.execute('DELETE FROM videos WHERE video_id = ?', (video_id,))
                conn.commit()
            self.log(f"🗑️ Vidéo {video_id} supprimée.")
            self.refresh_db_view()
        except Exception as e:
            self.log(f"❌ Erreur lors de la suppression : {e}")

    def load_settings(self):
        # Utilise les valeurs de l'objet Config qui a déjà chargé le .env
        for key, entry in self.settings_entries.items():
            entry.delete(0, "end")
            entry.insert(0, getattr(Config, key, ""))

    def save_settings(self):
        try:
            env_path = ".env"
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            new_lines = []
            for line in lines:
                found = False
                for key, entry in self.settings_entries.items():
                    if line.startswith(key + '='):
                        new_lines.append(f"{key}='{entry.get()}'\n")
                        found = True
                        break
                if not found:
                    new_lines.append(line)

            with open(env_path, 'w') as f:
                f.writelines(new_lines)
            self.log("✅ Paramètres sauvegardés dans .env. Veuillez redémarrer l'application pour appliquer les changements.")
        except Exception as e:
            self.log(f"❌ Erreur lors de la sauvegarde des paramètres : {e}")

    def start_extraction_thread(self):
        url = self.url_entry.get()
        if not url: self.log("❌ Erreur: Veuillez entrer une URL."); return
        self.extract_button.configure(state="disabled", text="Extraction...")
        threading.Thread(target=self.run_extraction_in_thread, args=(url,), daemon=True).start()

    def run_extraction_in_thread(self, url):
        try:
            self.log(f"[1/6] 📥 Téléchargement de la vidéo...")
            downloader = Downloader()
            video_info_list = downloader.download_audio([url])
            if not video_info_list: self.log("❌ Échec du téléchargement."); return
            video_info = video_info_list[0]
            video_id, original_path = video_info['id'], video_info['audio_path']
            self.log(f"✅ Vidéo téléchargée : {video_id}")

            self.log(f"[2/6] 🎤 Transcription (Whisper)... Cela peut prendre du temps.")
            transcriber = WhisperTranscriber()
            result = transcriber.transcribe_with_timestamps(video_id)
            if not result: self.log("❌ Échec de la transcription."); return
            self.log("✅ Transcription terminée.")

            self.log(f"[3/6] 🧠 Analyse par l'IA pour trouver les pépites...")
            clips = find_potential_clips(result['segments'], result['duration'])
            if not clips: self.log("🔴 L'IA n'a identifié aucun clip pertinent."); return
            self.log(f"✅ IA a trouvé {len(clips)} clips potentiels.")

            self.log("[4/6] 🙋‍♂️ En attente de votre sélection...")
            selection_window = ClipSelectionWindow(self, clips)
            selected_clip = selection_window.get_selection()
            if not selected_clip: self.log("🔴 Opération annulée."); return
            self.log(f"👍 Clip '{selected_clip['title']}' sélectionné.")

            self.log("[5/6] 🎬 Découpage de la vidéo...")
            start, end = selected_clip['start_time'], selected_clip['end_time']
            new_id = f"clip_{uuid.uuid4().hex[:8]}"
            db = VideoDatabase()
            output_path = os.path.join(db.audios_en_dir, f"{new_id}.mp4")
            ffmpeg.input(original_path, ss=start, to=end).output(output_path, c='copy', y='-y').run(quiet=True)
            self.log(f"✅ Clip sauvegardé : {output_path}")

            self.log("[6/6] 🗃️ Ajout à la base de données...")
            db.add_video(video_id=new_id, title=f"[CLIP] {selected_clip['title']}", url=url, channel_name=video_info['channel'], status='downloaded')
            self.log(f"🎉 Succès ! Le clip {new_id} est prêt à être traité par le pipeline.")
            self.after(0, self.refresh_db_view)

        except Exception as e:
            self.log(f"❌ Erreur critique : {e}")
        finally:
            self.extract_button.configure(state="normal", text="Lancer l'Extraction")

    def start_pipeline_thread(self):
        self.run_pipeline_button.configure(state="disabled", text="En cours...")
        threading.Thread(target=self.run_pipeline_in_thread, daemon=True).start()

    def run_pipeline_in_thread(self):
        self.log("🚀 Lancement du pipeline complet...", console='pipeline')
        # Rediriger stdout pour capturer les logs du script
        log_stream = io.StringIO()
        try:
            with redirect_stdout(log_stream):
                pipeline_main()
            # Récupérer les logs et les afficher
            log_output = log_stream.getvalue()
            self.log(log_output, console='pipeline')
            self.log("✅ Pipeline terminé !", console='pipeline')
        except Exception as e:
            self.log(f"❌ Erreur durant le pipeline : {e}", console='pipeline')
            self.log(log_stream.getvalue(), console='pipeline') # Afficher les logs même en cas d'erreur
        finally:
            self.run_pipeline_button.configure(state="normal", text="Lancer le Pipeline")
            self.after(0, self.refresh_db_view)

if __name__ == "__main__":
    app = App()
    app.mainloop()
