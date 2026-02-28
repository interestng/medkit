"""
Command-line interface for the MedKit SDK.
"""

import json
import webbrowser

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from medkit import (
    ClinicalTrial,
    ConditionSummary,
    DrugExplanation,
    MedKit,
    MedKitError,
    ResearchPaper,
    SearchResults,
)
from medkit.ask_engine import AskEngine
from medkit.intelligence import ClinicalConclusion

app = typer.Typer(help="MedKit - Unified Medical API SDK")
console = Console()


@app.command()
def status():
    """
    Check the health status of all medical data providers.
    """
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
                status_str = (
                    "[bold green]ONLINE[/bold green]"
                    if healthy
                    else "[bold red]OFFLINE[/bold red]"
                )
                table.add_row(name, status_str, f"{latency:.0f}ms")
            except Exception:
                table.add_row(name, "[bold red]ERROR[/bold red]", "N/A")

        console.print(table)


@app.command()
def interactions(drugs: list[str]):
    """
    Check for potential interactions between a list of drugs.
    """
    # Flatten and split by commas if user provides "aspirin, warfarin" as one arg
    final_drugs = []
    for d in drugs:
        if "," in d:
            final_drugs.extend([x.strip() for x in d.split(",")])
        else:
            final_drugs.append(d.strip())

    with MedKit() as med:
        warns = med.interactions(final_drugs)
        if not warns:
            drugs_str = ", ".join(final_drugs)
            console.print(
                f"[bold green]No known interactions found for: "
                f"{drugs_str}[/bold green]"
            )
            return

        table = Table(title="Drug-Drug Interactions")
        table.add_column("Severity", style="bold red")
        table.add_column("Drugs")
        table.add_column("Risk")

        for w in warns:
            sev = w["warning"].severity
            sev_color = "red" if sev == "High" else "yellow"
            table.add_row(
                f"[bold {sev_color}]{sev}[/bold {sev_color}]",
                " + ".join(w["drugs"]),
                w["warning"].risk,
            )
        console.print(table)


@app.command()
def drug(name: str, as_json: bool = False):
    """
    Search for drug information using OpenFDA.
    """
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
            console.print(f"Manufacturer: {info.manufacturer}")
            if info.warnings:
                console.print("\n[bold red]Warnings:[/bold red]")
                for warning in info.warnings[:3]:
                    console.print(f"- {warning}")
                if len(info.warnings) > 3:
                    console.print("- (and more...)")
    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def papers(
    query: str,
    limit: int = 5,
    as_json: bool = False,
    links: bool = False,
    open: bool = False,
):
    """
    Search for research papers on PubMed.
    """
    try:
        with MedKit() as med:
            results = med.papers(query, limit=limit)

            if as_json:
                json_data = [paper.model_dump() for paper in results]
                console.print(json.dumps(json_data, indent=2))
                return

            table = Table(title=f"PubMed Papers for '{query}'")
            table.add_column("PMID", style="cyan", no_wrap=True)
            table.add_column("Year", style="magenta")
            table.add_column("Title")
            table.add_column("Journal")

            for p in results:
                year_str = str(p.year) if p.year else "N/A"
                table.add_row(p.pmid, year_str, p.title, p.journal)

            console.print(table)

            if links:
                console.print("\n[bold cyan]Actionable Links:[/bold cyan]")
                for p in results:
                    console.print(
                        f"- {p.title[:50]}... \n  [underline]{p.url}[/underline]"
                    )

            if open and results:
                console.print(
                    "\n[bold green]Opening top result in browser...[/bold green]"
                )
                webbrowser.open(results[0].url)
    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def trials(
    condition: str,
    limit: int = 5,
    as_json: bool = False,
    links: bool = False,
    open: bool = False,
    recruiting: bool = typer.Option(
        False, "--recruiting", help="Only show recruiting trials"
    ),
):
    """
    Search for clinical trials on ClinicalTrials.gov.
    """
    try:
        with MedKit() as med:
            results = med.trials(condition, limit=limit, recruiting=recruiting)

            if as_json:
                json_data = [trial.model_dump() for trial in results]
                console.print(json.dumps(json_data, indent=2))
                return

            table = Table(title=f"Clinical Trials for '{condition}'")
            table.add_column("NCT ID", style="cyan", no_wrap=True)
            table.add_column("Status", style="green")
            table.add_column("Title")

            for t in results:
                table.add_row(t.nct_id, t.status, t.title)

            console.print(table)

            if links:
                console.print("\n[bold magenta]Actionable Links:[/bold magenta]")
                for t in results:
                    console.print(f"- {t.nct_id}: [underline]{t.url}[/underline]")

            if open and results:
                console.print(
                    "\n[bold green]Opening top trial in browser...[/bold green]"
                )
                webbrowser.open(results[0].url)
    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def search(query: str, as_json: bool = False):
    """
    Unified search across drugs, research papers, and clinical trials.
    """
    try:
        with MedKit() as med:
            with console.status(
                f"[bold blue]Searching for '{query}' across all sources...[/bold blue]"
            ):
                results = med.search(query)

            if as_json:
                console.print(results.model_dump_json(indent=2))
                return

            if results.metadata:
                l_msg = f"\n[dim italic]Latency: {results.metadata.query_time:.2f}s | "
                s_msg = f"Sources: {', '.join(results.metadata.sources)}[/dim italic]"
                console.print(l_msg + s_msg)

            _render_search_results(results, query)

    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def summary(query: str):
    """
    Get a concise medical summary for a condition or term.
    """
    try:
        with MedKit() as med:
            with console.status(
                f"[bold blue]Generating summary for '{query}'...[/bold blue]"
            ):
                s = med.summary(query)

            _render_summary(s)

    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def explain(name: str):
    """
    Get a comprehensive explanation of a drug combining multiple APIs.
    """
    try:
        with MedKit() as med:
            status_msg = (
                f"[bold blue]Fetching comprehensive data for "
                f"{name}...[/bold blue]"
            )
            with console.status(status_msg):
                explanation = med.explain_drug(name)

            _render_explanation(explanation, name)

    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def ask(question: str, debug: bool = False):
    """
    Ask a medical question in plain English.
    """
    try:
        if debug:
            intent = AskEngine.route(question)
            msg = "[bold yellow]DEBUG:[/bold yellow] Routing intent detected: "
            console.print(f"{msg}[bold cyan]{intent}[/bold cyan]")

        with MedKit() as med:
            with console.status(
                f"[bold blue]Processing question: '{question}'...[/bold blue]"
            ):
                # We need the cleaned query for rendering
                cleaned_q = AskEngine.clean_query(question)
                res = med.ask(question)

            if isinstance(res, SearchResults):
                _render_search_results(res, question)
            elif isinstance(res, ConditionSummary):
                _render_summary(res)
            elif isinstance(res, DrugExplanation):
                _render_explanation(res, cleaned_q)
            elif isinstance(res, ClinicalConclusion):
                _render_conclusion(res)
            elif isinstance(res, list) and res and isinstance(res[0], ResearchPaper):
                _render_papers(res)
            elif isinstance(res, list) and res and isinstance(res[0], ClinicalTrial):
                _render_trials(res)
            else:
                console.print(res)

    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


def _render_explanation(e, name: str):
    if e.drug_info:
        console.print("\n[bold green]=== FDA Information ===[/bold green]")
        console.print(f"Brand Name: {e.drug_info.brand_name}")
        console.print(f"Generic Name: {e.drug_info.generic_name}")
        console.print(f"Manufacturer: {e.drug_info.manufacturer}")
    else:
        console.print(f"\n[bold yellow]No FDA info found for '{name}'.[/bold yellow]")

    if e.papers:
        _render_papers(e.papers)

    if e.trials:
        _render_trials(e.trials)
    else:
        console.print("\n[bold magenta]=== Clinical Trials ===[/bold magenta]")
        console.print("No active recruiting trials found")


def _render_search_results(results: SearchResults, query: str):
    if results.drugs:
        console.print("\n[bold green]=== Found Drugs ===[/bold green]")
        for d in results.drugs:
            console.print(f"Brand Name: {d.brand_name} | Generic: {d.generic_name}")

    if results.papers:
        years = [p.year for p in results.papers if p.year]
        year_range = f" ({max(years)}–{min(years)})" if years else ""
        console.print(
            f"\n[bold cyan]=== Top Research Papers{year_range} ===[/bold cyan]"
        )
        for i, p in enumerate(results.papers, 1):
            console.print(f"{i}. {p.title} ({p.year})")

    if results.trials:
        console.print("\n[bold magenta]=== Clinical Trials ===[/bold magenta]")
        for t in results.trials:
            console.print(f"- {t.nct_id}: {t.status} - {t.title}")
    else:
        console.print("\n[bold magenta]=== Clinical Trials ===[/bold magenta]")
        console.print("No active recruiting trials found")

    if results.metadata:
        latency_msg = f"\n[dim italic]Latency: {results.metadata.query_time:.2f}s | "
        sources_msg = f"Sources: {', '.join(results.metadata.sources)}[/dim italic]"
        console.print(latency_msg + sources_msg)


def _render_summary(s: ConditionSummary):
    console.print(
        f"\n[bold white on blue] Condition: {s.condition.title()} [/bold white on blue]"
    )
    if s.drugs:
        console.print("\n[bold green]Drugs:[/bold green]")
        for d in s.drugs:
            console.print(f"- {d}")
    if s.papers:
        console.print("\n[bold cyan]Latest Research:[/bold cyan]")
        for p in s.papers[:5]:
            console.print(f"- {p.title} ({p.year})")
    if s.trials:
        console.print("\n[bold magenta]Clinical Trials:[/bold magenta]")
        for t in s.trials:
            console.print(f"- {t.nct_id}: {t.status} - {t.title}")
    else:
        console.print("\n[bold magenta]Clinical Trials:[/bold magenta]")
        console.print("No active recruiting trials found")


def _render_papers(papers: list[ResearchPaper]):
    console.print("\n[bold cyan]=== Latest Research ===[/bold cyan]")
    for p in papers:
        console.print(f"- {p.title} ({p.year})")


def _render_trials(trials: list[ClinicalTrial]):
    console.print("\n[bold magenta]=== Clinical Trials ===[/bold magenta]")
    for t in trials:
        console.print(f"- {t.nct_id}: {t.status} - {t.title}")


@app.command()
def graph(query: str):
    """
    Visualize medical relationships for a term.
    """
    try:
        with MedKit() as med:
            with console.status(
                f"[bold blue]Building relationship graph for '{query}'...[/bold blue]"
            ):
                g = med.graph(query)

            tree = Tree(f"[bold white on blue] {query.title()} [/bold white on blue]")

            # 1. Add specific Drug branch with nested correlations
            drug_branch = tree.add("[bold]Drugs[/bold]")
            drugs_found = [n for n in g.nodes if n.type == "drug"]
            if not drugs_found:
                drug_branch.add("[dim]None found[/dim]")
            else:
                for drug_node in drugs_found:
                    d_node = drug_branch.add(f"{drug_node.label}")
                    # Find trials linked to THIS drug
                    linked_trials = [
                        target_id for source_id, target_id, relation in g.edges 
                        if source_id == drug_node.id and relation == "intervenes"
                    ]
                    if linked_trials:
                        for t_id in linked_trials:
                            # Find trial label
                            t_node = next((n for n in g.nodes if n.id == t_id), None)
                            t_label = t_node.label if t_node else t_id
                            d_node.add(f"[dim]Intervenes in:[/dim] {t_label}")

            # 2. Add Trials branch (all)
            trial_branch = tree.add("[bold]Trials[/bold]")
            trials_found = [n for n in g.nodes if n.type == "trial"]
            if not trials_found:
                trial_branch.add("[dim]None found[/dim]")
            else:
                for trial_node in trials_found:
                    trial_branch.add(f"{trial_node.label}")

            # 3. Add Papers branch
            paper_branch = tree.add("[bold]Papers[/bold]")
            papers_found = [n for n in g.nodes if n.type == "paper"]
            if not papers_found:
                paper_branch.add("[dim]None found[/dim]")
            else:
                for paper_node in papers_found:
                    paper_branch.add(f"{paper_node.label}")

            console.print("\n", tree)

    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def conclude(query: str):
    """
    Get a synthesized clinical conclusion for a term.
    """
    try:
        with MedKit() as med:
            with console.status(
                f"[bold blue]Synthesizing evidence for '{query}'...[/bold blue]"
            ):
                conclusion = med.conclude(query)
            _render_conclusion(conclusion)
    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def export(query: str, format: str = "json", path: str = "results.json"):
    """
    Export search results for a term to a file.
    """
    try:
        with MedKit() as med:
            with console.status(
                f"[bold blue]Exporting data for '{query}' to {path}...[/bold blue]"
            ):
                results = med.search(query)
                med.export(results, path, format=format)
            console.print(
                f"[bold green]Successfully exported results to {path}[/bold green]"
            )
    except MedKitError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


def _render_conclusion(c: ClinicalConclusion):
    console.print("\n[bold white on green] Clinical Conclusion [/bold white on green]")
    console.print(f"\n[bold]Summary:[/bold] {c.summary}")
    
    # Evidence Meter
    score = c.evidence_score
    color = "green" if score > 0.7 else "yellow" if score > 0.4 else "red"
    meter = "█" * int(score * 20) + "░" * (20 - int(score * 20))
    console.print(
        f"[bold]Evidence Strength:[/bold] [{color}]{meter}[/{color}] {score:.2f}"
    )

    console.print("\n[bold]Key Findings:[/bold]")
    for finding in c.key_findings:
        console.print(f"• {finding}")

    console.print(f"\n[bold cyan]Recommendation:[/bold cyan] {c.recommendation}\n")


if __name__ == "__main__":
    app()
