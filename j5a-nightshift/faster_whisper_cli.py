#!/usr/bin/env python3
"""
faster-whisper CLI Wrapper
Provides OpenAI Whisper-compatible CLI interface using faster-whisper backend

Usage:
    faster_whisper_cli.py <audio_file> [options]

Compatible with OpenAI Whisper CLI arguments:
    --model MODEL          Model size (tiny, small, medium, large-v3, etc.)
    --language LANG        Language code (en, es, fr, etc.)
    --task TASK           Task type (transcribe or translate)
    --output_dir DIR      Output directory for transcripts
    --verbose BOOL        Enable verbose output (True/False)
    --output_format FMT   Output formats: txt, json, srt, vtt (comma-separated)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import warnings

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("ERROR: faster-whisper not installed. Install with: pip3 install faster-whisper", file=sys.stderr)
    sys.exit(1)


def format_timestamp(seconds: float, always_include_hours: bool = False, decimal_marker: str = '.') -> str:
    """Format seconds to SRT/VTT timestamp format"""
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds = milliseconds // 1_000
    milliseconds -= seconds * 1_000

    hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
    return f"{hours_marker}{minutes:02d}:{seconds:02d}{decimal_marker}{milliseconds:03d}"


def write_txt(transcript: str, output_path: Path):
    """Write plain text transcript"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(transcript.strip() + '\n')


def write_json(segments: List[Dict[str, Any]], output_path: Path, language: str, transcript: str):
    """Write JSON transcript with segments"""
    json_data = {
        "text": transcript.strip(),
        "segments": segments,
        "language": language
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)


def write_srt(segments: List[Dict[str, Any]], output_path: Path):
    """Write SRT subtitle file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, start=1):
            start = format_timestamp(segment['start'], always_include_hours=True, decimal_marker=',')
            end = format_timestamp(segment['end'], always_include_hours=True, decimal_marker=',')
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{segment['text'].strip()}\n\n")


def write_vtt(segments: List[Dict[str, Any]], output_path: Path):
    """Write VTT subtitle file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        for segment in segments:
            start = format_timestamp(segment['start'])
            end = format_timestamp(segment['end'])
            f.write(f"{start} --> {end}\n")
            f.write(f"{segment['text'].strip()}\n\n")


def transcribe_with_faster_whisper(
    audio_path: str,
    model: str = "tiny",
    language: str = "en",
    task: str = "transcribe",
    output_dir: str = ".",
    verbose: bool = False,
    output_formats: List[str] = None
):
    """
    Transcribe audio using faster-whisper

    Args:
        audio_path: Path to audio file
        model: Model size (tiny, small, medium, large-v3, etc.)
        language: Language code
        task: transcribe or translate
        output_dir: Output directory
        verbose: Show progress
        output_formats: List of output formats (txt, json, srt, vtt)
    """
    if output_formats is None:
        output_formats = ['txt', 'json', 'srt', 'vtt']

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    audio_file = Path(audio_path)
    basename = audio_file.stem

    if verbose:
        print(f"Loading faster-whisper model '{model}'...", file=sys.stderr)

    # Initialize faster-whisper model
    # Use CPU with int8 for memory efficiency (tiny model is small enough)
    model_instance = WhisperModel(
        model,
        device="cpu",
        compute_type="int8"
    )

    if verbose:
        print(f"Transcribing '{audio_path}'...", file=sys.stderr)

    # Transcribe
    segments_generator, info = model_instance.transcribe(
        audio_path,
        language=language,
        task=task,
        beam_size=5,
        vad_filter=True,  # Voice activity detection for better accuracy
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    # Collect segments
    segments = []
    full_transcript = []

    for segment in segments_generator:
        segment_data = {
            'id': segment.id,
            'seek': segment.seek,
            'start': segment.start,
            'end': segment.end,
            'text': segment.text,
            'tokens': segment.tokens,
            'temperature': segment.temperature,
            'avg_logprob': segment.avg_logprob,
            'compression_ratio': segment.compression_ratio,
            'no_speech_prob': segment.no_speech_prob
        }
        segments.append(segment_data)
        full_transcript.append(segment.text)

        if verbose:
            # Show progress similar to OpenAI Whisper
            progress = int((segment.end / info.duration) * 100) if info.duration > 0 else 0
            print(f"\rProgress: {progress}%", end='', file=sys.stderr)

    if verbose:
        print("\r", end='', file=sys.stderr)

    transcript_text = " ".join(full_transcript)

    # Write outputs
    if 'txt' in output_formats:
        write_txt(transcript_text, output_path / f"{basename}.txt")

    if 'json' in output_formats:
        write_json(segments, output_path / f"{basename}.json", info.language, transcript_text)

    if 'srt' in output_formats:
        write_srt(segments, output_path / f"{basename}.srt")

    if 'vtt' in output_formats:
        write_vtt(segments, output_path / f"{basename}.vtt")

    if verbose:
        print(f"✅ Transcription complete", file=sys.stderr)
        print(f"   Language: {info.language}", file=sys.stderr)
        print(f"   Duration: {info.duration:.2f}s", file=sys.stderr)
        print(f"   Segments: {len(segments)}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="faster-whisper CLI - OpenAI Whisper-compatible interface",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "audio",
        type=str,
        help="Audio file to transcribe"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="tiny",
        help="Model size: tiny, small, medium, large-v3, etc. (default: tiny)"
    )

    parser.add_argument(
        "--language",
        type=str,
        default="en",
        help="Language code (default: en)"
    )

    parser.add_argument(
        "--task",
        type=str,
        default="transcribe",
        choices=["transcribe", "translate"],
        help="Task: transcribe or translate (default: transcribe)"
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        default=".",
        help="Output directory (default: current directory)"
    )

    parser.add_argument(
        "--verbose",
        type=lambda x: x.lower() in ('true', '1', 'yes'),
        default=False,
        help="Show verbose output (default: False)"
    )

    parser.add_argument(
        "--output_format",
        type=str,
        default="txt,json,srt,vtt",
        help="Output formats (comma-separated): txt, json, srt, vtt (default: all)"
    )

    args = parser.parse_args()

    # Parse output formats
    output_formats = [fmt.strip() for fmt in args.output_format.split(',')]

    try:
        transcribe_with_faster_whisper(
            audio_path=args.audio,
            model=args.model,
            language=args.language,
            task=args.task,
            output_dir=args.output_dir,
            verbose=args.verbose,
            output_formats=output_formats
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
