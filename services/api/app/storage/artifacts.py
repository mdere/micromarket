from pathlib import Path


class ArtifactStore:
    def __init__(self, root: str) -> None:
        self.root = Path(root)

    def write_article_text(self, content_hash: str, text: str) -> str:
        path = self.root / "raw" / "articles" / f"{content_hash}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return str(path)
