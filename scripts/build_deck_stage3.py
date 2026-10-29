import build_deck as base  # pyrefly: ignore[missing-import]

SHOTS = base.SHOTS
OUT = base.DOCS / "parking_chatbot_stage3.pptx"
base.FOOTER = "Parking Reservation Chatbot  |  Stage 3"

ARCH = SHOTS / "s3_architecture.png"
SECURITY = SHOTS / "s3_01_security_checks.png"
CONSOLE = SHOTS / "s3_02_console_save.png"
CHAT = SHOTS / "s3_03_end_to_end.png"
FILE = SHOTS / "s3_04_reservation_file.png"
TESTS = SHOTS / "s3_05a_tests_passed.png"
CI = SHOTS / "s3_05b_ci_pipeline.png"

REQUIRED = [ARCH, SECURITY, CONSOLE, CHAT, FILE, TESTS, CI]


def title_slide():
    prs = base.prs
    slide = prs.slides.add_slide(base.BLANK)
    background = slide.shapes.add_shape(
        base.MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    background.fill.solid()
    background.fill.fore_color.rgb = base.NAVY
    background.line.fill.background()
    base.add_text(slide, "MCP Server for Approved Reservations", 0.9, 2.3, 11.5, 1.2,
                  size=44, bold=True, color=base.WHITE)
    base.add_text(slide, "Stage 3 of 4: secure recording of approved bookings", 0.9, 3.6,
                  11.5, 0.7, size=24, color=base.PALE)
    base.add_text(slide, "Edupuganti Likhith", 0.9, 5.4, 11.5, 0.5, size=18, color=base.WHITE)
    base.add_text(slide, "github.com/likhithe2204/parking-chatbot", 0.9, 5.9, 11.5, 0.5,
                  size=16, color=base.PALE)
    slide.notes_slide.notes_text_frame.text = (
        "Stage 2 added the administrator. Stage 3 saves every approved booking to a "
        "text file through a secured MCP server."
    )


def coverage_slide():
    slide = base.base_slide(
        "What the task asked and what was delivered",
        "Go row by row. Every Stage 3 requirement has a working feature and proof.",
    )
    rows = [
        ("MCP server with Python and FastAPI", "MCP tool mounted in a FastAPI app", "Slide 3"),
        ("Write after the administrator approves", "Approving in the console saves the booking", "Slides 4 and 5"),
        ("Entry: Name, Car, Period, Approval Time", "One line per booking, four columns", "Slide 6"),
        ("Secure against unauthorized access", "API key on every route, strict validation", "Slide 7"),
        ("Reliable service", "File lock, flush to disk, no duplicates, retry command", "Slides 6 and 7"),
        ("Extra artifacts", "README, 179 pytest tests, GitHub Actions CI, this deck", "Slide 8"),
    ]
    base.add_table(slide, ("Requirement", "What was built", "Proof"), rows, 0.6, 1.5,
                   (3.9, 6.6, 1.65))


def tests_slide():
    slide = base.base_slide(
        "Tests, CI/CD and documentation",
        "Left: the pytest result. Right: the green pipeline run.",
    )
    base.add_bullets(
        slide,
        [
            "179 pytest tests across the project, at least 2 per core module, no API key needed.",
            "GitHub Actions runs them on every push. The README documents setup, usage and structure.",
        ],
        0.6, 1.4, 12.0, 1.2, size=17,
    )
    base.add_image_fit(slide, TESTS, 0.6, 2.7, 6.0, 4.2)
    base.add_image_fit(slide, CI, 6.75, 2.7, 6.0, 4.2)


def build() -> None:
    missing = [str(p.relative_to(base.ROOT)) for p in REQUIRED if not p.exists()]
    if missing:
        raise SystemExit("Missing images:\n  " + "\n  ".join(missing))

    title_slide()
    coverage_slide()

    base.wide_image_slide(
        "Architecture of the recording step",
        ARCH,
        "Two ways in: the console on approval, and the customer's status check. "
        "Both go through the same secured MCP server.",
    )

    base.image_slide(
        "Approval saves the booking",
        [
            "The administrator approves in the console.",
            "The console calls the MCP server, which saves the booking at once.",
            "If saving fails, the decision is kept and the console says so.",
            "Typing s retries every approved booking that was not saved.",
        ],
        CONSOLE,
        "The human decision triggers the write. The model is not involved.",
    )

    base.image_slide(
        "End to end: approved and saved",
        [
            "The customer books, the request goes to the administrator, the administrator approves.",
            "The customer's status check confirms the booking is saved.",
            "The code decides what is saved, never the language model.",
        ],
        CHAT,
        "Request id, pending, approval and the saved booking in one conversation.",
    )

    base.image_slide(
        "The reservations file",
        [
            "One line per booking: Name | Car Number | Reservation Period | Approval Time.",
            "Writes are locked, flushed to disk and appended.",
            "The same booking is never written twice.",
            "The file holds customer data, so it is kept out of Git.",
        ],
        FILE,
        "This is the exact format the task asked for.",
    )

    base.image_slide(
        "Security checks",
        [
            "Every route except the health check needs the API key.",
            "Wrong key, bad car number, a separator in a name and an end before the start are all blocked.",
            "The server exposes one tool only and validates every field again.",
        ],
        SECURITY,
        "Four blocked requests and a 401 for a caller without the key.",
    )

    tests_slide()

    base.text_slide(
        "Outcomes and next stage",
        [
            "A working MCP server integrated with the administrator and the chatbot.",
            "Approved bookings are saved to a text file in the required format.",
            "The server rejects unauthorized and invalid requests.",
            "Next: Stage 4 LangGraph orchestrates the chatbot, the administrator and the server.",
            "Repository: github.com/likhithe2204/parking-chatbot (tag stage-3)",
        ],
        "Close with the outcome and the roadmap.",
    )

    base.prs.save(OUT)
    print(f"Saved {OUT} with {len(base.prs.slides)} slides")


if __name__ == "__main__":
    build()