import yt_dlp
import os
import re
import glob
import time
import sys
import argparse

# Reconfigure stdout to use UTF-8
sys.stdout.reconfigure(encoding='utf-8')

parser = argparse.ArgumentParser(description="批次下載 YouTube 字幕；影片沒有字幕時改用 Whisper 轉錄")
parser.add_argument("urls", nargs="*", help="只處理這些網址（不給就讀 sensebar_ai_urls.txt）")
parser.add_argument("--out-dir", help="輸出資料夾（預設為專案的 subtitles/）")
parser.add_argument("--force-whisper", action="store_true", help="即使有字幕也改用 Whisper 轉錄（測試用）")
parser.add_argument("--whisper-model", default="turbo", help="Whisper 模型名稱（預設 turbo）")
args = parser.parse_args()

# Paths
target_dir = r"c:\2026AI_agent\AI_AgentEP01_用 Agent 來學習 Agent"
if not os.path.exists(target_dir):
    target_dir = os.path.dirname(os.path.abspath(__file__))

urls_file = os.path.join(target_dir, "sensebar_ai_urls.txt")
sub_dir = args.out_dir or os.path.join(target_dir, "subtitles")
os.makedirs(sub_dir, exist_ok=True)

# Read URLs
if args.urls:
    urls = args.urls
else:
    with open(urls_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

def make_safe_filename(title):
    # Remove characters that are illegal in Windows filenames
    # Also remove any non-ascii or special symbols if they could cause path issues,
    # but keeping Chinese/Unicode is fine.
    safe = re.sub(r'[\\/*?:"<>|]', "_", title)
    # Strip leading/trailing spaces/dots
    safe = safe.strip().strip('.')
    return safe

def parse_vtt(vtt_path):
    with open(vtt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    cleaned = []
    last_line = ""
    for line in lines:
        line = line.strip()
        # Skip VTT headers and timestamp lines
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:") or "-->" in line:
            continue
        # Remove tags
        line = re.sub(r'<[^>]+>', '', line)
        line = line.strip()
        if not line:
            continue
        # Deduplicate consecutive identical lines
        if line == last_line:
            continue
        cleaned.append(line)
        last_line = line
        
    return "\n".join(cleaned)

# Whisper 後備轉錄：whisper / opencc 只在真的需要轉錄時才 import，
# 沒裝的電腦照樣能跑一般字幕下載
_whisper_model = None

WHISPER_PROMPT = "以下是繁體中文的教學影片逐字稿，有標點符號。內容會提到 Claude Code、Codex、AntiGravity、OpenCode、Agent、MCP、Skill、GitHub、Obsidian、NotebookLM、Firebase、Supabase、Gemini。"

# Whisper 對本頻道固定會聽錯的專有名詞，轉錄後直接更正
WHISPER_FIXES = {
    "Cloud Code": "Claude Code",
    "Superbase": "Supabase",
    "Super Bass": "Supabase",
    "Fire Bass": "Firebase",
}

def transcribe_with_whisper(url):
    global _whisper_model
    import whisper
    import opencc

    # 下載音軌（檔名沿用 temp_sub.* 前綴，交給既有的暫存清理與 .gitignore）
    audio_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(sub_dir, 'temp_sub.audio.%(ext)s'),
        'quiet': True,
        'noprogress': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(audio_opts) as ydl:
        ydl.extract_info(url, download=True)
    audio_files = glob.glob(os.path.join(sub_dir, "temp_sub.audio.*"))
    if not audio_files:
        raise RuntimeError("音軌下載失敗")

    if _whisper_model is None:
        print(f"  Loading Whisper model: {args.whisper_model}...")
        _whisper_model = whisper.load_model(args.whisper_model)

    # 提示詞只帶在第一個視窗；試過 carry_initial_prompt=True 會漏掉整段內容，不要開
    result = _whisper_model.transcribe(audio_files[0], language="zh", initial_prompt=WHISPER_PROMPT)

    # Whisper 中文常輸出簡體，統一轉成台灣正體用語
    converter = opencc.OpenCC('s2twp')
    cleaned = []
    last_line = ""
    for seg in result["segments"]:
        line = converter.convert(seg["text"].strip())
        for wrong, right in WHISPER_FIXES.items():
            line = line.replace(wrong, right)
        # 與字幕清洗相同的連續行去重（也能壓掉 Whisper 偶發的重複幻覺）
        if not line or line == last_line:
            continue
        cleaned.append(line)
        last_line = line
    return "\n".join(cleaned)

# yt-dlp configurations
ydl_opts = {
    'skip_download': True,
    'writesubtitles': True,
    'writeautomaticsubtitles': True,
    'subtitleslangs': ['zh-Hant', 'zh-TW', 'zh', 'en'],
    'subtitlesformat': 'vtt',
    'outtmpl': os.path.join(sub_dir, 'temp_sub.%(ext)s'),
    'quiet': True,
    'no_warnings': True,
}

print(f"Total videos to process: {len(urls)}")

for idx, url in enumerate(urls):
    print(f"[{idx+1}/{len(urls)}] Fetching metadata for {url}...")
    
    # 1. Get Title first to check if we already have the md file (resumable)
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get('title', f"video_{idx+1}")
    except Exception as e:
        print(f"  Error fetching metadata for {url}: {e}")
        continue

    safe_title = make_safe_filename(title)
    out_md_path = os.path.join(sub_dir, f"{safe_title}.md")
    
    if os.path.exists(out_md_path):
        print(f"  [Skip] Already exists: {safe_title}.md")
        continue

    # 2. Clean up old temp files
    for f in glob.glob(os.path.join(sub_dir, "temp_sub.*")):
        try:
            os.remove(f)
        except:
            pass

    # 3. Download subtitles
    print(f"  Downloading subtitles for: {title}...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
            
        sub_files = glob.glob(os.path.join(sub_dir, "temp_sub.*.vtt"))
        source_note = ""

        if not sub_files or args.force_whisper:
            print("  No subtitles found, transcribing with Whisper..." if not sub_files else "  Forced Whisper transcription...")
            # 轉錄失敗（多半是 403 之類的暫時性錯誤）不寫佔位檔，交給外層 except 並照常清暫存，下次執行會重試
            cleaned_text = transcribe_with_whisper(url)
            source_note = f"- 字幕來源: Whisper 轉錄（{args.whisper_model}），非官方字幕\n\n"
        else:
            # Parse and save
            sub_file = sub_files[0]
            cleaned_text = parse_vtt(sub_file)

        md_content = f"# {title}\n\n"
        md_content += f"- 影片網址: {url}\n\n"
        md_content += source_note
        md_content += "---\n\n"
        md_content += cleaned_text + "\n"
        
        with open(out_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"  [Success] Saved to: {safe_title}.md")
        
    except Exception as e:
        print(f"  Error downloading subtitles for {title}: {e}")
        
    # Clean up temp files
    for f in glob.glob(os.path.join(sub_dir, "temp_sub.*")):
        try:
            os.remove(f)
        except:
            pass

    # Polite sleep to avoid rate limits
    time.sleep(2)

print("\nAll tasks completed!")
