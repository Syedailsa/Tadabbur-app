"""
evaluate_story_agent.py
=======================
Tadabbur STORY AGENT — Standalone Evaluation Script

PLACE THIS FILE IN:  backend/   (same folder as main.py)

RUN:
    python evaluate_story_agent.py

REQUIREMENTS:
    - .env mein API keys hone chahiye (GROQ_AI_API_KEY, FIREWORKS_AI_API_KEY)
    - HuggingFace image credits hone chahiye (story generation ke liye)
    - backend/ folder ke andar se run karo

NOTE:
    Story agent directly invoke hoga — main agent bypass karke.
    Yeh test karega ke story_agent apne aap sahi kaam karta hai ya nahi.
"""

import asyncio
import sys
import os
import time
import unicodedata
from typing import Optional, List
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# ── Colors ───────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def header(t):  print(f"\n{BOLD}{CYAN}{'='*65}{RESET}\n{BOLD}{CYAN}  {t}{RESET}\n{BOLD}{CYAN}{'='*65}{RESET}")
def section(t): print(f"\n{BOLD}{BLUE}── {t} ──{RESET}")
def passed(t):  print(f"  {GREEN}✅ PASS{RESET}  {t}")
def failed(t):  print(f"  {RED}❌ FAIL{RESET}  {t}")
def warned(t):  print(f"  {YELLOW}⚠️  WARN{RESET}  {t}")

def normalize(text: str) -> str:
    """Unicode normalize + lowercase."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode()
    return text.lower()


# ============================================================================
# EVAL CASE
# ============================================================================

@dataclass
class EvalCase:
    test_id: str
    query: str
    expected_tool: Optional[str]          # "generate_ai_images_story" ya None
    must_contain: List[str]               = field(default_factory=list)
    must_not_contain: List[str]           = field(default_factory=list)
    should_refuse: bool                   = False   # True = tool call nahi hona chahiye
    check_tool: bool                      = True
    description: str                      = ""
    is_known_bug: bool                    = False


@dataclass
class EvalResult:
    test_id: str
    description: str
    passed: bool
    tool_correct: bool
    content_correct: bool
    response_preview: str
    tool_used: str
    latency_ms: float
    failure_reason: str = ""
    is_known_bug: bool  = False


# ============================================================================
# TEST CASES — 12 cases covering all scenarios
# ============================================================================

STORY_EVAL_CASES: List[EvalCase] = [

    # =========================================================================
    # 1. VALID STORY REQUESTS — generate_ai_images_story ZAROOR call hona chahiye
    # =========================================================================
    EvalCase(
        test_id="SA-01",
        query="Tell me the story of Prophet Ibrahim",
        expected_tool="generate_ai_images_story",
        must_contain=["ibrahim", "abraham", "story", "prophet",
                      "visual", "image", "generating", "segments", "ready",
                      "fire", "allah"],
        must_not_contain=["http://", "https://"],
        description="Story — Ibrahim. Tool must be called"
    ),
    EvalCase(
        test_id="SA-02",
        query="Tell me the story of Prophet Nuh and the ark",
        expected_tool="generate_ai_images_story",
        must_contain=["nuh", "noah", "ark", "flood", "story", "prophet",
                      "visual", "image", "generating", "segments", "ready"],
        must_not_contain=["http://", "https://"],
        description="Story — Nuh/Noah. Tool must be called"
    ),
    EvalCase(
        test_id="SA-03",
        query="Tell me the story of Prophet Yusuf and his brothers",
        expected_tool="generate_ai_images_story",
        must_contain=["yusuf", "joseph", "brothers", "egypt", "story",
                      "visual", "image", "generating", "segments", "ready"],
        must_not_contain=["http://", "https://"],
        description="Story — Yusuf. Tool must be called"
    ),
    EvalCase(
        test_id="SA-04",
        query="Tell me the story of Prophet Adam and Hawwa",
        expected_tool="generate_ai_images_story",
        must_contain=["adam", "hawwa", "eve", "paradise", "jannah", "story",
                      "visual", "image", "generating", "segments", "ready"],
        must_not_contain=["http://", "https://"],
        description="Story — Adam & Hawwa (must be Quranic, not Biblical)"
    ),
    EvalCase(
        test_id="SA-05",
        query="Tell me the story of Prophet Musa",
        expected_tool="generate_ai_images_story",
        must_contain=["musa", "moses", "pharaoh", "egypt", "story", "prophet",
                      "visual", "image", "generating", "segments", "ready"],
        must_not_contain=["http://", "https://"],
        description="[BUG] Story — Musa. Sub-agent may think no query exists",
        is_known_bug=True
    ),
    EvalCase(
        test_id="SA-06",
        query="Tell me the story of Prophet Sulaiman and the Queen of Sheba",
        expected_tool="generate_ai_images_story",
        must_contain=["sulaiman", "solomon", "queen", "sheba", "story",
                      "visual", "image", "generating", "segments", "ready"],
        must_not_contain=["http://", "https://"],
        description="[BUG] Story — Sulaiman. Tests query passing bug",
        is_known_bug=True
    ),

    # =========================================================================
    # 2. GREETING — koi tool call nahi hona chahiye
    # =========================================================================
    EvalCase(
        test_id="SA-GREET-01",
        query="Assalamu Alaikum",
        expected_tool=None,
        check_tool=False,
        must_contain=["salam", "alaikum", "hello", "welcome",
                      "story", "help", "assist", "peace"],
        description="Greeting — warm response, NO tool call"
    ),

    # =========================================================================
    # 3. OFF-TOPIC REFUSAL — koi tool call nahi, redirect hona chahiye
    # =========================================================================
    EvalCase(
        test_id="SA-REFUSE-01",
        query="What is the weather in Karachi?",
        expected_tool=None,
        should_refuse=True,
        must_contain=["sorry", "redirect", "story", "quran",
                      "purpose", "assist", "help"],
        description="Off-topic weather — must redirect, no image generation"
    ),
    EvalCase(
        test_id="SA-REFUSE-02",
        query="Write Python code for me",
        expected_tool=None,
        should_refuse=True,
        must_contain=["sorry", "redirect", "story", "quran",
                      "purpose", "assist"],
        must_not_contain=["import ", "def ", "class "],
        description="Off-topic coding — must redirect, no image generation"
    ),
    EvalCase(
        test_id="SA-REFUSE-03",
        query="What is 2 + 2?",
        expected_tool=None,
        should_refuse=True,
        must_contain=["sorry", "story", "quran", "redirect",
                      "purpose", "assist", "help"],
        description="Off-topic math — must redirect"
    ),

    # =========================================================================
    # 4. RAW OUTPUT GUARD
    # Tool call ke baad agent ko raw JSON kabhi nahi dikhana chahiye
    # =========================================================================
    EvalCase(
        test_id="SA-RAW-01",
        query="Tell me the story of Prophet Yunus",
        expected_tool="generate_ai_images_story",
        must_contain=["visual", "image", "generating", "segments",
                      "ready", "story", "yunus", "jonah"],
        # Agent ne yeh kabhi response mein nahi dikhana
        must_not_contain=[
            '"story_paragraph"',
            '"paragraph_title"',
            '"scene_summary"',
            '"success":',
            '"story_data"',
            "http://",
            "https://"
        ],
        description="Raw output guard — tool JSON must never appear in response"
    ),

    # =========================================================================
    # 5. CONTENT ACCURACY — story Quranic honi chahiye, fabricated nahi
    # =========================================================================
    EvalCase(
        test_id="SA-CONTENT-01",
        query="Tell me the story of Prophet Isa",
        expected_tool="generate_ai_images_story",
        must_contain=["isa", "jesus", "story", "prophet", "allah",
                      "visual", "image", "generating", "segments", "ready"],
        # Biblical elements jo Quran mein nahi hain
        must_not_contain=["crucifixion", "cross", "resurrection", "http://", "https://"],
        description="Content accuracy — Isa story must be Quranic version only"
    ),
]


# ============================================================================
# STORY AGENT INVOCATION
# Direct invoke — main agent bypass karta hai
# ============================================================================

async def invoke_story_agent(query: str) -> dict:
    """
    Story agent ko directly invoke karta hai.

    IMPORTANT: Yahan query HumanMessage ke zariye pass hoti hai.
    Yahi BUG-1 ka fix bhi hai — story_agent_tool mein bhi yahi
    hona chahiye lekin abhi nahi ho raha.
    """
    try:
        from tadabbur_agents.story_agent import story_agent
        from langchain.messages import HumanMessage

        tools_called   = []
        final_messages = []

        # ── Query HumanMessage ke zariye pass karo ──────────────────────────
        # Yeh production mein bhi aise hona chahiye
        messages = [HumanMessage(content=query)]

        async for event in story_agent.astream_events(
            {"messages": messages}, version="v2"
        ):
            etype     = event.get("event", "")
            tool_name = event.get("name", "")

            if etype == "on_tool_start" and tool_name:
                if tool_name not in tools_called:
                    tools_called.append(tool_name)
                    print(f"  {DIM}  → Tool called: {CYAN}{tool_name}{RESET}")

            elif etype == "on_chain_end":
                out = event.get("data", {}).get("output")
                if isinstance(out, dict) and "messages" in out:
                    final_messages = out["messages"]

        response_text = ""
        if final_messages:
            last = final_messages[-1]
            response_text = getattr(last, "content", "") or ""

        return {
            "response": response_text,
            "tools_called": tools_called,
            "error": None
        }

    except Exception as e:
        return {"response": "", "tools_called": [], "error": str(e)}


# ============================================================================
# SINGLE TEST RUNNER
# ============================================================================

async def run_single_eval(case: EvalCase) -> EvalResult:
    start      = time.time()
    result     = await invoke_story_agent(case.query)
    latency_ms = (time.time() - start) * 1000

    raw          = result["response"]
    response     = normalize(raw)
    tools_used   = result["tools_called"]
    error        = result["error"]
    tool_str     = ", ".join(tools_used) if tools_used else "none"
    failure_reasons = []

    # ── Exception ────────────────────────────────────────────────────────────
    if error:
        return EvalResult(
            test_id=case.test_id, description=case.description,
            passed=False, tool_correct=False, content_correct=False,
            response_preview=f"EXCEPTION: {error[:120]}",
            tool_used=tool_str, latency_ms=latency_ms,
            failure_reason=f"Exception: {error}",
            is_known_bug=case.is_known_bug
        )

    if not response.strip():
        return EvalResult(
            test_id=case.test_id, description=case.description,
            passed=False, tool_correct=False, content_correct=False,
            response_preview="[EMPTY RESPONSE]",
            tool_used=tool_str, latency_ms=latency_ms,
            failure_reason="Agent returned empty response",
            is_known_bug=case.is_known_bug
        )

    # ── Tool check ────────────────────────────────────────────────────────────
    tool_correct = True
    if case.check_tool:
        if case.should_refuse:
            # Off-topic mein generate_ai_images_story call nahi hona chahiye
            if "generate_ai_images_story" in tools_used:
                tool_correct = False
                failure_reasons.append(
                    "Should refuse but called generate_ai_images_story"
                )
        elif case.expected_tool:
            if case.expected_tool not in tools_used:
                tool_correct = False
                failure_reasons.append(
                    f"Expected '{case.expected_tool}' — got: {tool_str}"
                )

    # ── Content check ─────────────────────────────────────────────────────────
    content_correct = True
    if case.must_contain:
        found = any(normalize(kw) in response for kw in case.must_contain)
        if not found:
            content_correct = False
            failure_reasons.append(
                f"Missing keywords — expected any of: {case.must_contain}"
            )

    for fw in case.must_not_contain:
        if normalize(fw) in response:
            content_correct = False
            failure_reasons.append(f"Forbidden content found: '{fw}'")

    overall = tool_correct and content_correct
    preview = raw[:130].replace("\n", " ") + ("..." if len(raw) > 130 else "")

    return EvalResult(
        test_id=case.test_id, description=case.description,
        passed=overall, tool_correct=tool_correct,
        content_correct=content_correct,
        response_preview=preview, tool_used=tool_str,
        latency_ms=latency_ms,
        failure_reason=" | ".join(failure_reasons),
        is_known_bug=case.is_known_bug
    )


# ============================================================================
# MAIN
# ============================================================================

async def main():
    header("TADABBUR STORY AGENT — EVALUATION SUITE")
    print(f"\n  Total cases  : {BOLD}{len(STORY_EVAL_CASES)}{RESET}")
    print(f"  Model        : {BOLD}openai/gpt-oss-120b{RESET}")
    print(f"  Image API    : {BOLD}HuggingFace (credits required){RESET}")
    print(f"  {YELLOW}Note: Story tests call real image generation API{RESET}\n")

    all_results: List[EvalResult] = []

    categories = {
        "SA-0":       "Story Requests",
        "SA-GREET":   "Greetings",
        "SA-REFUSE":  "Refusal / Off-topic",
        "SA-RAW":     "Raw Output Guard",
        "SA-CONTENT": "Content Accuracy",
    }

    for prefix, cat_name in categories.items():
        cases = [c for c in STORY_EVAL_CASES if c.test_id.startswith(prefix)]
        if not cases:
            continue
        section(cat_name)

        for case in cases:
            bug_tag = f" {YELLOW}[KNOWN BUG]{RESET}" if case.is_known_bug else ""
            print(f"\n  {BOLD}[{case.test_id}]{RESET}{bug_tag} {DIM}{case.description.replace('[BUG] ','')}{RESET}")
            print(f"  {DIM}Query: \"{case.query}\"{RESET}")

            r = await run_single_eval(case)
            all_results.append(r)

            # Story agent ke liye SLA 30s hai (image generation slow hoti hai)
            lc = GREEN if r.latency_ms < 15000 else (YELLOW if r.latency_ms < 30000 else RED)

            if r.passed:
                passed(f"Tool: {CYAN}{r.tool_used}{RESET}  |  Latency: {lc}{r.latency_ms:.0f}ms{RESET}")
                print(f"  {DIM}Response: {r.response_preview}{RESET}")
            else:
                failed(f"Tool: {CYAN}{r.tool_used}{RESET}  |  Latency: {lc}{r.latency_ms:.0f}ms{RESET}")
                print(f"  {RED}Reason : {r.failure_reason}{RESET}")
                print(f"  {DIM}Response: {r.response_preview}{RESET}")

    # ── Final Report ──────────────────────────────────────────────────────────
    total      = len(all_results)
    pass_count = sum(1 for r in all_results if r.passed)
    fail_count = total - pass_count
    bug_fails  = sum(1 for r in all_results if not r.passed and r.is_known_bug)
    real_fails = fail_count - bug_fails
    pass_rate  = (pass_count / total * 100) if total else 0
    avg_lat    = sum(r.latency_ms for r in all_results) / total if total else 0
    sorted_lat = sorted(r.latency_ms for r in all_results)
    p95_lat    = sorted_lat[max(0, int(total * 0.95) - 1)] if total else 0

    rate_color = GREEN if pass_rate >= 90 else (YELLOW if pass_rate >= 70 else RED)

    header("STORY AGENT — FINAL REPORT")
    print(f"\n  {BOLD}Total Cases        :{RESET}  {total}")
    print(f"  {BOLD}Passed             :{RESET}  {GREEN}{pass_count}{RESET}")
    print(f"  {BOLD}Failed             :{RESET}  {RED}{fail_count}{RESET}")
    print(f"  {BOLD}  ↳ Known Bugs     :{RESET}  {YELLOW}{bug_fails}{RESET}  {DIM}(fix in story_agent_tool.py){RESET}")
    print(f"  {BOLD}  ↳ Real Failures  :{RESET}  {real_fails}")
    print(f"  {BOLD}Pass Rate          :{RESET}  {rate_color}{BOLD}{pass_rate:.1f}%{RESET}")
    print(f"  {BOLD}Avg Latency        :{RESET}  {avg_lat:.0f}ms")
    print(f"  {BOLD}p95 Latency        :{RESET}  {p95_lat:.0f}ms  {DIM}(SLA target <30s){RESET}")

    if fail_count:
        print(f"\n  {RED}{BOLD}Failed Cases:{RESET}")
        for r in all_results:
            if not r.passed:
                bm = f" {YELLOW}[BUG]{RESET}" if r.is_known_bug else ""
                print(f"  {RED}✗{RESET}{bm} [{r.test_id}] {r.description.replace('[BUG] ','')}")
                print(f"      {DIM}{r.failure_reason[:120]}{RESET}")

    slow = [r for r in all_results if r.latency_ms > 30000]
    if slow:
        print(f"\n  {YELLOW}{BOLD}SLA Breaches (>30s):{RESET}")
        for r in slow:
            print(f"  {YELLOW}⚠{RESET} [{r.test_id}] {r.latency_ms:.0f}ms — {r.description}")

    # ── Bug Report ────────────────────────────────────────────────────────────
    print(f"\n{BOLD}{'─'*65}{RESET}")
    print(f"{BOLD}  BUGS TO FIX IN story_agent_tool.py:{RESET}")
    print(f"""
  {RED}BUG-1 [CRITICAL] — Query HumanMessage ke zariye pass nahi hoti{RESET}

  Problem:
    story_agent_tool abhi query ko sirf string ke tor pe pass
    karta hai. Sub-agent (story_agent) ko yeh string system/
    developer message lagti hai — isliye kehta hai:
    "user hasn't asked anything yet"
    Phir 6-7 baar retry karta hai tokens waste karta hua.

  Fix in tools/story_agent_tool.py:
  ─────────────────────────────────
    # GALAT (current):
    result = story_agent.invoke({{"input": query}})

    # SAHI (fix):
    from langchain.messages import HumanMessage
    result = story_agent.invoke({{"messages": [HumanMessage(content=query)]}})

  {RED}BUG-2 [CRITICAL] — generate_ai_images_story mein dummy image call{RESET}

  Problem:
    Tool shuru mein ek dummy image generate karta hai credits
    check karne ke liye. Yeh HAMESHA ek extra API call waste
    karta hai — har story request pe.

  Fix:
    Dummy call hatao. Credits check karne ke liye pehle
    HuggingFace balance API call karo, ya credits error ko
    first real image pe catch karo.

  {YELLOW}BUG-3 [MEDIUM] — 8 segments ka hard cap enforce nahi{RESET}

  Fix in generate_ai_images_story():
    args = args[:8]  # pehli line mein add karo

  {YELLOW}BUG-4 [MEDIUM] — Retry loop mein koi sleep nahi{RESET}

  Fix in generate_ai_images_story():
    import asyncio
    # prompt generation retry loop mein:
    await asyncio.sleep(1.0 * try_number)
    # image generation retry loop mein:
    await asyncio.sleep(1.5 * try_number)
""")

    print(f"{BOLD}{'='*65}{RESET}")
    if pass_rate >= 90:
        print(f"{GREEN}{BOLD}  ✅ STORY AGENT PASSED ({pass_rate:.1f}%){RESET}")
    elif pass_rate >= 70:
        print(f"{YELLOW}{BOLD}  ⚠️  NEEDS IMPROVEMENT — Fix BUG-1 first ({pass_rate:.1f}%){RESET}")
    else:
        print(f"{RED}{BOLD}  ❌ STORY AGENT FAILED — Critical bugs found ({pass_rate:.1f}%){RESET}")
    print(f"{BOLD}{'='*65}{RESET}\n")

    sys.exit(0 if pass_rate >= 90 else 1)


if __name__ == "__main__":
    print(f"\n{BOLD}{CYAN}  Tadabbur Story Agent Evaluator{RESET}")
    print(f"  {DIM}Direct story_agent invocation — main agent bypass{RESET}\n")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}  Cancelled.{RESET}\n")
        sys.exit(1)