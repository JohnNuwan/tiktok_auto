# 🎵 Gestionnaire de Vidéos YouTube avec Base de Données SQLite

Ce projet permet de télécharger automatiquement les audios et sous-titres de chaînes YouTube et de les organiser dans une base de données SQLite pour une gestion facile.

## 🚀 Fonctionnalités

- ✅ Téléchargement automatique d'audios MP3 depuis YouTube
- ✅ Récupération automatique des sous-titres VTT
- ✅ Stockage organisé dans une base de données SQLite
- ✅ Métadonnées complètes des vidéos (titre, description, durée, etc.)
- ✅ Interface de recherche et de gestion
- ✅ Scan des fichiers existants
- ✅ Vérification de l'intégrité des fichiers
- ✅ **Traduction automatique en français** (VTT + Whisper)
- ✅ **Méthode hybride intelligente** (VTT si disponible, sinon Whisper)
- ✅ **Traduction en lot** pour plusieurs vidéos
- ✅ **Générateur de shorts automatiques** avec CTA audio
- ✅ **Organisation structurée** des shorts par plateforme

## 📁 Structure du Projet

```
TikTok_Auto/
├── database_manager.py      # Gestionnaire de base de données
├── downloader_yt_chaine.py  # Script de téléchargement principal
├── translation_manager.py   # Gestionnaire de traduction (VTT + Whisper)
├── db_manager.py           # Outil de gestion en ligne de commande
├── videos.db               # Base de données SQLite (créée automatiquement)
├── requirements.txt        # Dépendances Python
├── datas/
│   ├── audios_En/          # Fichiers audio et sous-titres téléchargés
│   ├── translations/       # Fichiers VTT traduits organisés par langue
│   │   └── fr/             # Traductions en français
│   └── shorts/             # Shorts générés automatiquement
│       ├── final/          # Shorts finaux prêts à publier
│       ├── temp/           # Fichiers temporaires de traitement
│       ├── thumbnails/     # Miniatures générées
│       └── platforms/      # Shorts organisés par plateforme
│           ├── tiktok/     # Shorts TikTok
│           ├── youtube/    # Shorts YouTube
│           └── instagram/  # Reels Instagram
└── README.md
```

## 🛠️ Installation

1. **Activer l'environnement virtuel** :
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

3. **Vérifier que yt-dlp est installé** :
   ```bash
   yt-dlp --version
   ```

## 📖 Utilisation

### 1. Téléchargement d'une nouvelle chaîne

```bash
python downloader_yt_chaine.py
```

Choisissez l'option 1 et entrez l'URL de la chaîne YouTube.

### 2. Scan des fichiers existants

Si vous avez déjà des fichiers téléchargés, vous pouvez les ajouter à la base de données :

```bash
python downloader_yt_chaine.py
```

Choisissez l'option 2 pour scanner les fichiers existants.

### 3. Traduction des vidéos

Traduisez vos vidéos en français avec différentes méthodes :

```bash
# Lancer le gestionnaire de traduction
python translation_manager.py

# Méthodes disponibles :
# 1. VTT uniquement (rapide, utilise les sous-titres existants)
# 2. Whisper uniquement (précis, retranscrit tout)
# 3. Hybride (VTT si disponible, sinon Whisper)
# 4. Traduction en lot
```

### 4. Gestion de la base de données

Utilisez le gestionnaire en ligne de commande :

```bash
# Lister toutes les vidéos
python db_manager.py list

# Rechercher des vidéos
python db_manager.py search --search "motivation"

# Informations détaillées d'une vidéo
python db_manager.py info --video-id VIDEO_ID

# Statistiques de la base de données
python db_manager.py stats

# Vérifier les fichiers manquants
python db_manager.py clean
```

### 5. Générateur de Shorts Automatiques

Générez automatiquement des shorts optimisés pour TikTok, YouTube Shorts et Instagram Reels :

```bash
# Lancer le générateur de shorts
python montage/shorts_generator.py

# Options disponibles :
# 1. Créer un short TikTok
# 2. Créer un short YouTube
# 3. Créer un Reel Instagram
# 4. Création en lot
# 5. Afficher les shorts créés
# 6. Nettoyer les fichiers temporaires
# 7. Statistiques des shorts
```

#### 🎤 CTA Audio

Les shorts générés incluent automatiquement des Call-to-Action audio à la fin :

- **TikTok** : "Abonne-toi pour plus de contenu comme ça !", "Suis-moi pour du contenu exclusif !"
- **YouTube** : "Abonne-toi et active la cloche !", "Like et abonne-toi pour plus de contenu !"
- **Instagram** : "Suis-moi pour plus de contenu !", "Abonne-toi et active les notifications !"

#### 📁 Organisation des Shorts

Les shorts sont automatiquement organisés dans une structure claire :

```
datas/shorts/
├── final/              # Shorts finaux prêts à publier
├── temp/               # Fichiers temporaires de traitement
├── thumbnails/         # Miniatures générées
└── platforms/          # Shorts organisés par plateforme
    ├── tiktok/         # Shorts TikTok
    ├── youtube/        # Shorts YouTube
    └── instagram/      # Reels Instagram
```

## 🗄️ Structure de la Base de Données

### Tables principales :

1. **channels** : Informations des chaînes YouTube
   - `channel_id` : Identifiant unique de la chaîne
   - `channel_name` : Nom de la chaîne
   - `channel_url` : URL de la chaîne

2. **videos** : Informations des vidéos
   - `video_id` : Identifiant YouTube de la vidéo
   - `title` : Titre de la vidéo
   - `description` : Description de la vidéo
   - `duration` : Durée en secondes
   - `upload_date` : Date de mise en ligne
   - `view_count` : Nombre de vues

3. **audio_files** : Fichiers audio téléchargés
   - `video_id` : Référence vers la vidéo
   - `file_path` : Chemin vers le fichier MP3
   - `file_size` : Taille du fichier
   - `duration` : Durée du fichier audio
   - `format` : Format du fichier (mp3)

4. **subtitle_files** : Fichiers de sous-titres
   - `video_id` : Référence vers la vidéo
   - `file_path` : Chemin vers le fichier VTT
   - `language` : Langue des sous-titres
   - `is_auto_generated` : Si généré automatiquement

5. **translations** : Fichiers de traductions
   - `video_id` : Référence vers la vidéo
   - `file_path` : Chemin vers le fichier VTT traduit
   - `language` : Langue de traduction
   - `translation_method` : Méthode utilisée (vtt_only/whisper_only/hybrid)
   - `original_language` : Langue d'origine
   - `segment_count` : Nombre de segments traduits
   - `file_size` : Taille du fichier

6. **shorts** : Shorts générés automatiquement
   - `id` : Identifiant unique du short
   - `video_id` : Référence vers la vidéo source
   - `platform` : Plateforme (tiktok/youtube_shorts/instagram_reels)
   - `short_path` : Chemin vers le fichier short
   - `thumbnail_path` : Chemin vers la miniature
   - `title` : Titre du short
   - `start_time` : Temps de début du moment viral
   - `end_time` : Temps de fin du moment viral
   - `justification` : Justification de la sélection
   - `created_at` : Date de création

## 🔍 Exemples d'Utilisation

### Traduction d'une vidéo :
```bash
# Méthode hybride (recommandée)
python translation_manager.py
# Choisir option 3, puis entrer l'ID de la vidéo

# Traduction en lot
python translation_manager.py
# Choisir option 4, puis "hybrid"
```

### Recherche de vidéos par mot-clé :
```bash
python db_manager.py search --search "motivation"
```

### Obtenir les informations d'une vidéo spécifique :
```bash
python db_manager.py info --video-id dEq6QtwmHvY
```

### Vérifier l'état de la base de données :
```bash
python db_manager.py stats
```

### Générer un short TikTok :
```bash
python montage/shorts_generator.py
# Choisir option 1, puis entrer l'ID de la vidéo
```

## 📊 Avantages de la Base de Données

1. **Organisation** : Tous les fichiers sont référencés et organisés
2. **Recherche rapide** : Trouvez facilement vos vidéos par titre ou description
3. **Métadonnées complètes** : Accès à toutes les informations des vidéos
4. **Gestion des fichiers** : Vérification de l'intégrité et localisation
5. **Évolutivité** : Facile d'ajouter de nouvelles fonctionnalités
6. **Shorts automatiques** : Génération et organisation automatiques des shorts

## 🌍 Avantages de la Traduction

1. **Méthode hybride intelligente** : Utilise VTT si disponible, sinon Whisper
2. **Timing préservé** : Les sous-titres traduits gardent la synchronisation
3. **Qualité optimale** : Combine rapidité (VTT) et précision (Whisper)
4. **Traduction en lot** : Traite plusieurs vidéos automatiquement
5. **Format VTT standard** : Compatible avec tous les lecteurs vidéo

## 🎬 Avantages des Shorts Automatiques

1. **CTA audio intégrés** : Messages vocaux d'incitation à s'abonner
2. **Durée optimisée** : 70 secondes minimum garantie
3. **Organisation structurée** : Dossiers organisés par plateforme
4. **Détection virale** : Algorithmes sophistiqués pour identifier les moments viraux
5. **Formats optimisés** : TikTok, YouTube Shorts, Instagram Reels
6. **Effets visuels** : Zoom progressif, transitions, filtres

## 🐛 Dépannage

### Erreur "yt-dlp not found"
Assurez-vous que yt-dlp est installé dans votre environnement virtuel :
```bash
pip install yt-dlp
```

### Erreur "whisper not found"
Installez Whisper pour la transcription :
```bash
pip install openai-whisper
```

### Erreur de traduction
Si la traduction échoue, vérifiez votre connexion internet et réessayez.

### Fichiers manquants
Utilisez la commande de nettoyage pour détecter les fichiers manquants :
```bash
python db_manager.py clean
```

### Base de données corrompue
Supprimez le fichier `videos.db` et relancez le script pour recréer la base de données.

### Erreur FFmpeg
Assurez-vous que FFmpeg est installé et accessible dans votre PATH :
```bash
# Windows
# Téléchargez FFmpeg depuis https://ffmpeg.org/download.html

# Linux
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

## 🔧 Personnalisation

Vous pouvez modifier les paramètres de téléchargement dans `downloader_yt_chaine.py` :
- Format audio (mp3, m4a, etc.)
- Langue des sous-titres
- Dossier de sortie
- Qualité audio

### Configuration des Shorts

Vous pouvez personnaliser les paramètres des shorts dans `montage/shorts_generator.py` :
- Durée minimale et maximale
- Styles de sous-titres
- Effets visuels
- Messages CTA audio

## 📝 Notes

- Les fichiers sont organisés par ID de vidéo YouTube
- Les sous-titres automatiques sont marqués comme tels
- La base de données est créée automatiquement au premier lancement
- Tous les chemins de fichiers sont relatifs au dossier du projet
- Les shorts sont automatiquement organisés par plateforme
- Les CTA audio sont générés avec Bark (gratuit) pour éviter les quotas 