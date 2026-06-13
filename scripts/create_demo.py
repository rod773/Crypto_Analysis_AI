"""
Crypto Analysis AI - Demo Video Generator
Generates a full demo video with English narration using:
  - Playwright (browser automation + screenshots)
  - gTTS (Google Text-to-Speech)
  - FFmpeg (video/audio composition)

Usage: python scripts/create_demo.py
Requires: yarn dev running on localhost:3000
"""

import json
import os
import time
import subprocess
import shutil
from pathlib import Path
from gtts import gTTS
from pydub import AudioSegment
from playwright.sync_api import sync_playwright, expect

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "demo_output"
AUDIO_DIR = OUTPUT_DIR / "audio"
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"

# Narration script segments (text, duration_seconds)
# Durations are approximate targets; actual audio length may vary slightly
SCENES = [
    # Scene 1: Intro & UI Overview (0:00 - 0:25)
    {
        "name": "01_intro",
        "duration": 22,
        "narration": (
            "Welcome to Crypto Analysis AI, your real-time cryptocurrency analysis assistant. "
            "Powered by data from over ten sources, this tool answers the most important question every trader asks: Buy or Sell? "
            "Here is the main interface: a sleek terminal-inspired chat UI with a dark cyberpunk theme. "
            "At the top, the title, asset switcher, and a live source indicator."
        ),
    },
    # Scene 2: Asset Switcher (0:25 - 0:55)
    {
        "name": "02_asset_switcher",
        "duration": 28,
        "narration": (
            "You can switch between three assets instantly: Ethereum, Bitcoin, and Gold. "
            "Each click resets the conversation and loads fresh analysis. "
            "Let's try Bitcoin. The chat resets, the subtitle changes, and we're ready to analyze BTC. "
            "Now Gold — note the source badge changes to five-plus sources. "
            "And back to Ethereum, the default asset with over ten sources available."
        ),
    },
    # Scene 3: Quick Suggestions (0:55 - 1:20)
    {
        "name": "03_suggestions",
        "duration": 22,
        "narration": (
            "To help you get started, the app provides quick suggestion buttons: "
            "Should I buy ETH today? What is the best time to sell? Technical analysis, and what are the whales saying? "
            "These are one-click prompts. Let's click the first one. "
            "The text populates the input field automatically."
        ),
    },
    # Scene 4: Send Query + Loading (1:20 - 1:40)
    {
        "name": "04_loading",
        "duration": 15,
        "narration": (
            "We click Analyze, and the app immediately begins scraping over ten sources simultaneously: "
            "CoinGecko, CoinMarketCap, Binance, Fear and Greed Index, DeFi Llama, and more. "
            "A smooth skeleton loading animation appears, giving us visual feedback that data is being collected."
        ),
    },
    # Scene 5: Analysis Result — Verdict & Price (1:40 - 2:10)
    {
        "name": "05_verdict",
        "duration": 28,
        "narration": (
            "And here is the result. First, the current price with an animated counter and the twenty-four hour change highlighted in green or red. "
            "Below that, the verdict card shows the recommendation — Buy, Sell, or Hold — for both short term and long term, "
            "along with a confidence percentage and a clear summary explaining the reasoning. "
            "Then we have the key levels: Stop Loss, Short Take Profit, and Long Take Profit, all clearly displayed."
        ),
    },
    # Scene 6: Scenarios (2:10 - 2:30)
    {
        "name": "06_scenarios",
        "duration": 17,
        "narration": (
            "The app shows probabilistic scenarios: a bearish case and a bullish case, "
            "each with a target price, probability percentage, and what would trigger that move. "
            "This helps you understand the risk-rebalance from both sides."
        ),
    },
    # Scene 7: Expand Detailed Analysis (2:30 - 2:45)
    {
        "name": "07_expand_details",
        "duration": 13,
        "narration": (
            "Now, let's expand the detailed analysis section to see the full power of the engine. "
        ),
    },
    # Scene 8: Detailed Sections (2:45 - 3:15)
    {
        "name": "08_detailed_sections",
        "duration": 28,
        "narration": (
            "Technical indicators: RSI, trend direction, moving averages. "
            "On-chain data: funding rates, exchange flows, staking yield. "
            "Order book: bid and ask depth with ratio analysis. "
            "Whale activity: large transactions and accumulation patterns. "
            "Multi-timeframe analysis: daily, four-hour, and one-hour trends with alignment scoring. "
            "Elliott Wave analysis: wave counting with a progress bar and targets. "
            "Smart Money Concepts: market structure, order blocks, fair value gaps, and liquidity zones. "
            "Macro: upcoming economic events and risk sentiment. "
            "And sentiment analysis: the Fear and Greed Index along with recent news headlines."
        ),
    },
    # Scene 9: Sources + Reset (3:15 - 3:25)
    {
        "name": "09_sources_reset",
        "duration": 10,
        "narration": (
            "At the bottom, you see exactly how many sources were successfully queried, full transparency on data reliability. "
            "When you're ready for a fresh start, just click Back to Start."
        ),
    },
    # Scene 10: Outro (3:25 - 3:35)
    {
        "name": "10_outro",
        "duration": 10,
        "narration": (
            "Crypto Analysis AI: real-time, multi-source, AI-powered market intelligence. "
            "Try it yourself and never trade blind again."
        ),
    },
]

FULL_NARRATION = " ".join(s["narration"] for s in SCENES)


def ensure_dir(d: Path):
    d.mkdir(parents=True, exist_ok=True)


def generate_audio():
    """Generate TTS audio for each scene and the full narration."""
    print("=== Generating TTS audio ===")
    ensure_dir(AUDIO_DIR)

    # Generate per-scene audio
    for scene in SCENES:
        name = scene["name"]
        text = scene["narration"]
        out_path = AUDIO_DIR / f"{name}.mp3"
        if out_path.exists():
            print(f"  {name}: already exists, skipping")
            continue
        try:
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(str(out_path))
            print(f"  {name}: saved ({out_path.stat().st_size} bytes)")
        except Exception as e:
            print(f"  {name}: FAILED - {e}")
            raise

    # Generate full narration audio
    full_path = AUDIO_DIR / "full_narration.mp3"
    if not full_path.exists():
        tts = gTTS(text=FULL_NARRATION, lang="en", slow=False)
        tts.save(str(full_path))
        print(f"  full_narration: saved ({full_path.stat().st_size} bytes)")

    # Measure actual durations
    print("\n=== Audio durations ===")
    total_ms = 0
    for scene in SCENES:
        path = AUDIO_DIR / f"{scene['name']}.mp3"
        audio = AudioSegment.from_mp3(str(path))
        dur = len(audio)
        total_ms += dur
        print(f"  {scene['name']}: {dur/1000:.1f}s (script target: {scene['duration']}s)")
    print(f"  TOTAL: {total_ms/1000:.1f}s")

    return total_ms / 1000


def take_screenshots(browser_context, viewport):
    """Navigate through the demo and take screenshots."""
    print("\n=== Taking screenshots ===")
    ensure_dir(SCREENSHOTS_DIR)

    page = browser_context.new_page()
    page.set_viewport_size(viewport)

    # Load mock data
    with open(str(PROJECT_DIR / "mock_analysis.json")) as f:
        mock_data = json.load(f)

    screenshot_idx = [0]  # mutable counter

    def snap(name):
        idx = screenshot_idx[0]
        screenshot_idx[0] += 1
        path = SCREENSHOTS_DIR / f"{idx:03d}_{name}.png"
        page.screenshot(path=str(path), full_page=False)
        print(f"  [{idx:03d}] {name}")
        return path

    # Helper: wait for animations
    def wait_anim(sec=0.8):
        page.wait_for_timeout(int(sec * 1000))

    def mock_api(route):
        """Intercept /api/analyze and return mock data instantly."""
        url = route.request.url
        if "/api/analyze" in url:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(mock_data),
            )
        else:
            route.continue_()

    # Intercept API calls
    page.route("**/api/analyze*", mock_api)

    # ==========================================================
    # SCENE 1: Intro - Initial app state
    # ==========================================================
    print("\n--- Scene 1: Intro ---")
    page.goto("http://localhost:3000", wait_until="networkidle")
    page.wait_for_timeout(2000)  # Let initial animations play
    snap("01_initial_app")
    wait_anim()

    # Hover over header elements
    page.hover("header h1")
    wait_anim(0.3)
    snap("01_hover_title")

    # Hover suggestion buttons
    suggestion_btns = page.locator("button:has-text('¿Debería')")
    if suggestion_btns.count() > 0:
        suggestion_btns.first.hover()
        wait_anim(0.5)
        snap("01_hover_suggestions")

    # Hover input
    page.locator('input[placeholder*="Pregunta"]').hover()
    wait_anim(0.3)
    snap("01_hover_input")

    # ==========================================================
    # SCENE 2: Asset Switcher
    # ==========================================================
    print("\n--- Scene 2: Asset Switcher ---")

    # Click BTC
    page.locator("button:has-text('BTC')").first.click()
    wait_anim(1.0)
    snap("02_btc_selected")
    wait_anim(0.5)

    # Click Gold
    page.locator("button:has-text('XAU')").first.click()
    wait_anim(1.0)
    snap("02_gold_selected")
    wait_anim(0.5)

    # Click ETH back
    page.locator("button:has-text('ETH')").first.click()
    wait_anim(1.0)
    snap("02_eth_selected")
    wait_anim(0.5)

    # ==========================================================
    # SCENE 3: Quick Suggestions
    # ==========================================================
    print("\n--- Scene 3: Suggestions ---")
    snap("03_suggestions_visible")
    wait_anim(0.5)

    # Click suggestion button
    buy_btn = page.locator("button:has-text('¿Debería comprar')")
    if buy_btn.count() > 0:
        buy_btn.first.hover()
        wait_anim(0.3)
        snap("03_hover_suggestion")
        buy_btn.first.click()
        wait_anim(0.5)
        snap("03_input_filled")

    # ==========================================================
    # SCENE 4: Send Query + Loading
    # ==========================================================
    print("\n--- Scene 4: Loading ---")

    # Click analyze button
    analyze_btn = page.locator('button[type="submit"]')
    analyze_btn.click()
    wait_anim(0.5)
    snap("04_sending")

    # Wait for user message to appear
    page.wait_for_timeout(500)
    snap("04_user_message")

    # Wait for loading skeleton
    page.wait_for_timeout(1000)
    snap("04_loading_skeleton")

    # Wait for analysis to appear (with mocked API it should be instant-ish)
    page.wait_for_timeout(2000)
    snap("04_analysis_appearing")

    # Wait for all animations
    page.wait_for_timeout(2000)

    # ==========================================================
    # SCENE 5: Verdict & Price
    # ==========================================================
    print("\n--- Scene 5: Verdict ---")

    # The analysis card should be visible now
    snap("05_full_analysis")
    wait_anim(0.5)

    # Scroll verdict into view
    verdict_card = page.locator("text=COMPRAR").first
    try:
        verdict_card.scroll_into_view_if_needed()
        wait_anim(0.5)
    except:
        pass
    snap("05_verdict_card")

    # Scroll to key levels
    page.evaluate("window.scrollBy(0, 200)")
    wait_anim(0.5)
    snap("05_key_levels")

    # ==========================================================
    # SCENE 6: Scenarios
    # ==========================================================
    print("\n--- Scene 6: Scenarios ---")
    page.evaluate("window.scrollBy(0, 150)")
    wait_anim(0.5)
    snap("06_scenarios")

    # Hover on bullish scenario
    bullish_card = page.locator("text=Alcista").first
    try:
        bullish_card.hover()
        wait_anim(0.5)
        snap("06_hover_bullish")
    except:
        snap("06_hover_bullish_fallback")

    # ==========================================================
    # SCENE 7: Expand Details
    # ==========================================================
    print("\n--- Scene 7: Expand Details ---")
    page.evaluate("window.scrollBy(0, -200)")  # Scroll back up a bit

    # Click "Análisis detallado" button
    details_btn = page.locator("button:has-text('Análisis detallado')")
    if details_btn.count() > 0:
        details_btn.first.scroll_into_view_if_needed()
        wait_anim(0.3)
        details_btn.first.click()
        wait_anim(1.5)  # Wait for expand animation
        snap("07_details_expanded")

    # ==========================================================
    # SCENE 8: Detailed Sections
    # ==========================================================
    print("\n--- Scene 8: Detailed Sections ---")

    sections = [
        ("técnico", "Técnico"),
        ("onchain", "On-Chain"),
        ("orderbook", "Order Book"),
        ("whales", "Ballenas"),
        ("timeframe", "Multi-Timeframe"),
        ("elliott", "Ondas Elliott"),
        ("smart_money", "Smart Money"),
        ("macro", "Macro"),
        ("sentiment", "Sentimiento"),
    ]

    for fname, label in sections:
        page.evaluate("window.scrollBy(0, 250)")
        wait_anim(0.4)
        snap(f"08_{fname}")

    # Scroll back to top of detailed section
    details_btn_first = page.locator("button:has-text('Análisis detallado')").first
    try:
        details_btn_first.scroll_into_view_if_needed()
        wait_anim(0.3)
    except:
        pass

    # ==========================================================
    # SCENE 9: Sources + Reset
    # ==========================================================
    print("\n--- Scene 9: Sources + Reset")

    # Scroll to bottom to show source counter
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    wait_anim(0.5)
    snap("09_sources_bottom")

    # Click "Volver al inicio"
    reset_btn = page.locator("button:has-text('Volver al inicio')")
    if reset_btn.count() > 0:
        reset_btn.first.scroll_into_view_if_needed()
        wait_anim(0.3)
        reset_btn.first.click()
        wait_anim(1.0)
        snap("09_reset")
    else:
        snap("09_reset_fallback")

    # ==========================================================
    # SCENE 10: Outro
    # ==========================================================
    print("\n--- Scene 10: Outro ---")
    wait_anim(0.5)
    snap("10_final_state")

    page.close()
    return screenshot_idx[0]


def create_video_from_screenshots(num_screenshots):
    """Build final video using FFmpeg: compose screenshots + audio."""
    print("\n=== Creating video with FFmpeg ===")

    # Calculate timing proportions based on actual audio durations
    audio_dir = AUDIO_DIR
    total_audio = AudioSegment.empty()
    scene_durations = []
    for scene in SCENES:
        path = audio_dir / f"{scene['name']}.mp3"
        seg = AudioSegment.from_mp3(str(path))
        scene_durations.append(len(seg) / 1000.0)
        total_audio += seg

    total_duration = len(total_audio) / 1000.0
    print(f"Total audio duration: {total_duration:.1f}s")

    # Save combined audio
    combined_audio = AUDIO_DIR / "combined.mp3"
    total_audio.export(str(combined_audio), format="mp3")
    print(f"Combined audio saved: {combined_audio}")

    # Build concat file for FFmpeg
    # We need to map screenshots to scenes with proper durations
    # Scene 1: screenshots 000-003 (4 screenshots)
    # Scene 2: screenshots 004-006 (3 screenshots)
    # etc.
    # We distribute each scene's duration evenly across its screenshots

    screenshot_files = sorted(
        [f for f in os.listdir(SCREENSHOTS_DIR) if f.endswith(".png")]
    )
    print(f"Total screenshots: {len(screenshot_files)}")

    # Map screenshots to scenes
    # Scene screenshot counts (based on snap() calls):
    scene_snapshot_counts = [4, 3, 2, 3, 3, 2, 1, 9, 2, 1]  # total = 30
    assert sum(scene_snapshot_counts) == len(screenshot_files), (
        f"Screenshot count mismatch: {sum(scene_snapshot_counts)} vs {len(screenshot_files)}"
    )

    # Create FFmpeg concat file
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        idx = 0
        for scene_i, count in enumerate(scene_snapshot_counts):
            dur_per_snap = scene_durations[scene_i] / count
            for _ in range(count):
                snap_path = SCREENSHOTS_DIR / screenshot_files[idx]
                f.write(f"file '{snap_path}'\n")
                f.write(f"duration {dur_per_snap:.3f}\n")
                idx += 1

    print(f"\nConcat file created with {len(screenshot_files)} entries")

    # Build video from screenshots
    video_no_audio = OUTPUT_DIR / "demo_no_audio.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-preset", "medium",
        "-crf", "18",
        str(video_no_audio),
    ]
    print(f"\nRunning: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, capture_output=True)

    # Overlay audio
    final_video = PROJECT_DIR / "Crypto_Analysis_AI_Demo.mp4"
    cmd2 = [
        "ffmpeg",
        "-y",
        "-i", str(video_no_audio),
        "-i", str(combined_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(final_video),
    ]
    print(f"\nRunning: {' '.join(cmd2)}")
    subprocess.run(cmd2, check=True, capture_output=True)

    print(f"\n=== FINAL VIDEO: {final_video} ===")
    size_mb = final_video.stat().st_size / (1024 * 1024)
    print(f"Size: {size_mb:.1f} MB")

    return final_video


def main():
    start = time.time()

    ensure_dir(OUTPUT_DIR)
    ensure_dir(AUDIO_DIR)
    ensure_dir(SCREENSHOTS_DIR)

    # Step 1: Generate audio
    audio_duration = generate_audio()

    # Step 2: Launch Playwright and take screenshots
    print("\n=== Launching Playwright ===")
    viewport = {"width": 1440, "height": 900}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = browser.new_context(
            viewport=viewport,
            device_scale_factor=2,
        )
        num_shots = take_screenshots(context, viewport)
        context.close()
        browser.close()

    # Step 3: Build video
    final = create_video_from_screenshots(num_shots)

    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed:.0f}s")
    print(f"Output: {final}")


if __name__ == "__main__":
    main()
