from src.config import load_config


def test_load_config_defaults(tmp_path):
    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text("camera:\n  index: 2\n", encoding="utf-8")

    cfg = load_config(cfg_file)
    assert cfg.camera.index == 2
    assert cfg.detection.freeze_seconds == 30.0
    assert cfg.alerts.enabled_methods is not None
