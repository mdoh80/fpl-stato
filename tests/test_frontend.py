from pathlib import Path


FRONTEND = Path(__file__).parents[1] / "frontend" / "index.html"


def test_skill_overlay_uses_backend_skill_and_exact_bot_images():
    source = FRONTEND.read_text()

    assert "fpl: 'https://raw.githubusercontent.com/mdoh80/images/main/football-comm.png'" in source
    assert "trivia: 'https://raw.githubusercontent.com/mdoh80/images/main/football-stato.png'" in source
    assert "if (data.skill && requestId === latestRequest) showSkill(data.skill);" in source
    assert "pointer-events: none" in source
    assert "prefers-reduced-motion: reduce" in source
