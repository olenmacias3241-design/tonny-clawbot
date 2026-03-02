"""Command-line interface client for Claw Bot AI."""

import asyncio
import httpx
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown

console = Console()


async def chat_session():
    """Interactive chat session with Claw Bot."""
    base_url = "http://localhost:8000"
    conversation_id = None

    console.print("[bold green]Claw Bot AI - Interactive Chat[/bold green]")
    console.print("Type 'exit' or 'quit' to end the conversation\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("[bold blue]You[/bold blue]")

                # Check for exit commands
                if user_input.lower() in ["exit", "quit", "bye"]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                if not user_input.strip():
                    continue

                # Send message to bot
                response = await client.post(
                    f"{base_url}/chat",
                    json={
                        "message": user_input,
                        "conversation_id": conversation_id,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    conversation_id = data["conversation_id"]

                    # Display bot response
                    console.print("\n[bold green]Bot[/bold green]:")
                    console.print(Markdown(data["message"]))
                    console.print()
                else:
                    console.print(f"[red]Error: {response.status_code}[/red]")

            except httpx.ConnectError:
                console.print(
                    "[red]Error: Cannot connect to Claw Bot server. "
                    "Make sure the server is running on http://localhost:8000[/red]"
                )
                break
            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")


def main():
    """Main entry point for CLI client."""
    asyncio.run(chat_session())


if __name__ == "__main__":
    main()
