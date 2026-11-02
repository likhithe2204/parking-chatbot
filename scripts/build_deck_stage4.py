import build_deck as base  # pyrefly: ignore[missing-import]

SHOTS = base.SHOTS
OUT = base.DOCS / "parking_chatbot_stage4.pptx"
base.FOOTER = "Parking Reservation Chatbot  |  Stage 4"

ARCH = SHOTS / "s4_architecture.png"
GRAPH = SHOTS / "s4_01_workflow_graph.png"
CHAT_APPROVE = SHOTS / "s4_02_end_to_end_approve.png"
CHAT_REJECT = SHOTS / "s4_02_end_to_end_reject.png"
CONSOLE_APPROVE = SHOTS / "s4_03_admin_console_approve.png"
CONSOLE_REJECT = SHOTS / "s4_03_admin_console_reject.png"
FILE = SHOTS / "s4_04_reservations_file.png"
LOAD = SHOTS / "s4_05_load_test.png"
ORCHESTRATION = SHOTS / "s4_06_orchestration_tests.png"
TESTS = SHOTS / "s4_07a_tests_passed.png"
CI = SHOTS / "s4_07b_ci_pipeline.png"
AVAILABILITY = SHOTS / "s4_08_availability_updates.png"

REQUIRED = [
    ARCH, GRAPH, CHAT_APPROVE, CHAT_REJECT, CONSOLE_APPROVE, CONSOLE_REJECT,
    FILE, LOAD, ORCHESTRATION, TESTS, CI, AVAILABILITY,
]


def title_slide():
    prs = base.prs
    slide = prs.slides.add_slide(base.BLANK)
    background = slide.shapes.add_shape(
        base.MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    background.fill.solid()
    background.fill.fore_color.rgb = base.NAVY
    background.line.fill.background()
    base.add_text(slide, "LangGraph Orchestration", 0.9, 2.3, 11.5, 1.2,
                  size=44, bold=True, color=base.WHITE)
    base.add_text(slide, "Stage 4 of 4: one workflow for chatbot, administrator and MCP server",
                  0.9, 3.6, 11.5, 0.7, size=24, color=base.PALE)
    base.add_text(slide, "Edupuganti Likhith", 0.9, 5.4, 11.5, 0.5, size=18, color=base.WHITE)
    base.add_text(slide, "github.com/likhithe2204/parking-chatbot", 0.9, 5.9, 11.5, 0.5,
                  size=16, color=base.PALE)
    slide.notes_slide.notes_text_frame.text = (
        "Stages 1 to 3 built the parts. Stage 4 connects them in one LangGraph workflow "
        "and tests the whole pipeline."
    )


def coverage_slide():
    slide = base.base_slide(
        "What the task asked and what was delivered",
        "Go row by row. Every Stage 4 requirement has a working feature and proof.",
    )
    rows = [
        ("Orchestrate with LangGraph", "One graph: chatbot, escalate, await_approval, record, notify", "Slides 3 and 4"),
        ("Chatbot interacts with users", "RAG, SQL tools and guardrails in the chatbot node", "Slides 5 and 8"),
        ("Escalate to the administrator", "Admin agent sends the request, the graph pauses for the human", "Slides 5 and 6"),
        ("MCP server processes the data", "The record node saves the booking, with retries", "Slides 5 and 7"),
        ("Workflow logic for the pipeline", "Approve, refuse and failure paths, all tested", "Slides 5, 6 and 10"),
        ("Load tests", "Chatbot, administrator confirmation and MCP recording", "Slide 9"),
        ("Integration tests", "Real services, scripted model", "Slide 10"),
        ("Documentation", "README: architecture, agent and server logic, deployment", "Slide 12"),
    ]
    base.add_table(slide, ("Requirement", "What was built", "Proof"), rows, 0.6, 1.5,
                   (3.6, 6.8, 1.75))


def two_images_slide(title, bullets, left, right, notes=""):
    slide = base.base_slide(title, notes)
    base.add_bullets(slide, bullets, 0.6, 1.4, 12.0, 1.2, size=17)
    base.add_image_fit(slide, left, 0.6, 2.7, 6.0, 4.2)
    base.add_image_fit(slide, right, 6.75, 2.7, 6.0, 4.2)


def load_slide():
    slide = base.base_slide(
        "Load tests",
        "Three components, tested under concurrent load with their own temporary servers.",
    )
    base.add_stat_card(slide, "0", "Errors in all tests", 0.6, 1.5)
    base.add_stat_card(slide, "50 / 50", "Bookings written once", 2.95, 1.5)
    base.add_stat_card(slide, "11 ops/s", "Admin confirmations", 0.6, 3.05)
    base.add_stat_card(slide, "11.5 ops/s", "MCP recordings", 2.95, 3.05)
    base.add_bullets(
        slide,
        [
            "50 concurrent operations per server test, 10 workers.",
            "Chatbot: 3 conversations, 9 messages, about 6 s each (model time).",
        ],
        0.6, 4.7, 4.5, 2.0, size=15,
    )
    base.add_image_fit(slide, LOAD, 5.2, 1.5, 7.55, 5.3)


def build() -> None:
    missing = [str(p.relative_to(base.ROOT)) for p in REQUIRED if not p.exists()]
    if missing:
        raise SystemExit("Missing images:\n  " + "\n  ".join(missing))

    title_slide()
    coverage_slide()

    base.wide_image_slide(
        "Architecture",
        ARCH,
        "The five workflow nodes in the middle, the services around them.",
    )

    base.image_slide(
        "One graph for the whole pipeline",
        [
            "chatbot answers and collects the booking.",
            "escalate: the admin agent sends the request.",
            "await_approval: the graph pauses until the human decides.",
            "record saves an approved booking, notify tells the customer.",
        ],
        GRAPH,
        "A normal question ends after the chatbot node. A booking continues through the other nodes.",
    )

    two_images_slide(
        "End to end: approved",
        [
            "The customer books, the administrator approves in the console.",
            "The customer is told by itself that the booking is saved.",
        ],
        CHAT_APPROVE, CONSOLE_APPROVE,
        "Left: the chat with the automatic update. Right: the administrator console.",
    )

    two_images_slide(
        "End to end: refused",
        [
            "A refusal reaches the customer with the reason.",
            "Nothing is saved and no space is taken.",
        ],
        CHAT_REJECT, CONSOLE_REJECT,
        "Left: the chat. Right: the administrator console.",
    )

    two_images_slide(
        "Saved booking and live availability",
        [
            "One line per approved booking: Name | Car Number | Reservation Period | Approval Time.",
            "An approval takes a space, so free spaces drop for that period only.",
        ],
        FILE, AVAILABILITY,
        "Left: the reservations file. Right: availability before and after an approval.",
    )


    load_slide()

    base.image_slide(
        "Integration tests",
        [
            "The real admin service and the real MCP server, only the model is scripted.",
            "Approval, refusal, a down MCP server and recovery after a restart.",
            "An approved booking takes a space for its period only.",
        ],
        ORCHESTRATION,
        "These tests prove the components work together through the workflow.",
    )

    two_images_slide(
        "Tests, CI/CD and documentation",
        [
            "240 pytest tests, at least 2 per core module, no API key needed.",
            "GitHub Actions runs them on every push. The README covers architecture, logic and deployment.",
        ],
        TESTS, CI,
        "Left: the pytest result. Right: the green pipeline run.",
    )

    base.text_slide(
        "Outcomes",
        [
            "One workflow connects the chatbot, the administrator and the MCP server.",
            "Approved bookings are saved once, in the required format, and take a space.",
            "The pipeline is tested end to end and under load.",
            "Repository: github.com/likhithe2204/parking-chatbot (tag stage-4)",
        ],
        "Close with the outcome, then take questions.",
    )

    base.prs.save(OUT)
    print(f"Saved {OUT} with {len(base.prs.slides)} slides")


if __name__ == "__main__":
    build()