"""
Focus Flow - Pilot Video Assembler
Gate 2: Intro + Step 1 (first ~27 seconds)
Built for MoviePy 2.2.1 API
"""
import os
from moviepy import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip

# ================================================================================
# CONFIGURATION & ASSET PATHS
# ================================================================================
WORKSPACE_DIR = r"C:\Users\Cherry\BackPocket_MVP"
ASSETS_DIR = os.path.join(WORKSPACE_DIR, "03 video free google tools")
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "video_output")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# MAIN MEDIA
INTRO_AUDIO = os.path.join(ASSETS_DIR, "01 Narration audio", "Intro.mp3")
INTRO_VIDEO = os.path.join(ASSETS_DIR, "02 Avatar Talking Head", "Intro1.mp4")

# 3D GENERATED B-ROLL ICONS (absolute paths)
GOOGLE_ICON = r"C:\Users\Cherry\.gemini\antigravity\brain\4159b659-0ad9-45f4-8587-9906dd8eb17a\google_ai_3d_icon_1775282018204.png"
PROFIT_ICON = r"C:\Users\Cherry\.gemini\antigravity\brain\4159b659-0ad9-45f4-8587-9906dd8eb17a\profit_growth_3d_icon_1775282031556.png"
TIME_ICON   = r"C:\Users\Cherry\.gemini\antigravity\brain\4159b659-0ad9-45f4-8587-9906dd8eb17a\stopwatch_24h_3d_icon_1775282047067.png"

# ================================================================================
# PILOT ASSEMBLY - INTRO (27 seconds)
# ================================================================================

def make_icon_overlay(path, start, duration, position, height):
    """Helper: load a PNG icon, resize it, set timing and position."""
    return (ImageClip(path)
            .resized(height=height)
            .with_start(start)
            .with_duration(duration)
            .with_position(position))


def create_pilot_intro():
    print("--- Starting Focus Flow Pilot Assembly ---")

    # ── 1. VALIDATE FILES EXIST ──────────────────────────────────────────────
    for label, path in [("Intro Video", INTRO_VIDEO), ("Intro Audio", INTRO_AUDIO),
                         ("Google Icon", GOOGLE_ICON), ("Profit Icon", PROFIT_ICON),
                         ("Time Icon", TIME_ICON)]:
        if not os.path.exists(path):
            print(f"  [MISSING] {label}: {path}")
            return
        print(f"  [OK]      {label}")

    # ── 2. LOAD MAIN CLIP (27 seconds) ───────────────────────────────────────
    print("\nLoading main video and audio...")
    main_clip = VideoFileClip(INTRO_VIDEO).subclipped(0, 27)
    audio     = AudioFileClip(INTRO_AUDIO).subclipped(0, 27)
    main_clip = main_clip.with_audio(audio)
    print(f"  Video: {main_clip.duration:.1f}s  |  Audio: {audio.duration:.1f}s")

    # ── 3. B-ROLL ICON OVERLAYS ──────────────────────────────────────────────
    # ICON 1: Google AI logo — appears at 0:02 (when "FREE Google AI" is spoken)
    google_overlay = make_icon_overlay(GOOGLE_ICON, start=2, duration=4,
                                       position=("center", "center"), height=380)

    # ICON 2: Profit chart  — appears at 0:08 (when "profitable business" is spoken)
    profit_overlay = make_icon_overlay(PROFIT_ICON, start=8, duration=3,
                                        position=("right", "center"), height=320)

    # ICON 3: 24H stopwatch — appears at 0:15 (when "24 hours" is spoken)
    time_overlay   = make_icon_overlay(TIME_ICON, start=15, duration=4,
                                        position=("left", "center"), height=320)

    # ── 4. ASSEMBLE COMPOSITE ─────────────────────────────────────────────────
    print("\nCompositing layers...")
    final_video = CompositeVideoClip([
        main_clip,
        google_overlay,
        profit_overlay,
        time_overlay,
    ])

    # ── 5. EXPORT ─────────────────────────────────────────────────────────────
    output_path = os.path.join(OUTPUT_DIR, "FocusFlow_Pilot_Intro.mp4")
    print(f"\nExporting -> {output_path}")
    final_video.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",
        logger="bar"
    )
    print(f"\n✅  DONE! Open: {output_path}")


if __name__ == "__main__":
    create_pilot_intro()
