"""Command-line interface for Jarbas."""

import argparse
import sys
from typing import List, Optional

from jarbas.core import TaskManager, greet


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Jarbas Task Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Greet command
    greet_parser = subparsers.add_parser("greet", help="Greet the user")
    greet_parser.add_argument("name", help="Name to greet")
    
    # Task management commands
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("description", help="Task description")
    
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument(
        "--status", 
        choices=["all", "completed", "pending"], 
        default="all",
        help="Filter tasks by status"
    )
    
    complete_parser = subparsers.add_parser("complete", help="Mark a task as completed")
    complete_parser.add_argument("task_id", type=int, help="ID of the task to complete")
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Run the CLI application.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code
    """
    parsed_args = parse_args(args)
    
    if parsed_args.command == "greet":
        print(greet(parsed_args.name))
        return 0
        
    # Initialize task manager
    manager = TaskManager()
    
    if parsed_args.command == "add":
        task_id = manager.add_task(parsed_args.description)
        print(f"Task added with ID: {task_id}")
        return 0
        
    elif parsed_args.command == "list":
        completed = None
        if parsed_args.status == "completed":
            completed = True
        elif parsed_args.status == "pending":
            completed = False
            
        tasks = manager.get_tasks(completed=completed)
        
        if not tasks:
            print("No tasks found.")
            return 0
            
        print("Tasks:")
        for task in tasks:
            status = "✓" if task["completed"] else "☐"
            print(f"{task['id']}: [{status}] {task['description']}")
        return 0
        
    elif parsed_args.command == "complete":
        success = manager.complete_task(parsed_args.task_id)
        if success:
            print(f"Task {parsed_args.task_id} marked as completed.")
        else:
            print(f"Task {parsed_args.task_id} not found.")
            return 1
        return 0
        
    else:
        print("Please specify a command. Use --help for more information.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 