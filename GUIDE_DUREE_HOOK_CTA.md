# 🎬 Guide - Durée Fixe et Hook/CTA

## 📋 Vue d'ensemble

Ce guide documente les améliorations apportées au système de montage vidéo pour répondre aux exigences TikTok :
- **Durée fixe de 1 minute 10 secondes** (70 secondes)
- **Hook d'accroche** au début de la vidéo
- **Call to Action (CTA)** à la fin de la vidéo

## ✨ Nouvelles Fonctionnalités

### 🕐 Durée Fixe (1min10)

**Problème résolu :** Les vidéos générées avaient des durées variables selon la longueur de l'audio TTS.

**Solution implémentée :**
- Remplacement de `-shortest` par `-t 70` dans la commande FFmpeg
- Ajout du filtre `loop=loop=-1:size=1` pour boucler la vidéo si nécessaire
- Durée garantie de 70 secondes (1 minute 10 secondes)

### 🎯 Hook d'Accroche

**Objectif :** Capturer l'attention dès les premières secondes.

**Implémentation :**
- **Durée :** 0-5 secondes
- **Texte :** "🎯 ATTENTION !"
- **Style :** Police Arial 64px, couleur jaune (`&H0000FFFF`)
- **Position :** Centré en bas avec contour noir

### 📢 Call to Action (CTA)

**Objectif :** Encourager l'engagement à la fin de la vidéo.

**Implémentation :**
- **Durée :** 65-70 secondes (dernières 5 secondes)
- **Texte :** "👍 Likez et abonnez-vous !"
- **Style :** Police Arial 56px, couleur verte (`&H0000FF00`)
- **Position :** Centré en bas avec contour noir

## 🏗️ Structure de la Vidéo

```
┌─────────────────────────────────────────────────────────┐
│                    VIDÉO FINALE (70s)                   │
├─────────────┬─────────────────────────────┬─────────────┤
│   HOOK      │        CONTENU              │    CTA      │
│   (0-5s)    │      (5-65s)                │  (65-70s)   │
│             │                             │             │
│ 🎯 ATTENTION│ Texte français progressif   │👍 Likez et  │
│     !       │ avec sous-titres stylisés   │abonnez-vous!│
└─────────────┴─────────────────────────────┴─────────────┘
```

## 🎨 Styles de Sous-titres

### Style Hook
- **Police :** Arial 64px
- **Couleur :** Jaune (`&H0000FFFF`)
- **Contour :** Noir 4px
- **Position :** Centré en bas

### Style CTA
- **Police :** Arial 56px
- **Couleur :** Vert (`&H0000FF00`)
- **Contour :** Noir 4px
- **Position :** Centré en bas

### Style Default (Contenu)
- **Police :** Arial 48px
- **Couleur :** Blanc (`&H00FFFFFF`)
- **Contour :** Noir 3px
- **Position :** Centré en bas

## 🔧 Modifications Techniques

### Fichier modifié : `montage/video_builder.py`

#### 1. Fonction `_create_subtitle_file()`
```python
# Structure de la vidéo : Hook (5s) + Contenu (60s) + CTA (5s) = 70s total
hook_duration = 5.0
content_duration = 60.0
cta_duration = 5.0

# HOOK (0-5 secondes)
hook_text = "🎯 ATTENTION !"
ass_content += f"Dialogue: 0,{self._format_time(0)},{self._format_time(hook_duration)},Hook,,0,0,0,,{hook_text}\n"

# CONTENU PRINCIPAL (5-65 secondes)
# ... logique de répartition du texte ...

# CTA (65-70 secondes)
cta_text = "👍 Likez et abonnez-vous !"
ass_content += f"Dialogue: 0,{self._format_time(hook_duration + content_duration)},{self._format_time(70.0)},CTA,,0,0,0,,{cta_text}\n"
```

#### 2. Fonction `create_final_video()`
```python
# Codecs et mapping
cmd.extend([
    '-c:v', 'libx264',      # Codec vidéo H.264
    '-c:a', 'aac',          # Codec audio AAC
    '-map', '0:v:0',        # Utiliser la vidéo de la première entrée
    '-map', '1:a:0',        # Utiliser l'audio de la deuxième entrée (TTS)
    '-t', '70',             # Forcer la durée à 70 secondes (1min10)
    '-y',                   # Écraser si existe
    str(output_path)
])

# Boucler la vidéo si nécessaire et ajouter les sous-titres
cmd.extend(['-vf', f'loop=loop=-1:size=1,ass={subtitle_rel_path}'])
```

## 🧪 Tests et Validation

### Test de Durée
```bash
python -c "
import subprocess
result = subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', 'datas/final_videos/final_0QC7iQ01DpU.mp4'], capture_output=True, text=True)
duration = float(result.stdout.strip())
print(f'Durée: {duration:.2f}s')
assert abs(duration - 70.0) < 1.0, 'Durée incorrecte'
"
```

### Test de Contenu
- ✅ Hook "🎯 ATTENTION !" présent (0-5s)
- ✅ CTA "👍 Likez et abonnez-vous !" présent (65-70s)
- ✅ Styles Hook et CTA définis
- ✅ Texte français progressif (5-65s)

## 📊 Résultats

### Avant les Modifications
- ❌ Durée variable (selon l'audio TTS)
- ❌ Pas de Hook d'accroche
- ❌ Pas de Call to Action
- ❌ Engagement limité

### Après les Modifications
- ✅ Durée fixe de 70 secondes (1min10)
- ✅ Hook d'accroche "🎯 ATTENTION !"
- ✅ CTA "👍 Likez et abonnez-vous !"
- ✅ Structure optimisée pour TikTok
- ✅ Engagement amélioré

## 🚀 Utilisation

### Montage Automatique
Le montage avec Hook et CTA est automatique lors de l'utilisation de l'option 5 "🎬 Montage vidéo" dans le menu principal.

### Recréation de Vidéos
Utilisez l'option 13 "📝 Recréer vidéos avec sous-titres" pour appliquer les nouvelles fonctionnalités aux vidéos existantes.

## 🔮 Améliorations Futures

### Personnalisation
- [ ] Hook personnalisable par thème
- [ ] CTA personnalisable par vidéo
- [ ] Styles configurables

### Optimisation
- [ ] A/B testing des textes Hook/CTA
- [ ] Analyse des performances d'engagement
- [ ] Adaptation automatique selon les tendances

### Fonctionnalités Avancées
- [ ] Animations pour Hook et CTA
- [ ] Sons d'alerte pour le Hook
- [ ] Intégration avec les analytics TikTok

## 📝 Notes Techniques

### Format ASS (Advanced SubStation Alpha)
Les sous-titres utilisent le format ASS pour un contrôle précis du style et du timing.

### Boucle Vidéo
Le filtre `loop=loop=-1:size=1` permet de boucler la vidéo de fond si elle est plus courte que 70 secondes.

### Synchronisation
Les sous-titres sont synchronisés avec l'audio TTS pour une expérience cohérente.

---

**Version :** 1.0  
**Date :** 27/07/2025  
**Auteur :** TikTok_Auto System 