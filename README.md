<div align="center">

# WatchLess

**Paste a YouTube link. Get the point.**

Turns a video's transcript into a clean, structured summary — a TL;DR, key points, topic tags, and notable quotes — powered by Google's Gemini API.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_API-4285F4?style=flat-square&logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-34d399?style=flat-square)

<img src="docs/photo.png" width="100%" alt="WatchLess screenshot" />

</div>

<br/>

## What it does

Paste a YouTube video URL, and WatchLess fetches its transcript and sends it to Gemini, which returns a structured summary:

- **TL;DR** — the video in a sentence or two
- **Key points** — the main ideas, broken down
- **Topic tags** — what the video is about, at a glance
- **Notable quotes** — a few lines worth pulling out
- **Timestamps** — when the transcript includes timing data, key points link back to the moment in the video

## Requirements

- Python
- A Google Gemini API key ([get one here](https://aistudio.google.com/))
- A YouTube video with an available transcript

## Setup

1. Clone or download this repo, then open a terminal in the project folder.

2. Install dependencies:
   ```powershell
   python -m pip install python-dotenv youtube-transcript-api google-genai
   ```

3. Create a `.env` file in the project folder (copy `.env.example` and rename it):
   ```dotenv
   GEMINI_API_KEY=your_api_key_here
   ```
   **Keep this key private.** Never commit `.env` or paste your key into `index.html`.

## Run the web app

```powershell
python summarizer.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Paste a YouTube video URL, choose a model, and select **Summarize video**. Keep the terminal open while using the app; press **Ctrl+C** there to stop the server.

## Models

| Picker option | Gemini model |
| --- | --- |
| Free tier · Flash-Lite | `gemini-3.5-flash-lite` |
| Advanced · Flash 3.8 | `gemini-3.8-flash` |

Model access, quotas, and charges depend on your Google AI Studio account and billing tier. "Free tier" indicates free-tier availability, not unlimited usage or a guarantee that every account can use the model. Check [Google's Gemini API pricing](https://aistudio.google.com/docs/pricing) for current details.

## Command-line mode

For the original terminal-based workflow instead of the web page:

```powershell
python summarizer.py --cli
```

The CLI prints the summary and saves it as `summary_<video_id>.md` in the project folder.

<details>
<summary><b>API reference</b></summary>

The frontend sends requests to the Python server; the Gemini API key stays on the backend and is never exposed to the browser.

**`POST /api/summarize`**

Request body:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "model": "flash-lite"
}
```

`model` can be `flash-lite` or `flash`. If omitted, `flash-lite` is used.

A successful response contains `summary`, `video_id`, and the display name of the selected model. The structured summary has `tldr`, `key_points`, `topics`, and `quotes` fields.

</details>

## Troubleshooting

| Problem | Fix |
| --- | --- |
| The page can't connect | Make sure `python summarizer.py` is still running, then refresh the page. |
| Missing API key | Check that `.env` is in the project folder and contains `GEMINI_API_KEY=...`, then restart the server. |
| No transcript | Try a video that has captions or a transcript available. |
| Model unavailable, overloaded, or quota errors | Check your account's model access and quota in Google AI Studio, or try the other model option. |

## Privacy

Your Gemini API key stays in your own `.env` file and on your own machine. It is never sent anywhere except directly to Google's API, and it never touches the frontend code.

## Notes

- Summaries are AI-generated and may miss nuance or occasionally misrepresent something said in the video.
- The core logic (transcript fetching, summarization) was built in Python by hand, then AI was used to improve and extend the project further.

## License

MIT
