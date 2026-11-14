# WatchLess

WatchLess turns a YouTube video transcript into a concise, structured summary. Paste a video link to get a TL;DR, key points, topic tags, and notable quotes. When captions include timing data, key points link to the relevant moment in the video.

## Requirements

- Python
- A Google Gemini API key
- A YouTube video with an available transcript

## Setup

Open PowerShell in the project folder:

```powershell
cd C:\Users\belal\youtube-summarizer
```

Install the Python dependencies:

```powershell
python -m pip install python-dotenv youtube-transcript-api google-genai
```

Create a `.env` file in the project folder and add your Gemini API key:

```dotenv
GEMINI_API_KEY=your_api_key_here
```

Keep the API key private. Do not put it in `index.html` or share it publicly.

## Run the web app

```powershell
python summarizer.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Paste a YouTube video URL, choose a model, and select **Summarize video**. Keep the terminal open while using the app; press **Ctrl+C** there to stop the server.

## Models

The model picker offers:

| Picker option | Gemini model |
| --- | --- |
| Free tier · Flash-Lite | `gemini-3.5-flash-lite` |
| Advanced · Flash 3.8 | `gemini-3.8-flash` |

Model access, quotas, and charges depend on your Google AI Studio account and billing tier. “Free tier” indicates free-tier availability, not unlimited usage or a guarantee that every account can use the model. Check [Google’s Gemini API pricing](https://aistudio.google.com/docs/pricing) for current details.

## Command-line mode

To use the original terminal-based workflow instead of the web page:

```powershell
python summarizer.py --cli
```

The CLI prints the summary and saves it as `summary_<video_id>.md` in the project folder.

## API

The frontend sends requests to the Python server; the Gemini API key remains on the backend.

`POST /api/summarize`

Request body:

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "model": "flash-lite"
}
```

`model` can be `flash-lite` or `flash`; if omitted, `flash-lite` is used. A successful response contains `summary`, `video_id`, and the display name of the selected model. The structured summary has `tldr`, `key_points`, `topics`, and `quotes` fields.

## Troubleshooting

- **The page cannot connect:** Make sure `python summarizer.py` is still running, then refresh the page.
- **Missing API key:** Check that `.env` is in the project folder and contains `GEMINI_API_KEY=...`; restart the server after changing it.
- **No transcript:** Try a video with captions/transcripts available.
- **Model unavailable, overloaded, or quota errors:** Check your account’s model access and quota in Google AI Studio, or try the other model option.
