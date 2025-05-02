import os
import argparse
import math
import re
import ast
import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
import json
from pathlib import Path
import networkx as nx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.panel import Panel
from rich import box
from rich.columns import Columns
from rich.tree import Tree
from rich.markdown import Markdown
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
log = logging.getLogger("rich")

console = Console()

@dataclass
class CodeMetrics:
    lines: int = 0
    complexity: float = 0.0
    duplicates: int = 0
    documentation_score: float = 0.0
    maintainability_index: float = 0.0

    def __add__(self, other):
        if not isinstance(other, CodeMetrics):
            return NotImplemented
        return CodeMetrics(
            lines=self.lines + other.lines,
            complexity=self.complexity + other.complexity,
            duplicates=self.duplicates + other.duplicates,
            documentation_score=self.documentation_score + other.documentation_score,
            maintainability_index=self.maintainability_index + other.maintainability_index
        )

class CodeAnalyzer:
    def __init__(self):
        self.metrics = defaultdict(CodeMetrics)
        self.duplicate_chunks = set()
        self.complexity_threshold = 10
        self.doc_threshold = 0.2
        self.min_lines_for_analysis = 5

    def is_valid_python(self, code: str) -> bool:
        """Check if code is valid Python syntax"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
        except Exception:
            return False

    def calculate_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity using AST"""
        if not code.strip() or len(code.splitlines()) < self.min_lines_for_analysis:
            return 1.0

        try:
            if not self.is_valid_python(code):
                return 1.0

            tree = ast.parse(code)
            complexity = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.Match,
                                  ast.Try, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            return float(complexity)
        except Exception as e:
            log.warning(f"Error calculating complexity: {str(e)}")
            return 1.0

    def find_duplicates(self, code: str, min_lines: int = 3) -> Set[str]:
        """Detect duplicate code blocks"""
        if not code.strip() or len(code.splitlines()) < min_lines:
            return set()

        try:
            lines = code.split('\n')
            chunks = set()
            for i in range(len(lines) - min_lines + 1):
                chunk = '\n'.join(lines[i:i + min_lines])
                if chunk.strip() and len(chunk.strip().splitlines()) >= min_lines:
                    chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
                    chunks.add(chunk_hash)
            return chunks
        except Exception as e:
            log.warning(f"Error detecting duplicates: {str(e)}")
            return set()

    def calculate_documentation_score(self, code: str) -> float:
        """Calculate documentation coverage score"""
        if not code.strip() or len(code.splitlines()) < self.min_lines_for_analysis:
            return 1.0

        try:
            if not self.is_valid_python(code):
                return 0.5

            tree = ast.parse(code)
            total_funcs = 0
            documented_funcs = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    total_funcs += 1
                    if ast.get_docstring(node):
                        documented_funcs += 1
            
            return documented_funcs / total_funcs if total_funcs > 0 else 1.0
        except Exception as e:
            log.warning(f"Error calculating documentation score: {str(e)}")
            return 0.5

    def calculate_maintainability_index(self, code: str, complexity: float) -> float:
        """Calculate maintainability index"""
        if not code.strip():
            return 100.0

        try:
            operators = set(re.findall(r'[+\-*/=<>!&|^~]|\b(and|or|not|in|is)\b', code))
            operands = set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', code))
            
            halstead_volume = (len(operators) + len(operands)) * math.log2(len(operators) + len(operands)) if operators or operands else 1
            
            loc = len(code.split('\n'))
            if loc == 0:
                return 100.0

            try:
                mi = 171 - 5.2 * math.log(max(1, halstead_volume)) - 0.23 * complexity - 16.2 * math.log(max(1, loc))
                return max(0, min(100, mi))
            except ValueError:
                return 50.0
        except Exception as e:
            log.warning(f"Error calculating maintainability index: {str(e)}")
            return 50.0

DEFAULT_EXTENSIONS = [
    # Web/Frontend
    '.html', '.htm', '.css', '.scss', '.sass', '.less',
    '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte',
    
    # Backend/Server
    '.py', '.php', '.rb', '.java', '.go', '.rs', '.cs', '.vb',
    '.scala', '.kt', '.groovy', '.clj', '.coffee',
    
    # Systems Programming
    '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.m', '.mm',
    
    # Data/Config
    '.sql', '.json', '.xml', '.yaml', '.yml', '.toml',
    
    # Shell/Scripts
    '.sh', '.bash', '.ps1', '.bat', '.cmd',
    
    # Mobile
    '.swift', '.dart', '.kotlin'
]

COST_MODELS = {
    "basic": {
        "name": "Basic LOC Model",
        "description": "Simple cost estimation based on lines of code",
        "hourly_rate": 50,  # Default hourly rate in USD
        "loc_per_hour": 30,  # Average LOC per hour
    },
    "cocomo": {
        "name": "COCOMO II Model",
        "description": "Constructive Cost Model (COCOMO II)",
        "coefficients": {
            "organic": {"a": 2.4, "b": 1.05},      # Small, simple projects
            "semi_detached": {"a": 3.0, "b": 1.12}, # Medium complexity
            "embedded": {"a": 3.6, "b": 1.20}      # Complex projects
        },
    },
    "function_point": {
        "name": "Function Point Analysis",
        "description": "Estimation based on function points",
        "loc_per_fp": {
            # Core languages
            "py": 50,    # Python
            "js": 55,    # JavaScript
            "java": 60,  # Java
            "cpp": 65,   # C++
            "c": 70,     # C
            "cs": 55,    # C#
            
            # Web languages
            "php": 50,   # PHP
            "html": 40,  # HTML
            "css": 45,   # CSS
            "ts": 52,    # TypeScript
            "jsx": 53,   # JSX
            "tsx": 53,   # TSX
            
            # Other languages
            "rb": 50,    # Ruby
            "go": 60,    # Go
            "rs": 65,    # Rust
            "swift": 55, # Swift
            "dart": 50,  # Dart
            "sql": 40,   # SQL
            "kt": 55,    # Kotlin
            "scala": 55, # Scala
            "vb": 50,    # Visual Basic
        },
        "default_loc_per_fp": 55,
    }
}

def count_lines_in_file(file_path, include_blank=False, include_comments=True) -> Optional[CodeMetrics]:
    """Count lines in a single file with advanced metrics"""
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        log.error(f"File not found or not accessible: {file_path}")
        return None

    try:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            log.warning(f"Empty file: {file_path}")
            return CodeMetrics()

        if file_size > 10 * 1024 * 1024:
            log.warning(f"File too large to analyze: {file_path}")
            return None

        _, ext = os.path.splitext(file_path)
        analyzer = CodeAnalyzer()
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            try:
                content = file.read()
                lines = content.splitlines()
            except Exception as e:
                log.error(f"Error reading file {file_path}: {str(e)}")
                return None
            
            if not lines:
                return CodeMetrics()
                
            if not include_blank:
                lines = [line for line in lines if line.strip()]
                
            if not include_comments:
                try:
                    lines = filter_comments(lines, ext.lower())
                except Exception as e:
                    log.warning(f"Error filtering comments in {file_path}: {str(e)}")
            
            try:
                complexity = analyzer.calculate_complexity(content)
                duplicates = len(analyzer.find_duplicates(content))
                doc_score = analyzer.calculate_documentation_score(content)
                maint_index = analyzer.calculate_maintainability_index(content, complexity)
                
                return CodeMetrics(
                    lines=len(lines),
                    complexity=complexity,
                    duplicates=duplicates,
                    documentation_score=doc_score,
                    maintainability_index=maint_index
                )
            except Exception as e:
                log.error(f"Error calculating metrics for {file_path}: {str(e)}")
                return None
            
    except Exception as e:
        log.error(f"Unexpected error processing {file_path}: {str(e)}")
        return None

def filter_comments(lines: List[str], ext: str) -> List[str]:
    """Filter out comments based on file extension"""
    comment_patterns = {
        '.py': r'^\s*#',
        '.js': r'^\s*//',
        '.java': r'^\s*//',
        '.cpp': r'^\s*//',
        '.c': r'^\s*//',
        '.cs': r'^\s*//',
        '.php': r'^\s*(//|#)',
        '.rb': r'^\s*#',
        '.html': r'^\s*<!--',
        '.css': r'^\s*/\*',
        '.sql': r'^\s*--',
        '.ps1': r'^\s*(#|<#)',
        '.sh': r'^\s*#',
        '.vb': r'^\s*\'',
    }
    
    if ext not in comment_patterns:
        return lines
        
    pattern = re.compile(comment_patterns[ext])
    return [line for line in lines if not pattern.match(line)]

def enter_custom_path():
    """Allow user to enter or paste a custom path"""
    console.print(Panel.fit("[bold cyan]Directory Path Entry[/bold cyan]", 
                         box=box.ROUNDED))
    
    console.print("[yellow]Enter a directory path to analyze:[/yellow]")
    console.print("[dim]- Type a path manually[/dim]")
    console.print("[dim]- Paste a path from clipboard[/dim]")
    console.print("[dim]- Press Enter to use current directory[/dim]")
    
    path = Prompt.ask("Directory path", default=".")
    
    path = path.strip().strip('"\'')
    
    if not path:
        return "."
        
    return path

def count_lines_in_directory(directory, extensions, include_blank=False, 
                           include_comments=True, exclude_dirs=None):
    """Count lines in directory with advanced metrics and analysis"""
    if not os.path.exists(directory) or not os.path.isdir(directory):
        log.error(f"Directory not found or not accessible: {directory}")
        return None, {}

    try:
        exclude_dirs = set(os.path.abspath(d) for d in (exclude_dirs or []))
        
        files_to_process = []
        with Progress() as progress:
            scan_task = progress.add_task("[cyan]Scanning directory...", total=None)
            
            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) not in exclude_dirs]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    _, ext = os.path.splitext(file_path)
                    if ext.lower() in extensions:
                        files_to_process.append(file_path)
                        
                progress.update(scan_task, advance=1)
        
        if not files_to_process:
            log.warning(f"No matching files found in {directory}")
            return CodeMetrics(), {}
        
        results = {}
        total_metrics = CodeMetrics()
        processed_files = 0
        error_files = []
        
        with Progress() as progress:
            analyze_task = progress.add_task(
                "[cyan]Analyzing files...", 
                total=len(files_to_process)
            )
            
            for file_path in files_to_process:
                try:
                    _, ext = os.path.splitext(file_path)
                    metrics = count_lines_in_file(file_path, include_blank, include_comments)
                    
                    if metrics is None:
                        error_files.append(file_path)
                        continue
                    
                    if ext not in results:
                        results[ext] = {
                            "files": 0,
                            "metrics": CodeMetrics(),
                            "error_files": 0
                        }
                    
                    results[ext]["files"] += 1
                    results[ext]["metrics"] += metrics
                    total_metrics += metrics
                    processed_files += 1
                    
                except Exception as e:
                    log.error(f"Error processing file {file_path}: {str(e)}")
                    error_files.append(file_path)
                    results[ext]["error_files"] = results.get(ext, {}).get("error_files", 0) + 1
                
                finally:
                    progress.update(analyze_task, advance=1, 
                                  description=f"[cyan]Analyzing: {os.path.basename(file_path)}")
        
        if processed_files > 0:
            total_metrics.documentation_score /= processed_files
            total_metrics.maintainability_index /= processed_files
            
            for ext in results:
                if results[ext]["files"] > 0:
                    results[ext]["metrics"].documentation_score /= results[ext]["files"]
                    results[ext]["metrics"].maintainability_index /= results[ext]["files"]
        
        if error_files:
            log.warning(f"Failed to process {len(error_files)} files:")
            for file in error_files[:5]:
                log.warning(f"  - {file}")
            if len(error_files) > 5:
                log.warning(f"  ... and {len(error_files) - 5} more")
        
        return total_metrics, results
        
    except Exception as e:
        log.error(f"Error analyzing directory {directory}: {str(e)}")
        return None, {}

def display_results(directory: str, total_metrics: CodeMetrics, results: Dict):
    """Display formatted results with advanced metrics"""
    if total_metrics is None or not results:
        console.print("[red]No results to display.[/red]")
        return
    
    try:
        console.print()
        console.print(Panel.fit(
            f"[bold green]Advanced Code Analysis Results for:[/bold green] [yellow]{directory}[/yellow]",
            box=box.ROUNDED
        ))
        
        table = Table(show_header=True, header_style="bold blue", box=box.SIMPLE_HEAD)
        table.add_column("File Type", style="cyan")
        table.add_column("Files", justify="right")
        table.add_column("Lines", justify="right")
        table.add_column("Complexity", justify="right")
        table.add_column("Duplicates", justify="right")
        table.add_column("Doc Score", justify="right")
        table.add_column("Maint. Index", justify="right")
        table.add_column("Errors", justify="right", style="red")
        
        for ext, data in sorted(results.items()):
            try:
                metrics = data["metrics"]
                maint_color = get_metric_color(metrics.maintainability_index, [70, 50])
                doc_color = get_metric_color(metrics.documentation_score * 100, [70, 40])
                
                table.add_row(
                    ext,
                    str(data["files"]),
                    str(metrics.lines),
                    f"{metrics.complexity:.1f}",
                    str(metrics.duplicates),
                    f"{doc_color}{metrics.documentation_score:.2%}[/]",
                    f"{maint_color}{metrics.maintainability_index:.1f}[/]",
                    str(data.get("error_files", 0))
                )
            except Exception as e:
                log.error(f"Error displaying results for {ext}: {str(e)}")
                continue
        
        try:
            total_files = sum(data["files"] for data in results.values())
            total_errors = sum(data.get("error_files", 0) for data in results.values())
            
            table.add_row(
                "[bold]Total[/bold]",
                str(total_files),
                str(total_metrics.lines),
                f"{total_metrics.complexity:.1f}",
                str(total_metrics.duplicates),
                f"{total_metrics.documentation_score:.2%}",
                f"{total_metrics.maintainability_index:.1f}",
                str(total_errors),
                style="bold"
            )
        except Exception as e:
            log.error(f"Error displaying totals: {str(e)}")
        
        console.print(table)
        
        try:
            quality_panel = Panel(
                Columns([
                    "[cyan]Code Quality Metrics:[/cyan]\n" +
                    f"• Overall Maintainability: {get_quality_rating(total_metrics.maintainability_index)}\n" +
                    f"• Documentation Coverage: {get_quality_rating(total_metrics.documentation_score * 100)}\n" +
                    f"• Average Complexity: {get_complexity_rating(total_metrics.complexity)}",
                    
                    "[cyan]Recommendations:[/cyan]\n" +
                    generate_recommendations(total_metrics)
                ], padding=(0, 2)),
                title="[bold]Quality Analysis[/bold]",
                box=box.ROUNDED
            )
            
            console.print()
            console.print(quality_panel)
            
        except Exception as e:
            log.error(f"Error displaying quality summary: {str(e)}")
            
    except Exception as e:
        log.error(f"Error displaying results: {str(e)}")

def get_quality_rating(score: float) -> str:
    """Convert numerical score to qualitative rating with color"""
    if score >= 80:
        return f"[green]Excellent ({score:.1f})[/green]"
    elif score >= 60:
        return f"[blue]Good ({score:.1f})[/blue]"
    elif score >= 40:
        return f"[yellow]Fair ({score:.1f})[/yellow]"
    else:
        return f"[red]Needs Improvement ({score:.1f})[/red]"

def get_complexity_rating(complexity: float) -> str:
    """Convert complexity score to qualitative rating with color"""
    if complexity <= 5:
        return f"[green]Simple ({complexity:.1f})[/green]"
    elif complexity <= 10:
        return f"[blue]Moderate ({complexity:.1f})[/blue]"
    elif complexity <= 20:
        return f"[yellow]Complex ({complexity:.1f})[/yellow]"
    else:
        return f"[red]Very Complex ({complexity:.1f})[/red]"

def generate_recommendations(metrics: CodeMetrics) -> str:
    """Generate improvement recommendations based on metrics"""
    recommendations = []
    
    if metrics.maintainability_index < 65:
        recommendations.append("• [yellow]Consider refactoring complex modules[/yellow]")
    if metrics.documentation_score < 0.6:
        recommendations.append("• [yellow]Improve documentation coverage[/yellow]")
    if metrics.complexity > 15:
        recommendations.append("• [yellow]Break down complex functions[/yellow]")
    if metrics.duplicates > 10:
        recommendations.append("• [yellow]Address code duplication[/yellow]")
    
    if not recommendations:
        recommendations.append("• [green]Code base is in good health![/green]")
    
    return "\n".join(recommendations)

def calculate_basic_cost(total_loc: int, hourly_rate: Optional[float] = None) -> float:
    """Calculate basic cost based on LOC"""
    try:
        model = COST_MODELS["basic"]
        rate = hourly_rate or model["hourly_rate"]
        
        if total_loc < 0:
            log.warning("Negative LOC count provided, using absolute value")
            total_loc = abs(total_loc)
        
        hours = total_loc / max(1, model["loc_per_hour"])
        cost = hours * rate
        
        return max(0, cost)
    except Exception as e:
        log.error(f"Error calculating basic cost: {str(e)}")
        return 0.0

def calculate_cocomo_cost(total_loc: int, project_type: str = "semi_detached", 
                         hourly_rate: Optional[float] = None) -> float:
    """Calculate cost using COCOMO II model"""
    try:
        model = COST_MODELS["cocomo"]
        rate = hourly_rate or COST_MODELS["basic"]["hourly_rate"]
        
        if total_loc < 0:
            log.warning("Negative LOC count provided, using absolute value")
            total_loc = abs(total_loc)
        
        if project_type not in model["coefficients"]:
            log.warning(f"Invalid project type '{project_type}', using 'semi_detached'")
            project_type = "semi_detached"
        
        coeffs = model["coefficients"][project_type]
        
        effort_pm = coeffs["a"] * (total_loc / 1000) ** coeffs["b"]
        
        hours = effort_pm * 152
        
        cost = hours * rate
        
        return max(0, cost)
    except Exception as e:
        log.error(f"Error calculating COCOMO cost: {str(e)}")
        return 0.0

def calculate_function_point_cost(results: Dict, hourly_rate: Optional[float] = None) -> float:
    """Calculate cost based on function points"""
    try:
        hourly_rate = hourly_rate or COST_MODELS["basic"]["hourly_rate"]
        total_cost = 0.0
        
        for ext, data in results.items():
            try:
                ext_clean = ext.lstrip('.').lower()
                loc_per_fp = COST_MODELS["function_point"]["loc_per_fp"].get(
                    ext_clean, 
                    COST_MODELS["function_point"]["default_loc_per_fp"]
                )
                
                fps = max(0, data["metrics"].lines) / max(1, loc_per_fp)
                
                type_cost = fps * hourly_rate
                total_cost += type_cost
                
            except Exception as e:
                log.warning(f"Error calculating function points for {ext}: {str(e)}")
                continue
        
        return max(0, total_cost)
    except Exception as e:
        log.error(f"Error calculating function point cost: {str(e)}")
        return 0.0

def display_cost_estimates(total_lines: int, results: Dict, hourly_rate: Optional[float] = None):
    """Display cost estimates using different models"""
    try:
        console.print()
        console.print(Panel.fit("[bold blue]Cost Estimation Analysis[/bold blue]", 
                              box=box.ROUNDED))
        
        if total_lines <= 0:
            console.print("[yellow]Warning: No lines of code to estimate cost for.[/yellow]")
            return
        
        basic_cost = calculate_basic_cost(total_lines, hourly_rate)
        cocomo_costs = {
            "Simple": calculate_cocomo_cost(total_lines, "organic", hourly_rate),
            "Medium": calculate_cocomo_cost(total_lines, "semi_detached", hourly_rate),
            "Complex": calculate_cocomo_cost(total_lines, "embedded", hourly_rate)
        }
        fp_cost = calculate_function_point_cost(results, hourly_rate)
        
        table = Table(show_header=True, header_style="bold blue", box=box.SIMPLE_HEAD)
        table.add_column("Model", style="cyan")
        table.add_column("Estimated Cost (USD)", justify="right")
        table.add_column("Notes", style="dim")
        
        table.add_row(
            "Basic LOC",
            f"${basic_cost:,.2f}",
            "Simple calculation based on LOC"
        )
        
        for complexity, cost in cocomo_costs.items():
            table.add_row(
                f"COCOMO II ({complexity})",
                f"${cost:,.2f}",
                f"For {complexity.lower()} complexity projects"
            )
        
        table.add_row(
            "Function Point",
            f"${fp_cost:,.2f}",
            "Based on functional complexity"
        )
        
        console.print(table)
        
        all_costs = [cost for cost in [basic_cost] + list(cocomo_costs.values()) + [fp_cost] if cost > 0]
        
        if all_costs:
            avg_cost = sum(all_costs) / len(all_costs)
            min_cost = min(all_costs)
            max_cost = max(all_costs)
            
            console.print()
            console.print(Panel(
                f"[cyan]Average Estimated Cost:[/cyan] [bold green]${avg_cost:,.2f}[/bold green]\n" +
                f"[cyan]Cost Range:[/cyan] [green]${min_cost:,.2f}[/green] - [green]${max_cost:,.2f}[/green]",
                title="[bold]Summary[/bold]",
                box=box.ROUNDED
            ))
        else:
            console.print("[yellow]Warning: Unable to calculate cost estimates.[/yellow]")
            
    except Exception as e:
        log.error(f"Error displaying cost estimates: {str(e)}")

def select_cost_model() -> float:
    """Interactive cost model configuration"""
    try:
        console.print(Panel.fit(
            "[bold yellow]Cost Estimation Configuration[/bold yellow]",
            box=box.ROUNDED
        ))
        
        while True:
            try:
                hourly_rate = float(Prompt.ask(
                    "Enter hourly rate in USD",
                    default=str(COST_MODELS["basic"]["hourly_rate"])
                ))
                
                if hourly_rate <= 0:
                    console.print("[red]Hourly rate must be positive.[/red]")
                    continue
                    
                return hourly_rate
            except ValueError:
                console.print("[red]Please enter a valid number.[/red]")
                
    except Exception as e:
        log.error(f"Error in cost model selection: {str(e)}")
        return COST_MODELS["basic"]["hourly_rate"]

def get_metric_color(value: float, thresholds: List[float]) -> str:
    """Get color for metric based on thresholds"""
    if value >= thresholds[0]:
        return "[green]"
    elif value >= thresholds[1]:
        return "[yellow]"
    return "[red]"

def main():
    try:
        console.print(Panel.fit(
            "[bold cyan]Advanced Lines of Code Counter & Cost Estimator[/bold cyan]\n"
            "[dim]A beautiful CLI tool for analyzing your codebase and estimating costs[/dim]",
            box=box.ROUNDED
        ))
        
        parser = argparse.ArgumentParser(
            description="Count lines of code and estimate software costs",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument("-d", "--directory", help="Directory to analyze (or use interactive path entry)")
        parser.add_argument("-e", "--extensions", nargs="+", help="File extensions to include (default: common code files)")
        parser.add_argument("-a", "--all", action="store_true", help="Include blank lines")
        parser.add_argument("-c", "--no-comments", action="store_true", help="Exclude comment lines")
        parser.add_argument("-x", "--exclude", nargs="+", help="Directories to exclude")
        parser.add_argument("-r", "--rate", type=float, help="Hourly rate in USD for cost estimation")
        parser.add_argument("--no-cost", action="store_true", help="Skip cost estimation")
        
        try:
            args = parser.parse_args()
        except Exception as e:
            log.error(f"Error parsing arguments: {str(e)}")
            return
        
        try:
            directory = args.directory if args.directory else enter_custom_path()
            directory = os.path.abspath(directory)
        except Exception as e:
            log.error(f"Error getting directory path: {str(e)}")
            return
        
        try:
            if args.extensions:
                extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions]
            else:
                extensions = DEFAULT_EXTENSIONS
        except Exception as e:
            log.error(f"Error processing extensions: {str(e)}")
            return
            
        exclude_dirs = args.exclude or []
        
        include_blank = args.all
        include_comments = not args.no_comments
        
        hourly_rate = args.rate
        
        if os.path.isdir(directory):
            try:
                console.print(f"[yellow]Analyzing directory:[/yellow] {directory}")
                console.print(f"[yellow]File types:[/yellow] {', '.join(extensions)}")
                
                total_metrics, results = count_lines_in_directory(
                    directory, 
                    extensions, 
                    include_blank,
                    include_comments,
                    exclude_dirs
                )
                
                if total_metrics is None:
                    log.error("Analysis failed")
                    return
                
                display_results(directory, total_metrics, results)
                
                # Perform cost estimation if not disabled
                if not args.no_cost:
                    # If hourly rate not provided and interactive mode
                    if hourly_rate is None and not args.directory:
                        try:
                            hourly_rate = select_cost_model()
                        except Exception as e:
                            log.error(f"Error selecting cost model: {str(e)}")
                            return
                            
                    display_cost_estimates(total_metrics.lines, results, hourly_rate)
                    
            except Exception as e:
                log.error(f"Error during analysis: {str(e)}")
        else:
            log.error(f"The directory '{directory}' does not exist.")
            
    except Exception as e:
        log.error(f"Unexpected error: {str(e)}")
        if log.getEffectiveLevel() <= logging.DEBUG:
            import traceback
            log.debug(traceback.format_exc())

if __name__ == "__main__":
    main()
