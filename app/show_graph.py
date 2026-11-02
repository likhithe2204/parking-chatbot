from app.config import ROOT
from app.workflow import Workflow

PNG_PATH = ROOT / "docs" / "screenshots" / "s4_01_workflow_graph.png"
MERMAID_PATH = ROOT / "docs" / "workflow_graph.mmd"


def main() -> None:
    workflow = Workflow(lambda session, message: "", None)
    drawable = workflow.graph.get_graph()

    mermaid = drawable.draw_mermaid()
    MERMAID_PATH.parent.mkdir(parents=True, exist_ok=True)
    MERMAID_PATH.write_text(mermaid, encoding="utf-8")
    print(mermaid)

    try:
        PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
        PNG_PATH.write_bytes(drawable.draw_mermaid_png())
        print(f"Saved {PNG_PATH}")
    except Exception as exc:
        print(f"Could not draw the PNG automatically ({exc}).")
        print(
            f"Paste the text from {MERMAID_PATH} into https://mermaid.live "
            f"and save the image as {PNG_PATH}."
        )


if __name__ == "__main__":
    main()