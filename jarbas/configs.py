import os
import yaml
from typing import List, Dict, Any, Optional

_config = None
_config_file_path = "config.yaml"


def init(config_path: str = _config_file_path) -> None:
    global _config
    
    try:
        with open(config_path, "r") as file:
            _config = yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")


def get_mcp_servers() -> List[Dict[str, str]]:
    if _config is None or "mcp_serrvers" not in _config:
        return []
    
    return _config["mcp_serrvers"]


def get_agents() -> List[Dict[str, Any]]:
    if _config is None or "agents" not in _config:
        return []
    
    return _config["agents"]


def get_default_model() -> Optional[str]:
    if _config is None or "default_model" not in _config:
        return None
    
    return _config["default_model"]


def get_default_agent() -> Optional[str]:
    if _config is None or "default_agent" not in _config:
        return None
    
    return _config["default_agent"]


def set_default_agent(agent_name: str) -> None:
    if _config is None:
        init()
    
    agents = get_agents()
    agent_names = [agent["name"] for agent in agents]
    
    if agent_name not in agent_names:
        raise ValueError(f"Agent '{agent_name}' not found")
    
    _config["default_agent"] = agent_name
    
    _save_config()


def set_default_model(model_name: str) -> None:
    if _config is None:
        init()
    
    _config["default_model"] = model_name
    
    _save_config()


def _save_config(config_path: str = _config_file_path) -> None:
    with open(config_path, "w") as file:
        yaml.dump(_config, file, default_flow_style=False) 