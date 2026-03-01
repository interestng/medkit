"""
Command-line interface for the MedKit SDK.
"""

import json
import webbrowser
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from medkit import (
    ClinicalConclusion,
    ConditionSummary,
    DrugExplanation,
    MedKit,
    MedKitError,
    SearchResults,
)

app = typer.Typer(help="MedKit - Unified Medical API SDK")
console = Console()


@app.command()
def status():
    """Check the health status of all medical data providers."""
    with MedKit() as med:
        table = Table(title="MedKit Provider Health")
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Latency", justify="right")

        for name, provider in med._providers.items():
            import time

            start = time.perf_counter()
            try:
                healthy = provider.health_check()
                latency = (time.perf_counter() - start) * 1000
                st = (
                    "[bold green]ONLINE[/bold green]"
                    if healthy
                    else "[bold red]OFFLINE[/bold red]"
                )
                table.add_row(name, st, f"{latency:.0f}ms")
            except Exception:
                table.add_row(name, "[bold red]ERROR[/bold red]", "N/A")

        console.print(table)


@app.command()
def interactions(drugs: str):
    """Check for potential interactions between a list of drugs (comma-separated)."""
    final_drugs = [d.strip() for d in drugs.split(",") if d.strip()]

    with MedKit() as med:
        warns = med.interactions(final_drugs)
        if not warns:
            console.print(
                f"[bold green]No interactions found for: {', '.join(final_drugs)}[/bold green]"
            )
            return

        table = Table(title="Drug-Drug Interactions")
        table.add_column("Drugs", style="cyan")
        table.add_column("Severity", style="bold")
        table.add_column("Risk")

        for w in warns:
            warning_obj = w.get("warning")
            if hasattr(warning_obj, "severity"):
                sev = getattr(warning_obj, "severity")
                risk = getattr(warning_obj, "risk")
            else:
                sev = "Unknown"
                risk = "N/A"

            sev_color = "red" if "High" in sev else "yellow"
            table.add_row(
                " + ".join(w["drugs"]),
                f"[bold {sev_color}]{sev}[/bold {sev_color}]",
                risk,
            )
        console.print(table)


@app.command()
def drug(name: str, as_json: bool = False):
    """Search for drug information using OpenFDA."""
    try:
        with MedKit() as med:
            info = med.drug(name)

            if as_json:
                console.print(info.model_dump_json(indent=2))
                return

            console.print(
                f"[bold green]Drug Information: {info.brand_name}[/bold green]"
            )
            console.print(f"Generic Name: {info.generic_name}")
            console.print(f"Manufacturer: {info.manufacturer or 'N/A'}")

            if info.indications:
                console.print("\n[bold cyan]Indications:[/bold cyan]")
                for ind in info.indications[:3]:
                    console.print(f"- {ind[:200]}...")

    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def papers(query: str, limit: int = 5, as_json: bool = False, open: bool = False):
    """Search for research papers on PubMed."""
    try:
        with MedKit() as med:
            results = med.papers(query, limit=limit)

            if as_json:
                data = [p.model_dump() for p in results]
                console.print(json.dumps(data, indent=2))
                return

            table = Table(title=f"PubMed Papers for '{query}'")
            table.add_column("PMID", style="cyan")
            table.add_column("Year", style="magenta")
            table.add_column("Title")

            for p in results:
                table.add_row(p.pmid, str(p.year or "N/A"), p.title)

            console.print(table)

            if open and results:
                webbrowser.open(results[0].full_url)
    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def trials(
    condition: str, limit: int = 5, as_json: bool = False, recruiting: bool = False
):
    """Search for clinical trials on ClinicalTrials.gov."""
    try:
        with MedKit() as med:
            results = med.trials(condition, limit=limit, recruiting=recruiting)

            if as_json:
                data = [t.model_dump() for t in results]
                console.print(json.dumps(data, indent=2))
                return

            if results:
                console.print(
                    f"\n[bold magenta]Clinical Trials for '{condition}'[/bold magenta]"
                )
                for t in results:
                    status = t.status or "N/A"
                    title = t.title or "Unknown Title"
                    console.print(f"- [cyan]{t.nct_id}[/cyan]: [green]{status}[/green] - {title}")
            else:
                console.print(
                    f"[yellow]No recruiting clinical trials found for '{condition}'.[/yellow]"
                )
    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def search(query: str, as_json: bool = False):
    """Unified search across drugs, papers, and trials."""
    import asyncio

    from medkit import AsyncMedKit

    async def _run():
        try:
            async with AsyncMedKit() as med:
                results = await med.search(query)

                if as_json:
                    console.print(results.model_dump_json(indent=2))
                    return

                _render_search_results(results, query)

                offline = results.metadata.offline_providers
                if offline:
                    names = ", ".join(offline)
                    console.print(
                        f"\n[dim][!] Limited results. Providers offline: {names}[/dim]"
                    )
        except MedKitError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    asyncio.run(_run())


@app.command()
def ask(question: str, debug: bool = False):
    """Ask a medical question in plain English."""
    import asyncio

    from medkit import AsyncMedKit

    async def _run():
        try:
            async with AsyncMedKit() as med:
                with console.status(
                    f"[bold blue]Processing: '{question}'...[/bold blue]"
                ):
                    res = await med.ask(question)

                if isinstance(res, SearchResults) and not any(
                    [res.drugs, res.papers, res.trials]
                ):
                    console.print(
                        f"[yellow]No information found for '{question}'. "
                        "Try stripping medical jargon.[/yellow]"
                    )
                elif isinstance(res, SearchResults):
                    _render_search_results(res, question)
                elif isinstance(res, ConditionSummary):
                    _render_summary(res)
                elif isinstance(res, DrugExplanation):
                    _render_explanation(res)
                elif isinstance(res, ClinicalConclusion):
                    _render_conclusion(res)
                else:
                    console.print(str(res))

                # Use metadata if available via res.metadata or similar
                # DrugExplanation and others don't have metadata yet,
                # but SearchResults (passed to synthesize) does.
                # For now, we rely on the search results within the engine.
        except MedKitError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    asyncio.run(_run())


def _render_search_results(results: Any, query: str):
    if hasattr(results, "drugs") and results.drugs:
        console.print("\n[bold green]=== Drugs ===[/bold green]")
        for d in results.drugs[:3]:
            console.print(f"- {d.brand_name} ({d.generic_name})")

    if hasattr(results, "papers") and results.papers:
        console.print("\n[bold cyan]=== Research Papers ===[/bold cyan]")
        for p in results.papers[:3]:
            console.print(f"- {p.title} ({p.year or 'N/A'})")

    if hasattr(results, "trials") and results.trials:
        console.print("\n[bold magenta]=== Clinical Trials ===[/bold magenta]")
        for t in results.trials[:3]:
            console.print(f"- {t.nct_id}: {t.status or 'N/A'}")


def _render_summary(s: ConditionSummary):
    console.print(f"\n[bold blue]Condition: {s.condition}[/bold blue]")
    if s.drugs:
        drug_list = ", ".join(s.drugs[:5])
        console.print(f"[bold]Relevant Drugs:[/bold] {drug_list}")
    if s.papers:
        count = len(s.papers)
        console.print(
            f"[bold cyan]Scientific Evidence:[/bold cyan] {count} publications found."
        )
        for p in s.papers[:2]:
            console.print(f"  - {p.title} ({p.year or 'N/A'})")
    if s.trials:
        console.print(
            f"[bold magenta]Clinical Trials:[/bold magenta] {len(s.trials)} studies identified."
        )


def _render_explanation(e: DrugExplanation):
    if e.drug_info:
        console.print(f"\n[bold green]Drug: {e.drug_info.brand_name}[/bold green]")
        console.print(f"Generic: {e.drug_info.generic_name}")
        console.print(f"Manufacturer: {e.drug_info.manufacturer or 'N/A'}")
        if e.drug_info.indications:
            console.print(f"Indications: {e.drug_info.indications[0][:150]}...")

    if e.papers:
        console.print(
            f"\n[bold cyan]Key Research ({len(e.papers)} papers):[/bold cyan]"
        )
        for p in e.papers[:3]:
            console.print(f"- {p.title}")

    if e.trials:
        console.print(
            f"\n[bold magenta]Related Trials ({len(e.trials)}):[/bold magenta]"
        )
        for t in e.trials[:3]:
            console.print(f"- {t.nct_id}: {t.status}")


def _render_conclusion(c: ClinicalConclusion):
    console.print("\n[bold white on green] Clinical Conclusion [/bold white on green]")
    console.print(f"\n[bold]Summary:[/bold] {c.summary}")

    score = getattr(c, "confidence_score", 0.0)
    color = "green" if score > 0.7 else "yellow" if score > 0.4 else "red"
    meter = "█" * int(score * 20) + "░" * (20 - int(score * 20))
    console.print(
        f"[bold]Evidence Confidence:[/bold] [{color}]{meter}[/{color}] {score:.2f}"
    )

    interv = ", ".join(getattr(c, "top_interventions", []))
    console.print(f"\n[bold cyan]Top Interventions:[/bold cyan] {interv}")


if __name__ == "__main__":
    app()
