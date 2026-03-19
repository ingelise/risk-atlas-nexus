import json
import os
from pathlib import Path
from typing import Literal, Optional

import typer
from rich.console import Console
from rich.table import Table

from ai_atlas_nexus import AIAtlasNexus
from ai_atlas_nexus.blocks.inference import (
    OllamaInferenceEngine,
    RITSInferenceEngine,
    VLLMInferenceEngine,
    WMLInferenceEngine,
)
from ai_atlas_nexus.exceptions import RiskInferenceError
from ai_atlas_nexus.toolkit.logging import configure_logger


app = typer.Typer()
logger = configure_logger(__name__)
console = Console()


@app.command()
def identify(
    usecase: Optional[str] = typer.Argument(
        None, help="Usecase description text (or use --file to read from file)"
    ),
    taxonomy: str = typer.Option(
        "ibm-risk-atlas",
        "--taxonomy",
        help="Risk taxonomy ID",
    ),
    engine: str = typer.Option(
        "ollama",
        "--engine",
        help="Inference engine: ollama | wml | vllm | rits",
    ),
    model: str = typer.Option(
        "granite3.3:8b",
        "--model",
        help="Model name or path",
    ),
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        help="Inference server URL (reads env vars as fallback)",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="API key (reads env vars as fallback)",
    ),
    project_id: Optional[str] = typer.Option(
        None,
        "--project-id",
        help="WML project ID (WML only, or reads WML_PROJECT_ID env var)",
    ),
    max_risks: Optional[int] = typer.Option(
        None,
        "--max-risks",
        help="Max number of risks to return",
    ),
    zero_shot: bool = typer.Option(
        False,
        "--zero-shot/--no-zero-shot",
        help="Skip CoT examples",
    ),
    show_descriptions: bool = typer.Option(
        True,
        "--show-descriptions/--no-show-descriptions",
        help="Include full risk descriptions in output",
    ),
    output: Literal["table", "json"] = typer.Option(
        "table",
        "--output",
        help="Output format",
    ),
    file: Optional[Path] = typer.Option(
        None,
        "--file",
        help="Read usecase from a text file instead of inline",
    ),
) -> None:
    """
    Identify potential AI risks from a usecase description.

    Pass a USECASE string directly, or use --file to read from a file.
    """
    try:
        # Get usecase from argument or file
        if file:
            if not file.exists():
                console.print(
                    f"[red]Error:[/red] File '{file}' not found",
                    style="bold",
                )
                raise typer.Exit(code=1)
            usecase_text = file.read_text().strip()
        elif usecase:
            usecase_text = usecase
        else:
            console.print(
                "[red]Error:[/red] Please provide a USECASE argument or use --file",
                style="bold",
            )
            raise typer.Exit(code=1)

        # Validate taxonomy
        valid_taxonomies = ["ibm-risk-atlas", "ibm-attack-risk-atlas", "nist-ai-rmf"]
        if taxonomy not in valid_taxonomies:
            console.print(
                f"[yellow]Warning:[/yellow] Unknown taxonomy '{taxonomy}'. "
                f"Proceeding anyway.",
                style="bold",
            )

        # Validate engine
        engine_lower = engine.lower()
        if engine_lower not in ["ollama", "wml", "vllm", "rits"]:
            console.print(
                f"[red]Error:[/red] Invalid engine '{engine}'. "
                f"Must be one of: ollama, wml, vllm, rits",
                style="bold",
            )
            raise typer.Exit(code=1)

        # Build credentials dict based on engine
        credentials = {}

        if engine_lower == "ollama":
            # Try to get from option first, then env var
            ollama_url = api_url or os.getenv("OLLAMA_API_URL")
            if not ollama_url:
                console.print(
                    "[red]Error:[/red] No API URL provided for Ollama. "
                    "Use --api-url or set OLLAMA_API_URL env var",
                    style="bold",
                )
                raise typer.Exit(code=1)
            credentials["api_url"] = ollama_url

        elif engine_lower == "rits":
            rits_url = api_url or os.getenv("RITS_API_URL")
            rits_key = api_key or os.getenv("RITS_API_KEY")
            if not rits_url or not rits_key:
                console.print(
                    "[red]Error:[/red] Missing RITS credentials. "
                    "Provide --api-url/--api-key or set RITS_API_URL/RITS_API_KEY env vars",
                    style="bold",
                )
                raise typer.Exit(code=1)
            credentials["api_url"] = rits_url
            credentials["api_key"] = rits_key

        elif engine_lower == "wml":
            wml_url = api_url or os.getenv("WML_API_URL")
            wml_key = api_key or os.getenv("WML_API_KEY")
            wml_proj = project_id or os.getenv("WML_PROJECT_ID")
            if not wml_url or not wml_key or not wml_proj:
                console.print(
                    "[red]Error:[/red] Missing WML credentials. "
                    "Provide --api-url, --api-key, --project-id "
                    "or set WML_API_URL, WML_API_KEY, WML_PROJECT_ID env vars",
                    style="bold",
                )
                raise typer.Exit(code=1)
            credentials["api_url"] = wml_url
            credentials["api_key"] = wml_key
            credentials["project_id"] = wml_proj

        elif engine_lower == "vllm":
            vllm_url = api_url or os.getenv("VLLM_API_URL")
            if not vllm_url:
                console.print(
                    "[red]Error:[/red] No API URL provided for vLLM. "
                    "Use --api-url or set VLLM_API_URL env var",
                    style="bold",
                )
                raise typer.Exit(code=1)
            credentials["api_url"] = vllm_url

        # Instantiate the appropriate inference engine
        if engine_lower == "ollama":
            inference_engine = OllamaInferenceEngine(
                model_name_or_path=model, credentials=credentials
            )
        elif engine_lower == "rits":
            inference_engine = RITSInferenceEngine(
                model_name_or_path=model, credentials=credentials
            )
        elif engine_lower == "wml":
            inference_engine = WMLInferenceEngine(
                model_name_or_path=model, credentials=credentials
            )
        elif engine_lower == "vllm":
            inference_engine = VLLMInferenceEngine(
                model_name_or_path=model, credentials=credentials
            )

        # Call identify_risks_from_usecases
        nexus = AIAtlasNexus()
        result = nexus.identify_risks_from_usecases(
            usecases=[usecase_text],
            inference_engine=inference_engine,
            taxonomy=taxonomy,
            max_risk=max_risks,
            zero_shot_only=zero_shot,
        )

        # Handle result
        if not result or not result[0]:
            console.print("[yellow]No risks identified for the provided usecase.[/yellow]")
            raise typer.Exit(code=0)

        risks = result[0]  # First element of List[List[Risk]]

        # Format output
        if output == "json":
            _output_json(risks, show_descriptions)
        else:
            _output_table(risks, show_descriptions)

    except typer.Exit:
        raise
    except RiskInferenceError as e:
        console.print(
            f"[red]Risk Inference Error:[/red] {e.message}",
            style="bold",
        )
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(
            f"[red]Error:[/red] {str(e)}",
            style="bold",
        )
        logger.exception("Unexpected error during risk identification")
        raise typer.Exit(code=1)


def _output_table(risks, show_descriptions: bool) -> None:
    """Output risks as a formatted table."""
    table = Table(title="Identified Risks")

    table.add_column("Risk Name", style="cyan")
    table.add_column("Group", style="magenta")
    table.add_column("Risk Type", style="yellow")
    if show_descriptions:
        table.add_column("Concern", style="green")

    for risk in risks:
        group = risk.isPartOf or "N/A"
        risk_type = risk.risk_type or "N/A"

        if show_descriptions:
            concern = risk.concern or risk.description or "N/A"
            # Truncate long concerns for table display
            if len(concern) > 80:
                concern = concern[:77] + "..."
            table.add_row(risk.name or "N/A", group, risk_type, concern)
        else:
            table.add_row(risk.name or "N/A", group, risk_type)

    console.print(table)


def _output_json(risks, show_descriptions: bool) -> None:
    """Output risks as JSON."""
    output_list = []

    for risk in risks:
        risk_dict = {
            "id": risk.id,
            "name": risk.name,
            "tag": risk.tag,
            "risk_type": risk.risk_type,
            "phase": risk.phase,
            "group": risk.isPartOf,
        }

        if show_descriptions:
            risk_dict["description"] = risk.description
            risk_dict["concern"] = risk.concern

        # Add only non-None fields
        risk_dict = {k: v for k, v in risk_dict.items() if v is not None}
        output_list.append(risk_dict)

    console.print(json.dumps(output_list, indent=2))


if __name__ == "__main__":
    app()
