from pathlib import Path

from voxcat.personas import load_personas


def test_loads_from_files(tmp_path):
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()
    (personas_dir / "test-persona.md").write_text(
        '---\nlabel: "Test"\ndescription: "A test persona."\n'
        "tools:\n  builtin: [file_read]\n  mcp_servers: []\n"
        "output:\n  directory: output/test\n---\n\nYou are a test persona."
    )
    profiles = load_personas(personas_dir, {"persona": {"profiles": {}}})
    assert "test-persona" in profiles
    assert profiles["test-persona"]["label"] == "Test"
    assert profiles["test-persona"]["instruction"] == "You are a test persona."


def test_falls_back_to_config(tmp_path):
    config = {
        "persona": {
            "profiles": {
                "from-config": {
                    "instruction": "Config persona.",
                    "tools": {"builtin": [], "mcp_servers": []},
                }
            }
        }
    }
    profiles = load_personas(tmp_path / "nonexistent", config)
    assert "from-config" in profiles


def test_file_overrides_config(tmp_path):
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()
    (personas_dir / "shared.md").write_text(
        '---\nlabel: "From File"\ntools:\n  builtin: []\n  mcp_servers: []\n'
        "output:\n  directory: output/shared\n---\n\nFile instruction."
    )
    config = {
        "persona": {
            "profiles": {
                "shared": {"instruction": "Config instruction.", "label": "From Config"},
            }
        }
    }
    profiles = load_personas(personas_dir, config)
    assert profiles["shared"]["label"] == "From File"
    assert profiles["shared"]["instruction"] == "File instruction."


def test_skips_underscore_files(tmp_path):
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()
    (personas_dir / "_base.md").write_text("---\nlabel: Base\n---\nBase.")
    profiles = load_personas(personas_dir, {"persona": {"profiles": {}}})
    assert "_base" not in profiles
    assert "base" not in profiles
