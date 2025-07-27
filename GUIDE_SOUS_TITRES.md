# Guide des Sous-titres - TikTok Auto

## 🎯 Vue d'ensemble

Le système TikTok Auto intègre maintenant une fonctionnalité de sous-titres automatiques qui affiche le texte français au fur et à mesure de l'audio, incitant les spectateurs à lire et améliorant l'engagement.

## ✨ Fonctionnalités

### 📝 Sous-titres automatiques
- **Affichage progressif** : Le texte s'affiche phrase par phrase
- **Synchronisation audio** : Les sous-titres sont synchronisés avec l'audio TTS
- **Style professionnel** : Police Arial, taille 48px, couleur blanche avec contour noir
- **Position optimisée** : Centré en bas de l'écran pour une lecture confortable

### 🎨 Style des sous-titres
- **Format** : ASS (Advanced SubStation Alpha) pour un rendu professionnel
- **Police** : Arial, 48px
- **Couleur** : Blanc avec contour noir pour une excellente lisibilité
- **Position** : Centré en bas de l'écran
- **Animation** : Apparition progressive phrase par phrase

## 🔧 Utilisation

### Option 1 : Montage automatique avec sous-titres
Le montage vidéo inclut automatiquement les sous-titres si du texte français est disponible :

1. **Lancer le montage vidéo** (Option 5 du menu principal)
2. **Sélectionner le montage en lot** (Option 2)
3. Les vidéos seront créées avec sous-titres automatiquement

### Option 2 : Recréer des vidéos existantes avec sous-titres
Pour ajouter des sous-titres aux vidéos déjà créées :

1. **Menu principal** → **Option 13** : "📝 Recréer vidéos avec sous-titres"
2. **Choisir une vidéo** parmi la liste affichée
3. La vidéo sera recréée avec sous-titres

## 📋 Prérequis

### Base de données
- **Texte français** : Doit être présent dans `whisper_translations` ou `audio_translations`
- **Audio TTS** : Doit être généré et présent dans `tts_outputs`
- **Fond vidéo** : Doit être téléchargé selon le thème

### Fichiers requis
```
📁 Base de données
├── whisper_translations (french_text)
├── audio_translations (text)
└── tts_outputs (audio_path)

📁 Fichiers système
├── datas/tts_outputs/*.mp3
├── assets/videos/[theme]/*.mp4
└── datas/temp_subtitles/*.ass (temporaire)
```

## 🔄 Workflow complet

### 1. Préparation des données
```bash
# Transcription audio
python translation/whisper_simple.py

# Traduction en français
python translation/text_translator.py

# Génération audio TTS
python translation/tts_simple.py

# Téléchargement des fonds vidéos
python core/fond_downloader.py
```

### 2. Montage avec sous-titres
```bash
# Montage automatique
python montage/video_builder.py
# Option 2 : Montage en lot
```

### 3. Recréation avec sous-titres
```bash
# Menu principal
python main.py
# Option 13 : Recréer vidéos avec sous-titres
```

## 📊 Format des sous-titres

### Structure ASS
```ass
[Script Info]
Title: TikTok Auto Subtitles
ScriptType: v4.00+
WrapStyle: 1
ScaledBorderAndShadow: yes

[V4+ Styles]
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,20,20,20,1

[Events]
Dialogue: 0,0:00:00.00,0:00:03.00,Default,,0,0,0,,Première phrase
Dialogue: 0,0:00:03.00,0:00:06.00,Default,,0,0,0,,Deuxième phrase
```

### Caractéristiques
- **Durée** : Calculée automatiquement selon le nombre de mots (~0.3s/mot)
- **Division** : Phrases longues divisées automatiquement
- **Synchronisation** : Basée sur la durée estimée de l'audio

## 🎬 Exemple de résultat

### Avant (sans sous-titres)
- Vidéo avec fond + audio TTS
- Pas de texte à l'écran

### Après (avec sous-titres)
- Vidéo avec fond + audio TTS
- **Texte français progressif** :
  - "Quand une fille vous aime..."
  - "elle sera tellement attachée à vous..."
  - "Elle voudra toujours vous appeler..."

## ⚙️ Configuration avancée

### Personnalisation du style
Modifier `montage/video_builder.py` dans la méthode `_create_subtitle_file()` :

```python
# Style personnalisé
Style: Custom,Arial,60,&H00FF0000,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,1,2,20,20,20,1
```

### Paramètres ajustables
- **Taille de police** : Modifier `48` dans le style
- **Couleur** : Modifier `&H00FFFFFF` (blanc)
- **Contour** : Modifier `3` (épaisseur du contour)
- **Position** : Modifier `2` (centré en bas)

## 🐛 Dépannage

### Problèmes courants

#### 1. Sous-titres non affichés
```bash
# Vérifier le texte français
python main.py
# Option 1 → Vérifier whisper_translations

# Vérifier l'audio TTS
ls datas/tts_outputs/*.mp3
```

#### 2. Erreur FFmpeg
```bash
# Vérifier FFmpeg
ffmpeg -version

# Vérifier les chemins
ls datas/temp_subtitles/*.ass
```

#### 3. Synchronisation incorrecte
- **Cause** : Durée estimée incorrecte
- **Solution** : Ajuster le paramètre `0.3` dans `_create_subtitle_file()`

### Logs utiles
```bash
# Vérifier la création des sous-titres
tail -f datas/temp_subtitles/*.ass

# Vérifier les erreurs FFmpeg
ffmpeg -i video.mp4 -vf ass=subtitles.ass output.mp4
```

## 📈 Avantages

### Engagement amélioré
- **Lecture active** : Les spectateurs lisent le texte
- **Rétention** : Plus de temps passé sur la vidéo
- **Compréhension** : Texte français clair et lisible

### Accessibilité
- **Sourds et malentendants** : Accès au contenu
- **Langues étrangères** : Compréhension facilitée
- **Environnements bruyants** : Lecture possible sans son

### SEO et algorithmes
- **Détection de contenu** : Les algorithmes lisent le texte
- **Recommandations** : Meilleur classement
- **Engagement** : Métriques positives

## 🚀 Améliorations futures

### Fonctionnalités prévues
- [ ] **Animations avancées** : Effets de transition
- [ ] **Styles multiples** : Choix de styles de sous-titres
- [ ] **Synchronisation précise** : Analyse audio pour timing exact
- [ ] **Emojis supportés** : Intégration d'emojis dans le texte
- [ ] **Langues multiples** : Support d'autres langues

### Optimisations
- [ ] **Cache des sous-titres** : Éviter la recréation
- [ ] **Compression** : Réduction de la taille des fichiers
- [ ] **Parallélisation** : Traitement en lot optimisé

## 📞 Support

### Commandes utiles
```bash
# Tester les sous-titres
python -c "from montage.video_builder import VideoBuilder; vb = VideoBuilder(); vb._create_subtitle_file('test', 'Texte de test')"

# Vérifier la configuration
python main.py
# Option 12 → Tests système
```

### Structure des fichiers
```
📁 TikTok_Auto
├── montage/video_builder.py    # Logique des sous-titres
├── datas/temp_subtitles/       # Fichiers temporaires
├── datas/final_videos/         # Vidéos avec sous-titres
└── GUIDE_SOUS_TITRES.md        # Ce guide
```

---

**🎉 Les sous-titres automatiques sont maintenant intégrés au système TikTok Auto !** 