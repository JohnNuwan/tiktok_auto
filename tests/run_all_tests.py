#!/usr/bin/env python3
"""
Script de lancement de tous les tests pour TikTok_Auto
Combine les tests d'imports, unitaires et système complet
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

def run_import_tests():
    """Lance les tests d'imports"""
    console = Console()
    
    console.print(Panel.fit(
        "🔍 Tests d'Imports",
        style="bold blue"
    ))
    
    try:
        from test_imports import main as import_main
        import_main()
        return True
    except Exception as e:
        console.print(f"❌ Erreur lors des tests d'imports: {e}")
        return False

def run_unit_tests():
    """Lance les tests unitaires"""
    console = Console()
    
    console.print(Panel.fit(
        "🧪 Tests Unitaires",
        style="bold blue"
    ))
    
    try:
        from test_unit import run_tests as unit_main
        success = unit_main()
        return success
    except Exception as e:
        console.print(f"❌ Erreur lors des tests unitaires: {e}")
        return False

def run_system_tests():
    """Lance les tests système complets"""
    console = Console()
    
    console.print(Panel.fit(
        "🔧 Tests Système Complets",
        style="bold blue"
    ))
    
    try:
        from test_complet import main as system_main
        system_main()
        return True
    except Exception as e:
        console.print(f"❌ Erreur lors des tests système: {e}")
        return False

def display_final_results(results):
    """Affiche les résultats finaux de tous les tests"""
    console = Console()
    
    # Titre
    title = Panel.fit(
        "🎯 Rapport Final - Tous les Tests",
        style="bold blue"
    )
    console.print(title)
    
    # Tableau des résultats
    results_table = Table(title="📊 Résultats des Tests", show_header=True)
    results_table.add_column("Type de Test", style="cyan")
    results_table.add_column("Statut", style="green")
    results_table.add_column("Détails", style="white")
    
    for test_type, result in results.items():
        if result:
            results_table.add_row(
                test_type,
                "✅ Réussi",
                "Tous les tests passés"
            )
        else:
            results_table.add_row(
                test_type,
                "❌ Échec",
                "Certains tests ont échoué"
            )
    
    console.print(results_table)
    console.print()
    
    # Calcul du score global
    total_tests = len(results)
    successful_tests = sum(results.values())
    global_score = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    if global_score >= 90:
        status_style = "bold green"
        status_emoji = "🎉"
        status_text = "Excellent ! Le système est prêt pour la production"
    elif global_score >= 70:
        status_style = "bold yellow"
        status_emoji = "⚠️"
        status_text = "Bon ! Le système est fonctionnel avec quelques améliorations possibles"
    else:
        status_style = "bold red"
        status_emoji = "❌"
        status_text = "Attention ! Le système nécessite des corrections"
    
    # Résumé final
    summary = Panel.fit(
        f"{status_emoji} Score Global: {global_score:.1f}% ({successful_tests}/{total_tests} tests réussis)\n"
        f"{status_text}",
        style=status_style
    )
    console.print(summary)
    
    # Recommandations
    console.print("\n💡 Recommandations:")
    
    if not results.get('Imports', False):
        console.print("  • Corrigez les problèmes d'imports des modules")
    
    if not results.get('Unitaires', False):
        console.print("  • Vérifiez les fonctionnalités de base du système")
    
    if not results.get('Système', False):
        console.print("  • Assurez-vous que toutes les dépendances sont installées")
    
    if global_score >= 90:
        console.print("  • 🚀 Le système est prêt à être utilisé !")
    
    return global_score

def main():
    """Fonction principale de lancement de tous les tests"""
    console = Console()
    
    console.print(Panel.fit(
        "🧪 Suite de Tests Complète - TikTok_Auto",
        style="bold blue"
    ))
    
    console.print("Cette suite va exécuter tous les tests disponibles :")
    console.print("  • Tests d'imports (vérification des modules)")
    console.print("  • Tests unitaires (fonctionnalités de base)")
    console.print("  • Tests système complets (intégration)")
    console.print()
    
    # Exécuter tous les tests
    results = {}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Tests d'imports
        task1 = progress.add_task("Tests d'imports...", total=None)
        results['Imports'] = run_import_tests()
        progress.update(task1, completed=True)
        
        # Tests unitaires
        task2 = progress.add_task("Tests unitaires...", total=None)
        results['Unitaires'] = run_unit_tests()
        progress.update(task2, completed=True)
        
        # Tests système
        task3 = progress.add_task("Tests système...", total=None)
        results['Système'] = run_system_tests()
        progress.update(task3, completed=True)
    
    # Afficher les résultats finaux
    global_score = display_final_results(results)
    
    # Conclusion
    console.print(f"\n✅ Suite de tests terminée !")
    
    if global_score >= 90:
        console.print("🎉 Félicitations ! Votre système TikTok_Auto est prêt !")
    elif global_score >= 70:
        console.print("👍 Votre système est fonctionnel avec quelques ajustements mineurs.")
    else:
        console.print("🔧 Quelques corrections sont nécessaires avant utilisation.")
    
    return global_score

if __name__ == "__main__":
    main() 