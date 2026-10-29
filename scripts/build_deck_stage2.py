# pyrefly: ignore[missing-import]
import build_deck as base

SHOTS = base.SHOTS
OUT = base.DOCS / "parking_chatbot_stage2.pptx"
base.FOOTER = "Parking Reservation Chatbot  |  Stage 2"

ARCH = SHOTS / "s2_architecture.png"
API_DOCS = SHOTS / "s2_01_admin_api_docs.png"
CONSOLE = SHOTS / "s2_02_admin_console.png"
AGENT = SHOTS / "s2_03_admin_agent.png"
APPROVED = SHOTS / "s2_04_end_to_end.png"
REFUSED = SHOTS / "s2_05_refusal.png"
TESTS = SHOTS / "s2_06a_tests_passed.png"
CI = SHOTS / "s2_06b_ci_pipeline.png"

REQUIRED = [ARCH, API_DOCS, CONSOLE, AGENT, APPROVED, REFUSED, TESTS, CI]


def title_slide():
    prs = base.prs
    slide = prs.slides.add_slide(base.BLANK)
    background = slide.shapes.add_shape(
        base.MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    background.fill.solid()
    background.fill.fore_color.rgb = base.NAVY
    background.line.fill.background()
    base.add_text(slide, "Human-in-the-Loop Reservation Approval", 0.9, 2.3, 11.5, 1.2,
                  size=44, bold=True, color=base.WHITE)
    base.add_text(slide, "Stage 2 of 4: administrator agent, REST service and escalation",
                  0.9, 3.6, 11.5, 0.7, size=24, color=base.PALE)
    base.add_text(slide, "Edupuganti Likhith", 0.9, 5.4, 11.5, 0.5, size=18, color=base.WHITE)
    base.add_text(slide, "github.com/likhithe2204/parking-chatbot", 0.9, 5.9, 11.5, 0.5,
                  size=16, color=base.PALE)
    slide.notes_slide.notes_text_frame.text = (
        "Stage 1 built the chatbot. Stage 2 adds a human administrator who approves "
        "or refuses every reservation."
    )


def coverage_slide():
    slide = base.base_slide(
        "What the task asked and what was delivered",
        "Go row by row. Every Stage 2 requirement has a working feature and proof.",
    )
    rows = [
        ("Second agent with LangChain", "Admin agent writes the note and sends the request", "Slide 5"),
        ("Send request, get confirm or refuse", "REST service plus an administrator console", "Slides 4 and 6"),
        ("Integrate with the first agent", "Chatbot escalates after the customer confirms", "Slide 7"),
        ("Receive the response", "Customer asks for the status, decision text comes from code", "Slides 7 and 8"),
        ("Reliable and safe", "API key, one decision per request, fallback note", "Slides 4 and 5"),
        ("Extra artifacts", "README, 142 pytest tests, GitHub Actions CI, this deck", "Slide 9"),
    ]
    base.add_table(slide, ("Requirement", "What was built", "Proof"), rows, 0.6, 1.5,
                   (3.8, 6.7, 1.65))


def tests_slide():
    slide = base.base_slide(
        "Tests, CI/CD and documentation",
        "Left: the pytest result. Right: the green pipeline run.",
    )
    base.add_bullets(
        slide,
        [
            "142 pytest tests across the project, at least 2 per core module, no API key needed.",
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
        "Architecture of the escalation",
        ARCH,
        "Follow the numbers: details, confirmation, request, pending, decision, status.",
    )

    base.image_slide(
        "Admin service: the manager's inbox",
        [
            "A small FastAPI service stores every reservation request.",
            "Every call needs an API key. Requests are validated again on arrival.",
            "A request can be decided only once.",
        ],
        API_DOCS,
        "The interactive API page lists the five endpoints.",
    )

    base.image_slide(
        "Admin agent: the second LangChain agent",
        [
            "The model only writes the note, using the live availability.",
            "Customer details are attached by code, so the model cannot change them.",
            "If the model fails, the request is still sent with a default note.",
        ],
        AGENT,
        "First run sends the request with the note. Second run reads the decision.",
    )

    base.image_slide(
        "Administrator console: the human decision",
        [
            "The administrator sees pending requests and the customer's note.",
            "Approve or refuse, with an optional reason.",
            "The decision is saved and the customer can read it.",
        ],
        CONSOLE,
        "The human stays in control of every reservation.",
    )

    base.image_slide(
        "End to end: approved",
        [
            "Every detail must come from the customer's own words. Made-up values are rejected.",
            "After confirmation the request is sent and the customer gets an id.",
            "The bot says it is not confirmed until the administrator decides.",
        ],
        APPROVED,
        "Request sent, pending, then approved with the administrator's reason.",
    )

    base.image_slide(
        "End to end: refused",
        [
            "A refusal is shown to the customer with the administrator's reason.",
            "The decision text comes from code, so a refusal is never worded as an approval.",
            "If the admin service is down, the customer is told the request was not sent.",
        ],
        REFUSED,
        "This proves the confirm or refuse requirement in both directions.",
    )

    tests_slide()

    base.text_slide(
        "Outcomes and next stages",
        [
            "Automated system that connects a human administrator for reservation approval.",
            "Requests, decisions and status flow between the two agents.",
            "Next: Stage 3 MCP server writes approved reservations to a file.",
            "Then: Stage 4 LangGraph orchestrates all components.",
            "Repository: github.com/likhithe2204/parking-chatbot (tag stage-2)",
        ],
        "Close with the outcome and the roadmap.",
    )

    base.prs.save(OUT)
    print(f"Saved {OUT} with {len(base.prs.slides)} slides")


if __name__ == "__main__":
    build()