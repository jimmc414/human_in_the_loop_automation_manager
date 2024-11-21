from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown
from rich import box
from typing import List, Dict, Optional, Literal
import time
import datetime
import json
from pathlib import Path
import msvcrt
import signal

class AutomationUI:
    def __init__(self):
        """Initialize the AutomationUI with basic setup"""
        self.console = Console()
        self.current_step = 0
        self.session_logs = []
        self.session_start_time = datetime.datetime.now()
        self.is_running = True
        self.step_history = []  # Track step execution history
        self.setup_signal_handlers()
        self.log_event("Session started")
        
    def log_event(self, event: str, details: dict = None):
        """Log an event with timestamp and optional details"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event": event,
            "step": self.current_step + 1,
            "details": details or {}
        }
        self.session_logs.append(log_entry)
    
    def setup_signal_handlers(self):
        """Setup handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)
    
    def handle_interrupt(self, signum, frame):
        """Handle interrupt signals gracefully"""
        self.is_running = False
        self.print_message("\nGracefully shutting down...", "warning")
        self.cleanup()
    
    def show_keyboard_shortcuts(self):
        """Display available keyboard shortcuts"""
        shortcuts_panel = Panel(
            "\n".join([
                "[bold cyan]Available Commands:[/]",
                "",
                "[yellow]Enter[/] Next step / Proceed",
                "[yellow]h[/] Show help",
                "[yellow]q[/] Quit",
                "[yellow]l[/] Export logs",
                "[yellow]r[/] Retry current step",
                "[yellow]s[/] Show summary"
            ]),
            title="[bold]Command Guide[/]",
            border_style="blue"
        )
        self.console.print(shortcuts_panel)
    
    def check_keyboard_input(self) -> Optional[str]:
        """Check for keyboard input without blocking (Windows-compatible)"""
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            actions = {
                '\r': "proceed",  # Enter key
                'h': "help",
                'q': "exit",
                'l': "logs",
                'r': "retry",
                's': "summary"
            }
            return actions.get(key)
        return None
    
    def print_message(self, message: str, level: Literal["success", "error", "warning", "info"] = "info"):
        """Print a message with appropriate color coding based on level"""
        styles = {
            "success": "[bold green]✓[/] [green]{}[/]",
            "error": "[bold red]✗[/] [red]{}[/]",
            "warning": "[bold yellow]![/] [yellow]{}[/]",
            "info": "[bold blue]i[/] [blue]{}[/]"
        }
        formatted_message = styles.get(level, "{}").format(message)
        self.console.print(formatted_message)
        self.log_event(f"Message displayed", {"message": message, "level": level})

    def cleanup(self):
        """Perform cleanup operations before exit"""
        if self.session_logs:
            if Confirm.ask("[cyan]Would you like to save the session logs before exiting?"):
                self.show_export_options()
        self.print_message("Cleanup completed", "info")

    def show_export_options(self):
        """Display and handle log export options"""
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Format", style="cyan")
        table.add_column("Description", style="dim")
        
        table.add_row("📄 text", "Human-readable text format")
        table.add_row("🔧 json", "Machine-readable JSON format")
        
        self.console.print(table)
        format_choice = Prompt.ask(
            "[bold cyan]Choose export format",
            choices=["text", "json"],
            default="text"
        )
        self.export_logs(format_choice)

    def export_logs(self, format: str = "text") -> bool:
        """Export session logs to a file in the specified format"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            if format == "text":
                filename = f"automation_logs_{timestamp}.txt"
                content = self._format_logs_as_text()
            else:  # json format
                filename = f"automation_logs_{timestamp}.json"
                content = self._format_logs_as_json()
                
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_path = log_dir / filename
            
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.print_message(f"Logs exported successfully to {log_path}", "success")
            self.log_event("Logs exported", {"filename": str(log_path)})
            return True
            
        except Exception as e:
            self.print_message(f"Error exporting logs: {str(e)}", "error")
            self.log_event("Log export failed", {"error": str(e)})
            return False

    def _format_logs_as_text(self) -> str:
        """Format logs as human-readable text"""
        lines = [f"Automation Session Log - Started at {self.session_start_time}"]
        lines.append("=" * 80)
        
        for entry in self.session_logs:
            timestamp = datetime.datetime.fromisoformat(entry["timestamp"])
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"\n[{formatted_time}] Step {entry['step']}: {entry['event']}")
            if entry["details"]:
                for key, value in entry["details"].items():
                    lines.append(f"  {key}: {value}")
                    
        return "\n".join(lines)

    def _format_logs_as_json(self) -> str:
        """Format logs as JSON"""
        log_data = {
            "session_start": self.session_start_time.isoformat(),
            "logs": self.session_logs
        }
        return json.dumps(log_data, indent=2)

    def display_header(self):
        """Display an attractive header for the automation tool"""
        header = Panel(
            "[bold blue]🤖 Interactive Automation Assistant[/]\n"
            "[dim]Human-in-the-loop process automation[/]",
            box=box.DOUBLE,
            style="bold white on blue",
            padding=(1, 2)
        )
        self.console.print(header)
        self.log_event("Header displayed")

    def create_step_panel(self, step: Dict) -> Panel:
        """Create a visually appealing panel for the current step"""
        content = f"""[bold]{step['title']}[/]
        
[dim]Description:[/] {step['description']}

[yellow]Current Status:[/] {step['status']}
[dim]─────────────────────────────────[/]
"""
        return Panel(
            content,
            title=f"[bold cyan]Step {self.current_step + 1}[/]",
            border_style="cyan",
            padding=(1, 2)
        )

    def display_progress(self, description: str):
        """Show an animated progress indicator with status"""
        self.log_event("Progress started", {"description": description})
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description, total=None)
            # Simulation of process running
            time.sleep(2)
        self.log_event("Progress completed", {"description": description})

    def display_help(self, step: Dict):
        """Show contextual help in an informative panel"""
        self.log_event("Help displayed", {"step_title": step['title']})
        help_content = f"""
# Help for Step {self.current_step + 1}: {step['title']}

{step['help_text']}

## Common Issues:
{step['common_issues']}
        """
        help_panel = Panel(
            Markdown(help_content),
            title="[bold blue]Help & Troubleshooting[/]",
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(help_panel)

    def show_action_menu(self) -> str:
        """Display an intuitive action menu for the current step"""
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Action", style="cyan")
        table.add_column("Description", style="dim")
        
        actions = [
            ("▶️ [green]proceed", "Continue to next step (Enter)"),
            ("🔄 [yellow]retry", "Retry current step (r)"),
            ("❓ [blue]help", "Get help with current step (h)"),
            ("📝 [magenta]logs", "Export session logs (l)"),
            ("❌ [bold red]exit", "Exit automation (q)")
        ]
        
        for action, desc in actions:
            table.add_row(action, desc)
            
        self.console.print(table)
        
        # Wait for valid input
        while True:
            action = self.check_keyboard_input()
            if action:
                self.log_event("Action selected", {"action": action})
                return action
            time.sleep(0.1)  # Small delay to prevent CPU spinning

    def run_step(self, step: Dict) -> bool:
        """Execute a single step of the automation with user interaction"""
        self.console.clear()
        self.display_header()
        
        self.log_event("Step started", {
            "step_title": step['title'],
            "step_status": step['status']
        })
        
        # Show step information
        self.console.print(self.create_step_panel(step))
        
        # Show progress animation
        self.display_progress(f"Running {step['title']}...")
        
        while True:
            action = self.show_action_menu()
            
            if action == "proceed":
                self.print_message(f"Step '{step['title']}' completed", "success")
                self.log_event("Step completed", {"step_title": step['title']})
                return True
            elif action == "retry":
                self.print_message("Retrying step...", "warning")
                self.log_event("Step retry", {"step_title": step['title']})
                self.display_progress("Retrying operation...")
            elif action == "help":
                self.display_help(step)
            elif action == "logs":
                self.show_export_options()
            elif action == "exit":
                if Confirm.ask("[bold red]Are you sure you want to exit?"):
                    self.print_message("Session terminated by user", "warning")
                    self.log_event("Session terminated by user")
                    return False

    def run_automation(self, steps: List[Dict]):
        """Main loop for running the automation process"""
        try:
            self.show_keyboard_shortcuts()  # Show available shortcuts at start
            time.sleep(2)  # Give user time to read shortcuts
            
            while self.current_step < len(steps) and self.is_running:
                step = steps[self.current_step]
                if self.run_step(step):
                    self.current_step += 1
                else:
                    break
                    
            if self.current_step >= len(steps):
                self.log_event("Automation completed", {
                    "total_steps": len(steps)
                })
                self.print_message("🎉 Automation completed successfully!", "success")
                self.console.print(Panel(
                    f"[dim]Total steps completed: {len(steps)}[/]",
                    style="bold white on green",
                    padding=(1, 2)
                ))
                
                if Confirm.ask("[cyan]Would you like to export the session logs?"):
                    self.show_export_options()
                
        except Exception as e:
            self.print_message(f"Unexpected error: {str(e)}", "error")
            self.log_event("Error occurred", {"error": str(e)})
        finally:
            self.cleanup()


# Example usage:
if __name__ == "__main__":
    # Example automation steps
    steps = [
        {
            "title": "Initialize System Configuration",
            "description": "Setting up necessary configurations and checking prerequisites",
            "status": "Ready to start",
            "status_level": "info",
            "help_text": "This step verifies your system meets all requirements",
            "common_issues": "- Missing dependencies\n- Insufficient permissions"
        },
        {
            "title": "Data Preparation",
            "description": "Preparing and validating input data",
            "status": "Waiting for previous step",
            "status_level": "pending",
            "help_text": "Ensures all required data is present and correctly formatted",
            "common_issues": "- Invalid file format\n- Missing required fields"
        }
    ]
    
    ui = AutomationUI()
    ui.run_automation(steps)