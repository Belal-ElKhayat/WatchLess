import os
import json
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

load_dotenv()
MODEL_OPTIONS = {
    "flash-lite": {
        "id": "gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash-Lite",
    },
    "flash": {
        "id": "gemini-3.8-flash",
        "name": "Gemini 3.8 Flash",
    },
}
DEFAULT_MODEL = "flash-lite"
WEB_DIR = Path(__file__).parent

def extract_video_id(url):
    """
    Extracts the Id from different Url formats of yt ._.
    Example: https://youtu.be/dQw4w9WgXcQ --> dQw4w9WgXcQ 
    the short format : https://www.youtube.com/shorts/S7GruduLIUY
    """
    parsed = urlparse(url)
    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2] or None
        elif parsed.path.startswith(("/embed/", "/v/")):
            return parsed.path.split("/")[2]
    return None

def fetch_transcript_text(video_id):
    """
    Fetches the transcript chunks using youtube-transcript-api 
    and stitches them together into a single plain-text string.
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        transcript_list = fetched_transcript.to_raw_data()
        lines = []
        for chunk in transcript_list:
            text = chunk["text"].replace("\n", " ").strip()
            start = chunk.get("start")
            if start is not None:
                total_seconds = max(0, int(start))
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                timestamp = f"{hours:02}:{minutes:02}:{seconds:02}" if hours else f"{minutes:02}:{seconds:02}"
                lines.append(f"[{timestamp}] {text}")
            else:
                lines.append(text)
        return "\n".join(lines)
    except Exception as e:
        raise RuntimeError(f"Could not retrieve a transcript for this video: {e}") from e

def summarize_with_gemini(transcript_text, model=MODEL_OPTIONS[DEFAULT_MODEL]["id"]):
    """
    Sends the timestamped transcript to Gemini and returns structured summary data.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to your .env file and restart the app.")

    client = genai.Client(api_key=api_key)
    prompt = f"""
    You are an expert video research assistant. Use only the transcript below.
    Return one JSON object with exactly these fields:
    - "tldr": one or two concise sentences with the main idea.
    - "key_points": 4 to 6 objects, each with "text" and "timestamp".
      Use an exact [MM:SS] or [HH:MM:SS] transcript timestamp for the moment
      that supports the point. Set timestamp to null only when no timestamp exists.
    - "topics": 3 to 5 short topic tags.
    - "quotes": zero to two short, exact verbatim quotes from the transcript.
      Do not invent, paraphrase, or clean up quotes.
    Do not include markdown fences or any text outside the JSON object.

    Transcript:
    {transcript_text}
    """
    
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty summary. Please try again.")
    try:
        summary = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise RuntimeError("Gemini returned an unreadable summary. Please try again.") from e

    if not isinstance(summary, dict):
        raise RuntimeError("Gemini returned a summary in an unexpected format.")
    if not isinstance(summary.get("tldr"), str) or not summary["tldr"].strip():
        raise RuntimeError("Gemini returned a summary without a TL;DR.")
    if not isinstance(summary.get("key_points"), list) or not 4 <= len(summary["key_points"]) <= 6 or not all(
        isinstance(point, dict)
        and isinstance(point.get("text"), str)
        and point["text"].strip()
        and (point.get("timestamp") is None or isinstance(point.get("timestamp"), str))
        for point in summary["key_points"]
    ):
        raise RuntimeError("Gemini must return 4 to 6 valid key points.")
    if not isinstance(summary.get("topics"), list) or not 3 <= len(summary["topics"]) <= 5 or not all(
        isinstance(topic, str) and topic.strip() for topic in summary["topics"]
    ):
        raise RuntimeError("Gemini must return 3 to 5 valid topic tags.")
    if not isinstance(summary.get("quotes"), list) or len(summary["quotes"]) > 2 or not all(
        isinstance(quote, str) and quote.strip() for quote in summary["quotes"]
    ):
        raise RuntimeError("Gemini returned quotes in an unexpected format.")
    return summary

def summary_to_markdown(summary):
    if isinstance(summary, str):
        return summary

    lines = ["## TL;DR", summary["tldr"], "", "## Key points"]
    for point in summary["key_points"]:
        timestamp = point.get("timestamp")
        prefix = f"[{timestamp}] " if timestamp else ""
        lines.append(f"- {prefix}{point['text']}")
    lines.extend(["", "## Topics", ", ".join(summary["topics"])])
    if summary["quotes"]:
        lines.extend(["", "## Notable quotes"])
        lines.extend(f"> {quote}" for quote in summary["quotes"])
    return "\n".join(lines)

class SummarizerHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return

        page = WEB_DIR / "index.html"
        try:
            body = page.read_bytes()
        except OSError:
            self.send_error(500, "Frontend file index.html could not be read.")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/summarize":
            self.send_json(404, {"error": "Endpoint not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 16_384:
                self.send_json(413, {"error": "Request must contain a YouTube URL."})
                return
            payload = json.loads(self.rfile.read(content_length))
            url = payload.get("url") if isinstance(payload, dict) else None
            if not isinstance(url, str):
                self.send_json(400, {"error": "Enter a valid YouTube video URL."})
                return
            model_key = payload.get("model", DEFAULT_MODEL)
            if not isinstance(model_key, str) or model_key not in MODEL_OPTIONS:
                self.send_json(400, {"error": "Choose one of the available models."})
                return

            url = url.strip()
            video_id = extract_video_id(url)
            if not video_id:
                self.send_json(400, {"error": "Enter a valid YouTube video URL."})
                return

            transcript = fetch_transcript_text(video_id)
            if not transcript:
                self.send_json(422, {"error": "This video does not have an available transcript."})
                return

            model = MODEL_OPTIONS[model_key]
            summary = summarize_with_gemini(transcript, model["id"])
            self.send_json(
                200,
                {
                    "summary": summary,
                    "video_id": video_id,
                    "model": model["name"],
                },
            )
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(400, {"error": "Request body must be valid JSON."})
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))

def run_web_app(host="127.0.0.1", port=8000):
    server = ThreadingHTTPServer((host, port), SummarizerHandler)
    print(f"YouTube Summarizer is running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server...")
    finally:
        server.server_close()

def main():
    parser = argparse.ArgumentParser(description="YouTube transcript summarizer")
    parser.add_argument("--cli", action="store_true", help="use the original command-line interface")
    args = parser.parse_args()
    if not args.cli:
        run_web_app()
        return

    print("=== YouTube Transcript Summarizer ===")
    url = input("Paste YouTube Video URL: ").strip()
    
    video_id = extract_video_id(url)
    if not video_id:
        print("Invalid YouTube URL. Please check and try again.")
        return

    print(f"Extracted Video ID: {video_id}")
    print("Fetching transcript...")
    
    try:
        transcript_text = fetch_transcript_text(video_id)
    except RuntimeError as e:
        print(e)
        return
    
    if transcript_text:
        print(f"Success! Fetched {len(transcript_text)} characters of text.")
        try:
            summary = summarize_with_gemini(transcript_text)
        except Exception as e:
            print(f"Could not generate summary: {e}")
            return
        
        print("\n" + "="*40)
        print("SUMMARY RESULTS:")
        print("="*40)
        print(summary_to_markdown(summary))
        
        # Optional: Save summary to a local markdown file
        filename = f"summary_{video_id}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(summary_to_markdown(summary))
        print(f"\n📁 Summary successfully saved to {filename}")

if __name__ == "__main__":
    main()