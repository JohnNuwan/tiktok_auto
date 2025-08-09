
"""
Module d'Identification de Clips (Clip Finder)
Ce module est responsable de l'analyse d'une transcription de vidéo longue
pour identifier les segments les plus prometteurs à transformer en vidéos courtes (Shorts/TikToks).
Il utilise un grand modèle de langage (LLM) via Ollama pour effectuer cette analyse sémantique.
"""

import json
import ollama
from config import Config

def find_potential_clips(transcript_with_timestamps: list, video_duration: int) -> list:
    """
    Analyse une transcription pour trouver les meilleurs segments pour des vidéos courtes.

    Args:
        transcript_with_timestamps (list): Une liste de dictionnaires, où chaque dictionnaire
                                            représente un segment de la transcription et contient
                                            au moins les clés 'start', 'end', et 'text'.
                                            Ex: [{'start': 15.3, 'end': 25.1, 'text': '...'}]
        video_duration (int): La durée totale de la vidéo en secondes.

    Returns:
        list: Une liste de dictionnaires, chaque dictionnaire représentant un clip potentiel
              identifié par le LLM. Retourne une liste vide en cas d'erreur.
              Ex: [{'title': 'Le secret...', 'start_time': 45.32, 'end_time': 92.10, 'justification': '...'}]
    """
    print("🧠 Lancement de l'analyse par l'IA pour trouver les meilleures pépites...")

    # 1. Formater la transcription pour le prompt
    # On crée une chaîne de caractères lisible de la transcription complète.
    try:
        full_text = "\n".join([f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}" for segment in transcript_with_timestamps])
    except KeyError:
        print("❌ Erreur: La transcription ne semble pas contenir les clés 'start', 'end', et 'text'.")
        return []

    # 2. Créer un prompt puissant et précis pour Ollama
    prompt = f"""
    Tu es un expert de classe mondiale en stratégie de contenu viral pour les plateformes comme TikTok, YouTube Shorts et Instagram Reels.
    Ton rôle est d'analyser la transcription d'une vidéo de {video_duration // 60} minutes et d'en extraire 3 à 5 "pépites" : des segments courts (entre 30 et 90 secondes) avec le plus haut potentiel de devenir viraux.

    Critères de sélection d'une pépite :
    - **Hook Puissant** : Le segment doit commencer par une question intrigante, une déclaration audacieuse, ou une affirmation qui suscite la curiosité.
    - **Valeur Concentrée** : Il doit offrir une information claire et précieuse, une astuce actionnable, une histoire captivante ou une émotion forte (humour, inspiration, surprise).
    - **Autonome** : Le clip doit être compréhensible sans le reste de la vidéo.
    - **Rythme** : Privilégie les moments où le locuteur est énergique et passionné.

    Voici la transcription complète avec les timestamps [début en secondes - fin en secondes] :
    ---
    {full_text}
    ---

    Ta mission est de retourner un objet JSON valide, et RIEN D'AUTRE. Le JSON doit être une liste de clips potentiels.
    Pour chaque clip, fournis les éléments suivants :
    1.  `title`: Un titre très court et percutant (max 10 mots).
    2.  `start_time`: Le timestamp de début exact en secondes (nombre à virgule).
    3.  `end_time`: Le timestamp de fin exact en secondes (nombre à virgule). Assure-toi que la durée (end_time - start_time) est entre 30 et 90 secondes.
    4.  `justification`: Une phrase expliquant pourquoi ce clip a un fort potentiel viral, en se basant sur tes critères d'expert.

    Exemple de format de sortie attendu :
    [
      {{
        "title": "Le secret de la productivité que personne ne révèle",
        "start_time": 45.32,
        "end_time": 92.10,
        "justification": "Ce segment démarre avec une question provocante et révèle une méthode contre-intuitive, ce qui est idéal pour capter l'attention."
      }},
      {{
        "title": "L'échec qui a transformé ma vie",
        "start_time": 182.50,
        "end_time": 241.80,
        "justification": "Le storytelling est puissant et crée une connexion émotionnelle instantanée, un facteur clé de partage."
      }}
    ]

    Ne fournis aucune explication ou texte avant ou après le bloc JSON.
    """

    # 3. Appeler l'API Ollama
    try:
        print(f"🤖 Envoi de la requête au modèle Ollama ({Config.OLLAMA_MODEL})... Cela peut prendre un moment.")
        response = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            format='json'  # Demande une sortie JSON directement, simplifie le parsing
        )
        
        # La réponse de l'API est directement un dictionnaire Python si format='json' est utilisé
        content_str = response['message']['content']
        
        # Le contenu est une chaîne de caractères JSON, il faut la parser
        potential_clips = json.loads(content_str)
        
        print(f"✅ Analyse terminée ! {len(potential_clips)} clips potentiels identifiés.")
        return potential_clips

    except json.JSONDecodeError as e:
        print(f"❌ Erreur de décodage JSON. L'IA n'a peut-être pas retourné un JSON valide. Réponse brute : {content_str}")
        return []
    except Exception as e:
        print(f"❌ Une erreur est survenue lors de la communication avec Ollama : {e}")
        return []

# --- Section de test ---
if __name__ == '__main__':
    # Cette section s'exécute seulement si vous lancez ce fichier directement
    # python montage/clip_finder.py
    # C'est utile pour tester le module de manière isolée.

    print("🚀 Lancement du test pour le module Clip Finder...")

    # 1. Créer une fausse transcription pour le test
    mock_transcript = [
        {'start': 0.0, 'end': 10.0, 'text': "Bonjour à tous et bienvenue dans cette longue vidéo où nous allons explorer de nombreux sujets."},
        {'start': 10.5, 'end': 25.0, 'text': "Le premier point est intéressant, mais pas exceptionnel. Parlons de la météo."},
        {'start': 25.5, 'end': 35.0, 'text': "Maintenant, abordons le vrai sujet. Vous êtes-vous déjà demandé pourquoi les projets échouent ?"},
        {'start': 35.5, 'end': 55.0, 'text': "La raison principale, et c'est une chose que peu de gens admettent, c'est un manque de clarté absolue dès le départ. C'est le secret numéro un."},
        {'start': 55.5, 'end': 80.0, 'text': "Laissez-moi vous donner une méthode en trois étapes pour définir cette clarté et garantir que vos projets réussissent à chaque fois. Prenez un papier et un stylo."},
        {'start': 80.5, 'end': 95.0, 'text': "Voilà, c'était le conseil du jour. Passons maintenant à un autre sujet, l'histoire des papillons."},
        {'start': 95.5, 'end': 120.0, 'text': "Les papillons sont fascinants, mais ce n'est pas ce qui nous intéresse pour un clip viral."},
    ]
    mock_duration = 120

    # 2. Appeler la fonction principale
    clips = find_potential_clips(mock_transcript, mock_duration)

    # 3. Afficher les résultats
    if clips:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="✨ Pépites Identifiées par l'IA ✨", show_header=True, header_style="bold magenta")
        table.add_column("Titre", style="cyan")
        table.add_column("Début (s)", style="green")
        table.add_column("Fin (s)", style="green")
        table.add_column("Durée (s)", style="yellow")
        table.add_column("Justification", style="white")

        for clip in clips:
            duration = clip.get('end_time', 0) - clip.get('start_time', 0)
            table.add_row(
                clip.get('title', 'N/A'),
                f"{clip.get('start_time', 0):.2f}",
                f"{clip.get('end_time', 0):.2f}",
                f"{duration:.2f}",
                clip.get('justification', 'N/A')
            )
        
        console.print(table)
    else:
        print("🔴 Aucun clip n'a été identifié lors du test.")
