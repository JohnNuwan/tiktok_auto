# 🎬 Guide des Shorts et CTA Audio - TikTok_Auto

## 🎯 Vue d'ensemble

Ce guide détaille l'utilisation du générateur de shorts automatiques et des fonctionnalités CTA audio du système TikTok_Auto.

## 🎬 Générateur de Shorts Automatiques

### ✨ Fonctionnalités Principales

Le générateur de shorts offre des fonctionnalités avancées pour créer des contenus optimisés pour les réseaux sociaux :

- **CTA audio intégrés** : Messages vocaux d'incitation à s'abonner à la fin de la vidéo
- **Organisation structurée** : Dossiers organisés par plateforme et type
- **Durée minimale garantie** : 70 secondes (1min10) pour tous les shorts
- **Format TikTok corrigé** : Format 9:16 (vertical) pour tous les shorts
- **Détection virale améliorée** : +50 mots-clés viraux et algorithme sophistiqué
- **Effets visuels avancés** : Zoom progressif, transitions fade, filtres de couleur
- **Système d'analytics** : Suivi complet des performances (vues, likes, partages)
- **Interface analytics** : CLI pour consulter les statistiques et rapports

### 🎯 Formats Supportés

| Plateforme | Format | Durée | Effets | CTA Audio |
|------------|--------|-------|--------|-----------|
| **TikTok** | 9:16 | 70s+ | Zoom, transitions, filtres | ✅ |
| **YouTube Shorts** | 9:16 | 70s+ | Zoom, transitions | ✅ |
| **Instagram Reels** | 9:16 | 70s+ | Zoom, transitions, filtres | ✅ |

## 📁 Organisation des Shorts

### Structure des Dossiers

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

### Avantages de l'Organisation

1. **Séparation claire** : Shorts finaux séparés des fichiers temporaires
2. **Organisation par plateforme** : Chaque plateforme a son propre dossier
3. **Miniatures centralisées** : Toutes les thumbnails dans un seul dossier
4. **Nettoyage facile** : Fichiers temporaires dans un dossier dédié

## 🎤 CTA Audio

### Fonctionnement

Les Call-to-Action sont maintenant générés en audio et ajoutés à la fin de la vidéo :

1. **Génération automatique** : Le système génère automatiquement des messages CTA audio
2. **Concaténation** : Les CTA audio sont concaténés à l'audio principal
3. **Synchronisation** : Les CTA s'intègrent naturellement dans la vidéo
4. **Qualité optimisée** : Utilisation de Bark (gratuit) pour éviter les quotas

### Messages CTA par Plateforme

#### TikTok
- "Abonne-toi pour plus de contenu comme ça !"
- "Suis-moi pour du contenu exclusif !"
- "Abonne-toi et active la cloche !"
- "Like et abonne-toi pour plus !"

#### YouTube Shorts
- "Abonne-toi et active la cloche !"
- "Like et abonne-toi pour plus de contenu !"
- "Rejoins la communauté !"
- "Abonne-toi pour ne rien manquer !"

#### Instagram Reels
- "Suis-moi pour plus de contenu !"
- "Abonne-toi et active les notifications !"
- "Double tap et abonne-toi !"
- "Suis-moi pour du contenu exclusif !"

### Avantages des CTA Audio

1. **Engagement naturel** : Messages vocaux plus naturels que les sous-titres
2. **Moins intrusif** : Ne perturbe pas la lecture des sous-titres principaux
3. **Qualité professionnelle** : Audio généré avec Bark (TTS de qualité)
4. **Personnalisation** : Messages adaptés à chaque plateforme

## 🎮 Utilisation du Générateur de Shorts

### Lancement

```bash
python montage/shorts_generator.py
```

### Options Disponibles

#### 1. 🎬 Créer un short TikTok
- Entrez l'ID de la vidéo source
- Le système génère automatiquement un short optimisé pour TikTok
- Durée minimale : 70 secondes
- CTA audio intégré

#### 2. 📺 Créer un short YouTube
- Entrez l'ID de la vidéo source
- Le système génère automatiquement un short optimisé pour YouTube Shorts
- Durée minimale : 70 secondes
- CTA audio intégré

#### 3. 📱 Créer un Reel Instagram
- Entrez l'ID de la vidéo source
- Le système génère automatiquement un Reel optimisé pour Instagram
- Durée minimale : 70 secondes
- CTA audio intégré

#### 4. 🔄 Création en lot
- Choisissez la plateforme
- Entrez le nombre de shorts à créer
- Le système traite automatiquement plusieurs vidéos

#### 5. 📊 Afficher les shorts créés
- Affiche tous les shorts créés de manière organisée
- Statistiques par plateforme
- Informations détaillées (taille, date, etc.)

#### 6. 🧹 Nettoyer les fichiers temporaires
- Supprime les fichiers temporaires de traitement
- Libère de l'espace disque
- Nettoie les dossiers temp

#### 7. 📈 Statistiques des shorts
- Affiche les statistiques complètes des shorts
- Nombre total de shorts par plateforme
- Taille totale des fichiers
- Dernier short créé

## 🔧 Configuration Avancée

### Paramètres des Shorts

Vous pouvez personnaliser les paramètres dans `montage/shorts_generator.py` :

```python
# Templates pour différentes plateformes
self.platform_templates = {
    'tiktok': {
        'aspect_ratio': '9:16',   # Format vertical
        'duration_limit': 60,     # 60 secondes max
        'min_duration': 70,       # 70 secondes minimum
        'subtitle_style': 'tiktok',
        'effects': ['zoom', 'text_animations', 'transitions', 'filters'],
        'output_dir': self.tiktok_dir
    },
    # ... autres plateformes
}
```

### Configuration des CTA Audio

Les CTA audio sont configurés dans la méthode `generate_cta_audio` :

```python
# CTA audio à ajouter à la fin
cta_texts = {
    'tiktok': [
        "Abonne-toi pour plus de contenu comme ça !",
        "Suis-moi pour du contenu exclusif !",
        "Abonne-toi et active la cloche !",
        "Like et abonne-toi pour plus !"
    ],
    # ... autres plateformes
}
```

## 🎬 Structure de la Vidéo Finale

```
0-5s    : 🎯 ATTENTION ! (Hook)
5-65s   : Contenu principal avec sous-titres progressifs
65-70s  : CTA audio "Abonne-toi pour plus de contenu !" (parole)
```

## 🔍 Dépannage

### Erreurs Courantes

#### Erreur FFmpeg
```bash
# Windows
# Téléchargez FFmpeg depuis https://ffmpeg.org/download.html

# Linux
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

#### Erreur CTA audio
- Les CTA audio utilisent Bark (gratuit) par défaut
- Si vous avez des problèmes, vérifiez que Bark est installé
- Les quotas ElevenLabs ne sont pas utilisés pour les CTA

#### Fichiers temporaires
- Utilisez l'option de nettoyage pour supprimer les fichiers temporaires
- Les fichiers temporaires sont stockés dans `datas/shorts/temp/`

#### Durée insuffisante
- Le système étend automatiquement les vidéos courtes à 70 secondes
- Les vidéos sont répétées si nécessaire pour atteindre la durée minimale

### Conseils d'Optimisation

1. **Nettoyage régulier** : Utilisez l'option de nettoyage des fichiers temporaires
2. **Statistiques** : Consultez régulièrement les statistiques des shorts
3. **Organisation** : Les shorts sont automatiquement organisés par plateforme
4. **Qualité** : Les CTA audio utilisent Bark pour une qualité optimale

## 📊 Analytics et Statistiques

### Statistiques Disponibles

- **Nombre total de shorts** : Par plateforme et global
- **Taille des fichiers** : Espace disque utilisé
- **Dernier short créé** : Date et plateforme
- **Performance** : Suivi des vues, likes, partages

### Interface Analytics

```bash
# Afficher les statistiques
python montage/shorts_generator.py
# Choisir option 7
```

## 🎯 Conseils d'Utilisation

### Performance
- **Traitement en lot** : Utilisez l'option de création en lot pour traiter plusieurs vidéos
- **Nettoyage régulier** : Supprimez les fichiers temporaires régulièrement
- **Organisation** : Les shorts sont automatiquement organisés

### Engagement
- **CTA audio** : Messages vocaux naturels pour l'engagement
- **Durée optimisée** : 70 secondes minimum pour maximiser l'engagement
- **Format vertical** : Optimisé pour les plateformes mobiles

### Organisation
- **Dossiers structurés** : Les shorts sont automatiquement organisés
- **Nettoyage régulier** : Utilisez l'option de nettoyage des fichiers temporaires
- **Statistiques** : Consultez régulièrement les statistiques des shorts

## 📚 Documentation Associée

- **Guide d'utilisation** : `GUIDE_UTILISATION.md`
- **Guide sous-titres** : `GUIDE_SOUS_TITRES.md`
- **Guide Hook/CTA** : `GUIDE_DUREE_HOOK_CTA.md`
- **Documentation complète** : `docs/README.md`

---

**🎬 Générateur de Shorts** - Créez des contenus optimisés automatiquement avec CTA audio intégrés !
