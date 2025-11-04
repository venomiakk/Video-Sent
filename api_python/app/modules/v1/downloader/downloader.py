from pathlib import Path
from typing import Dict, Optional, Tuple

from pydantic import HttpUrl
import yt_dlp
from app.core.exceptions import DownloadError




def download_audio(
	url: HttpUrl,
	filename_hash: str,
	*,
	out_dir: Optional[Path] = None,
	format: str = "bestaudio/best",
	audio_codec: Optional[str] = "wav",
	sample_rate: Optional[int] = 16000,
	channels: Optional[int] = 1,
	bitrate: Optional[str] = None,
	force: bool = False,
	ytdlp_opts: Optional[Dict] = None,
) -> Tuple[str, Path, Optional[str]]:
	"""
	Download audio from a YouTube URL and save it into `app/resources`.

	Parameters
	- url: video URL to download
	- out_dir: directory to save the file (defaults to app/resources)
	- filename_hash: optional precomputed filename base; if not provided we'll hash the url
	- format: yt-dlp format selector (defaults to 'bestaudio/best')
	- audio_codec: output audio codec/extension (e.g. 'mp3', 'wav', 'm4a')
	- sample_rate: target sample rate in Hz (None to leave as-is)
	- channels: number of audio channels (1 mono, 2 stereo)
	- bitrate: audio bitrate string like '192k' (None to use defaults)
	- force: overwrite existing file if True
	- ytdlp_opts: extra options passed to yt_dlp

	Returns (filename_hash, path_to_file, title)

	Raises RuntimeError on failure.

	Usage examples (presets):
	- Whisper-ready (16k mono WAV): sample_rate=16000, audio_codec='wav', channels=1
	- Azure-ready (16k or 8k WAV/PCM): sample_rate=16000, audio_codec='wav', channels=1
	"""

	url = str(url) 
	# compute out_dir
	project_root = Path(__file__).resolve().parents[3]  # app/modules/v1/downloader -> app
	default_out = project_root / "resources"
	out_dir = Path(out_dir) if out_dir else default_out
	out_dir.mkdir(parents=True, exist_ok=True)

	# build filename
	ext = (audio_codec or "mp3").lower()
	out_path = out_dir / f"{filename_hash}.{ext}"

	if out_path.exists() and not force:
		title = None
		try:
			# ufetch metadata only
			with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
				meta = ydl.extract_info(url, download=False)
				title = meta.get("title") if isinstance(meta, dict) else None
		except Exception:
			title = None

		return str(filename_hash), out_path, title


	ytdlp_opts = dict(ytdlp_opts or {})
	ytdlp_opts.update({
		"format": format,
		"outtmpl": str(out_path.with_suffix(".%(ext)s")),
		"noplaylist": True,
		# YouTube bypass options
		"extractor_args": {"youtube": {"player_client": ["android", "web"]}},
		"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		# extract audio options
		"postprocessors": [
			{
				"key": "FFmpegExtractAudio",
				"preferredcodec": audio_codec,
				# preferredquality accepts a number for some codecs; we pass bitrate if set
				"preferredquality": bitrate if bitrate else "192",
			},
		],
	})

	# If we need to force channels/sample rate, add an FFmpegPostProcessor later using `postprocessor_args`.
	pp_args = []
	if sample_rate:
		pp_args += ["-ar", str(sample_rate)]
	if channels:
		pp_args += ["-ac", str(channels)]
	if pp_args:
		# postprocessor_args to pass to ffmpeg
		ytdlp_opts.setdefault("postprocessor_args", [])
		ytdlp_opts["postprocessor_args"] += pp_args

	try:
		with yt_dlp.YoutubeDL(ytdlp_opts) as ydl:
			info = ydl.extract_info(url, download=True)
			matches = list(out_dir.glob(f"{filename_hash}.*"))
			if matches:
				final_path = max(matches, key=lambda p: p.stat().st_mtime)
			else:
				final_path = out_path

			title = info.get("title") if isinstance(info, dict) else None
			return str(filename_hash), final_path, title
	except Exception as exc:
		raise DownloadError(f"Failed to download audio for {url}: {exc}") from exc


if __name__ == "__main__":
    test_url = "https://www.youtube.com/shorts/c7SRzIUjVYw"
    filename_hash, path, info = download_audio(
        test_url,
        sample_rate=16000,
        audio_codec="wav",
        channels=1,
    )
    print(f"Downloaded to: {path}")
    print(f"Base: {filename_hash}")