"""Tests for the core module."""

import pytest

from jarbas.core import TaskManager, greet


def test_greet() -> None:
    """Test the greet function."""
    assert greet("World") == "Hello, World! Welcome to Jarbas."
    assert greet("User") == "Hello, User! Welcome to Jarbas."


class TestTaskManager:
    """Tests for the TaskManager class."""

    def test_add_task(self) -> None:
        """Test adding tasks."""
        manager = TaskManager()
        task_id = manager.add_task("Test task")
        assert task_id == 1
        assert len(manager.tasks) == 1
        assert manager.tasks[1]["description"] == "Test task"
        assert manager.tasks[1]["completed"] is False

    def test_complete_task(self) -> None:
        """Test completing tasks."""
        manager = TaskManager()
        task_id = manager.add_task("Test task")
        
        # Test completing an existing task
        result = manager.complete_task(task_id)
        assert result is True
        assert manager.tasks[task_id]["completed"] is True
        
        # Test completing a non-existent task
        result = manager.complete_task(999)
        assert result is False

    def test_get_tasks(self) -> None:
        """Test getting tasks with various filters."""
        manager = TaskManager()
        manager.add_task("Task 1")
        manager.add_task("Task 2")
        task3_id = manager.add_task("Task 3")
        manager.complete_task(task3_id)
        
        # Get all tasks
        all_tasks = manager.get_tasks()
        assert len(all_tasks) == 3
        
        # Get only completed tasks
        completed_tasks = manager.get_tasks(completed=True)
        assert len(completed_tasks) == 1
        assert completed_tasks[0]["description"] == "Task 3"
        
        # Get only incomplete tasks
        incomplete_tasks = manager.get_tasks(completed=False)
        assert len(incomplete_tasks) == 2
        descriptions = [task["description"] for task in incomplete_tasks]
        assert "Task 1" in descriptions
        assert "Task 2" in descriptions 