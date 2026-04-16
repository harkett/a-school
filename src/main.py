import typer
from pathlib import Path
from datetime import date
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.prompts import build_prompt
from src.generator import generate
from src.formats import to_markdown, save

app = typer.Typer(help="Générateur d'activités pédagogiques de français par IA")
console = Console()


@app.command()
def comprehension(
    texte: str = typer.Option(..., "--texte", "-t", help="Fichier texte ou texte direct"),
    niveau: str = typer.Option("4e", "--niveau", "-n", help="Niveau scolaire (ex: 6e, 5e, 4e, 3e)"),
    nb: int = typer.Option(10, "--nb-questions", "-q", help="Nombre de questions"),
    type_questions: str = typer.Option("ouvertes", "--type", help="ouvertes / QCM / mélange"),
    sortie: str = typer.Option(None, "--sortie", "-o", help="Fichier de sortie (.md)"),
):
    """Génère des questions de compréhension sur un texte."""
    contenu_texte = _lire_texte(texte)
    prompt = build_prompt("comprehension", contenu_texte, niveau=niveau, nb=nb, type_questions=type_questions)
    _executer(prompt, "comprehension", niveau, sortie)


@app.command()
def pistes(
    texte: str = typer.Option(..., "--texte", "-t", help="Fichier texte ou texte direct"),
    niveau: str = typer.Option("4e", "--niveau", "-n", help="Niveau scolaire"),
    nb: int = typer.Option(3, "--nb-pistes", help="Nombre de pistes"),
    angle: str = typer.Option("thématique", "--angle", help="thématique / stylistique / narratif / personnages"),
    sortie: str = typer.Option(None, "--sortie", "-o", help="Fichier de sortie (.md)"),
):
    """Génère des pistes de lecture / axes de réflexion."""
    contenu_texte = _lire_texte(texte)
    prompt = build_prompt("pistes", contenu_texte, niveau=niveau, nb=nb, angle=angle)
    _executer(prompt, "pistes", niveau, sortie)


@app.command()
def reecriture(
    texte: str = typer.Option(..., "--texte", "-t", help="Fichier texte ou texte direct"),
    niveau: str = typer.Option("4e", "--niveau", "-n", help="Niveau scolaire"),
    transformation: str = typer.Option("direct vers indirect", "--transformation", help="Type de transformation"),
    sortie: str = typer.Option(None, "--sortie", "-o", help="Fichier de sortie (.md)"),
):
    """Génère un exercice de réécriture."""
    contenu_texte = _lire_texte(texte)
    prompt = build_prompt("reecriture", contenu_texte, niveau=niveau, transformation=transformation)
    _executer(prompt, "reecriture", niveau, sortie)


def _lire_texte(texte: str) -> str:
    p = Path(texte)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8")
    return texte


def _executer(prompt: str, activite: str, niveau: str, sortie: str | None):
    with console.status("[bold green]Génération en cours...", spinner="dots"):
        resultat = generate(prompt)

    md_content = to_markdown(activite, niveau, resultat)

    if sortie is None:
        today = date.today().strftime("%Y%m%d")
        sortie = f"outputs/{activite}_{today}.md"

    Path(sortie).parent.mkdir(parents=True, exist_ok=True)
    save(md_content, sortie)

    console.print(Panel(Markdown(md_content), title=f"[bold green]{sortie}", border_style="green"))
    console.print(f"\n[bold]Fichier sauvegardé :[/bold] {sortie}")


if __name__ == "__main__":
    app()
