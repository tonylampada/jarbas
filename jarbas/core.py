"""Core functionality for the Jarbas project."""

from typing import Dict, List, Optional, Union


def greet(name: str) -> str:
    """Return a greeting message.
    
    Args:
        name: The name to greet
        
    Returns:
        A greeting message
    """
    return f"Hello, {name}! Welcome to Jarbas."


class TaskManager:
    """A simple task manager."""
    
    def __init__(self) -> None:
        """Initialize an empty task manager."""
        self.tasks: Dict[int, Dict[str, Union[str, bool]]] = {}
        self._next_id: int = 1
        
    def add_task(self, description: str) -> int:
        """Add a new task.
        
        Args:
            description: The task description
            
        Returns:
            The ID of the new task
        """
        task_id = self._next_id
        self.tasks[task_id] = {
            "description": description,
            "completed": False
        }
        self._next_id += 1
        return task_id
        
    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed.
        
        Args:
            task_id: The ID of the task to complete
            
        Returns:
            True if the task was found and completed, False otherwise
        """
        if task_id in self.tasks:
            self.tasks[task_id]["completed"] = True
            return True
        return False
        
    def get_tasks(self, completed: Optional[bool] = None) -> List[Dict[str, Union[int, str, bool]]]:
        """Get all tasks, optionally filtered by completion status.
        
        Args:
            completed: If provided, filter tasks by completion status
            
        Returns:
            A list of tasks with their IDs
        """
        result = []
        for task_id, task in self.tasks.items():
            if completed is None or task["completed"] == completed:
                task_with_id = {"id": task_id, **task}
                result.append(task_with_id)
        return result 