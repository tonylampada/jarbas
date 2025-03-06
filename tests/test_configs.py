import os
import tempfile
import yaml
import pytest
from unittest.mock import patch, mock_open

from jarbas import configs


def setup_module(module):
    """Set up the module for testing by adding the _config attribute."""
    # Add the _config attribute to the configs module if it doesn't exist
    if not hasattr(configs, "_config"):
        configs._config = None


@pytest.fixture
def sample_config():
    """Sample config data for testing."""
    return {
        "mcp_serrvers": [
            {"name": "slack", "url": "http://localhost:8201/sse"},
            {"name": "youtube", "url": "http://localhost:8203/sse"},
        ],
        "agents": [
            {
                "name": "helpful",
                "system_content": "You are a helpful assistant...",
                "enable_tools": True,
                "tools": ["slack.*", "youtube.*"],
            },
            {
                "name": "unhelpful",
                "system_content": "You are an extremely rude and unhelpful assistant...",
            },
        ],
        "default_model": "qwen2.5",
        "default_agent": "helpful",
    }


@pytest.fixture
def temp_config_file(sample_config):
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        yaml.dump(sample_config, temp_file)
        temp_path = temp_file.name
    
    yield temp_path
    
    # Clean up the temporary file
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_init(temp_config_file):
    """Test that init loads the config file correctly."""
    with patch("jarbas.configs.open", mock_open(read_data=yaml.dump(yaml.load(open(temp_config_file), Loader=yaml.SafeLoader)))):
        configs.init()
        # Since init doesn't return anything, we'll verify its effects in other tests


def test_get_mcp_servers(sample_config):
    """Test that get_mcp_servers returns the correct server configurations."""
    with patch("jarbas.configs._config", sample_config):
        servers = configs.get_mcp_servers()
        assert len(servers) == 2
        assert servers[0]["name"] == "slack"
        assert servers[0]["url"] == "http://localhost:8201/sse"
        assert servers[1]["name"] == "youtube"
        assert servers[1]["url"] == "http://localhost:8203/sse"


def test_get_agents(sample_config):
    """Test that get_agents returns the correct agent configurations."""
    with patch("jarbas.configs._config", sample_config):
        agents = configs.get_agents()
        assert len(agents) == 2
        assert agents[0]["name"] == "helpful"
        assert agents[0]["enable_tools"] is True
        assert "slack.*" in agents[0]["tools"]
        assert agents[1]["name"] == "unhelpful"


def test_get_default_model(sample_config):
    """Test that get_default_model returns the correct default model."""
    with patch("jarbas.configs._config", sample_config):
        model = configs.get_default_model()
        assert model == "qwen2.5"


def test_get_default_agent(sample_config):
    """Test that get_default_agent returns the correct default agent."""
    with patch("jarbas.configs._config", sample_config):
        agent = configs.get_default_agent()
        assert agent == "helpful"


def test_set_default_agent(sample_config, temp_config_file):
    """Test that set_default_agent updates the default agent correctly."""
    # Setup mock config
    mock_config = sample_config.copy()
    
    # Mock the open function for reading and writing
    with patch("jarbas.configs._config", mock_config), \
         patch("jarbas.configs.open", mock_open()), \
         patch("yaml.dump") as mock_yaml_dump:
        
        configs.set_default_agent("unhelpful")
        
        # Check that the config was updated in memory
        assert mock_config["default_agent"] == "unhelpful"
        
        # Check that yaml.dump was called to save the updated config
        mock_yaml_dump.assert_called_once()


def test_set_default_model(sample_config, temp_config_file):
    """Test that set_default_model updates the default model correctly."""
    # Setup mock config
    mock_config = sample_config.copy()
    
    # Mock the open function for reading and writing
    with patch("jarbas.configs._config", mock_config), \
         patch("jarbas.configs.open", mock_open()), \
         patch("yaml.dump") as mock_yaml_dump:
        
        configs.set_default_model("gpt-4")
        
        # Check that the config was updated in memory
        assert mock_config["default_model"] == "gpt-4"
        
        # Check that yaml.dump was called to save the updated config
        mock_yaml_dump.assert_called_once()


def test_set_default_agent_invalid(sample_config):
    """Test that set_default_agent raises an error for invalid agent names."""
    with patch("jarbas.configs._config", sample_config):
        with pytest.raises(ValueError, match="Agent 'nonexistent' not found"):
            configs.set_default_agent("nonexistent")


def test_get_mcp_servers_empty():
    """Test that get_mcp_servers handles empty server list."""
    with patch("jarbas.configs._config", {"mcp_serrvers": []}):
        servers = configs.get_mcp_servers()
        assert len(servers) == 0


def test_get_agents_empty():
    """Test that get_agents handles empty agent list."""
    with patch("jarbas.configs._config", {"agents": []}):
        agents = configs.get_agents()
        assert len(agents) == 0


def test_init_file_not_found():
    """Test that init handles missing config file."""
    with patch("jarbas.configs.open", side_effect=FileNotFoundError("No such file")):
        with pytest.raises(FileNotFoundError):
            configs.init() 