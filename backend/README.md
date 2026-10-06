# GyanDrishti — Speech Engine (Milestone 1)

> **Offline Multilingual Speech Foundation for Classroom Intelligence**  
> Supports: English (`en`), Hindi (`hi`), Bengali (`bn`), and code-switched classroom lectures.  
> Target Hardware: Apple Silicon (MacBook Air M2, 8 GB RAM, macOS) and portable Linux devices.  
> **100% Offline | Zero-Cost | Local Audio & Transcripts**

---

## 1. What the Speech Engine Does

The GyanDrishti Speech Engine is the foundational audio perception layer for the GyanDrishti Multimodal Classroom Intelligence system. It takes raw lecture audio (from local recordings or direct microphone capture), removes classroom silence, and generates **structured, timestamped source transcripts** preserving original spoken languages and Indic scripts (Devanagari for Hindi, Bengali script for Bangla, and Latin script for English).

```
RAW AUDIO (Mic / WAV) ──> VAD (Silence Filtering) ──> LOCAL ASR (CTranslate2 INT8) ──> RAW TRANSCRIPT (JSON Source Data)
```

**Key Principle**: The raw transcript is **SOURCE DATA**. It is never translated, altered, or overwritten during ASR. Higher-level intelligence (lecture notes, summaries, Q&A, and board fusion) will be built as separate layers in subsequent milestones.

---

## 2. Why the Selected ASR Model Was Chosen

We selected **`faster-whisper`** (CTranslate2-backed Whisper) with the **`small` multilingual model** as the default engine:

1. **Native CTranslate2 Inference Engine**: CTranslate2 provides a custom C++ inference engine that applies 8-bit integer quantization (`int8`) with ARM NEON SIMD vector optimizations on Apple Silicon (M1/M2/M3).
2. **Superior Indic Script Accuracy**: While `tiny` and `base` struggle severely with Hindi and Bengali script fidelity, the `small` model (244M parameters) delivers high-accuracy phoneme-to-grapheme mapping for Devanagari and Bengali scripts.
3. **Low Latency & High RTF**: Processes 1 minute of audio in ~4–8 seconds on an M2 chip (Real-Time Factor: **0.06 – 0.15**).
4. **Memory Safety on 8 GB RAM**: Requires only **~850 MB – 1.1 GB of RAM**, safely operating alongside macOS system services without triggering memory swapping or background process kills.
5. **No Cloud Dependency**: Zero external API calls, zero telemetry, zero data egress.

### Model Tradeoff Comparison

| Model | Disk Size | RAM Footprint | Apple Silicon M2 RTF | Indic Script Accuracy | Status in GyanDrishti |
|---|---|---|---|---|---|
| `tiny` | ~75 MB | ~250 MB | ~0.04 | Low (frequent script garbling) | Supported (low memory) |
| `base` | ~145 MB | ~450 MB | ~0.08 | Moderate (acceptable for simple speech) | Supported (ultra-lightweight) |
| **`small`** | **~485 MB** | **~900 MB** | **~0.12** | **Strong (accurate Devanagari & Bengali)** | **RECOMMENDED DEFAULT** |
| `medium` | ~1.53 GB | ~2.2 GB | ~0.35 | High | Supported (for 16GB+ RAM) |
| `large-v3-turbo` | ~1.62 GB | ~2.5 GB | ~0.42 | State-of-the-art | Supported (for 16GB+ RAM) |

---

## 3. Supported Languages

- **English (`en`)**: Lectures, technical terminology, mathematical notation.
- **Hindi (`hi`)**: Devanagari script preservation (e.g. *अब हम Faraday's law के बारे में पढ़ेंगे।*).
- **Bengali (`bn`)**: Bengali script preservation (e.g. *এখানে আমরা দেখছি যে magnetic flux পরিবর্তন হচ্ছে।*).
- **Multilingual Code-Switching**:
  - Hindi + English (Hinglish): *Ab is equation ko differentiate karne ke baad hum EMF calculate karenge.*
  - Bengali + English (Banglish): *এই equation-এর derivative নিলে we get the induced EMF.*
  - Bengali + Hindi + English (Trilingual): *এখানে basically আমরা देख सकते हैं कि the current is increasing.*

---

## 4. Code-Switching & Script Limitations

1. **Intra-Word Code-Switching**: Morphological agglutination common in Indian languages (e.g. English noun + Bengali inflection: *flux-er*, *equation-ta*) may be transcribed phonetically in Bengali script (ফ্লাক্সের, ইকুয়েশনটা) or in Latin script (`flux-er`). Both are preserved as-is.
2. **Segment-Level Honesty**: Whisper does not provide calibrated word-level language identification tokens. GyanDrishti detects languages at the segment level using script analysis and lexical cues, marking segments honestly (e.g. `["bn", "en"]`) rather than fabricating false word-level precision.
3. **Transliteration Nuances**: Hinglish/Banglish spoken in rapid classroom delivery is preserved in the script emitted by the ASR decoder. Downstream LLM reasoning (Milestone 5) handles phonetic normalization.

---

## 5. Model Specifications

- **Default Model**: `small` multilingual
- **Disk Storage**: ~485 MB in `backend/models/small/`
- **RAM Footprint**: ~900 MB during active inference
- **Quantization**: `int8` (CTranslate2 NEON optimized)

---

## 6. Apple Silicon Considerations

- The engine automatically detects Apple Silicon (`darwin` on `arm64`).
- CTranslate2 uses Apple Accelerate / ARM NEON vector instructions for matrix multiplication.
- Uses `device="cpu"` with `compute_type="int8"`. This avoids PyTorch MPS float32 memory bloat while delivering near-instant execution.
- Configured with 4 CPU worker threads, perfectly balancing M2 performance and efficiency cores.

---

## 7. Installation

### Prerequisites
- macOS 12+ (Apple Silicon M1/M2/M3) or Linux (x86_64 / aarch64)
- Python 3.10+ (tested on Python 3.13)
- `ffmpeg` (installed via `brew install ffmpeg`)

### Step-by-Step Setup

1. **Navigate to the backend directory**:
   ```bash
   cd /path/to/GyanDrishti/backend
   ```

2. **Create and activate the isolated virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 8. Model Download (One-Time Setup)

Download the recommended `small` model weights into `backend/models/`:

```bash
# Option A: Using the CLI
python -m speech_engine download --model small

# Option B: Using the standalone download script
python scripts/download_model.py --model small
```

To inspect downloaded models and specifications:
```bash
python -m speech_engine models
```

---

## 9. 100% Offline Usage Verification

Once the model weights are stored in `backend/models/`, **no network connection is needed**.

### Offline Verification Procedure

1. **Disconnect Wi-Fi / disable network interfaces**:
   ```bash
   # On macOS via command line:
   networksetup -setairportpower en0 off
   # Or simply turn off Wi-Fi in macOS Control Center
   ```

2. **Run transcription with the `--offline` flag**:
   ```bash
   python -m speech_engine transcribe recordings/my_lecture.wav --offline
   ```

3. **Check network activity**:
   - The engine loads weights directly from `backend/models/small/`.
   - Transcription finishes successfully with zero packets sent or received.

---

## 10. macOS Microphone Permissions

When using `python -m speech_engine record`, macOS requires microphone permissions.

If you encounter:
```
PermissionError: Microphone access denied or audio device unavailable.
```

**Resolution**:
1. Open **System Settings** -> **Privacy & Security** -> **Microphone**.
2. Enable access for **Terminal** (or **iTerm**, **VS Code**, depending on your shell environment).
3. If still blocked, reset microphone permissions for Terminal:
   ```bash
   tccutil reset Microphone
   ```

To check detected input devices:
```bash
python -m speech_engine devices
```

---

## 11. CLI Usage Guide

All commands can be run via `python -m speech_engine` (with `PYTHONPATH=.` inside `backend/`):

### 1. Record from Microphone (30-second default test)
```bash
python -m speech_engine record --duration 30
```
- Initializes the microphone.
- Captures audio and saves it to `recordings/recording_<timestamp>.wav`.
- Runs VAD and ASR transcription.
- Prints timestamped segments and detected languages.
- Saves structured output to `recordings/transcript_<timestamp>.json`.

### 2. Transcribe an Audio File
```bash
python -m speech_engine transcribe path/to/lecture.wav
```
Supports WAV, MP3, and M4A. To specify model and output JSON:
```bash
python -m speech_engine transcribe path/to/lecture.wav --model small --output-json output.json
```

### 3. List Available Models & Status
```bash
python -m speech_engine models
```

### 4. List Microphones
```bash
python -m speech_engine devices
```

---

## 12. Structured JSON Output Format

The output schema strictly preserves source data and uses `null` for uncalibrated confidence:

```json
{
  "lecture_id": "physics_lecture_01",
  "audio_path": "/path/to/recordings/physics_lecture_01.wav",
  "duration": 18.54,
  "processing_time": 2.15,
  "real_time_factor": 0.116,
  "model_name": "small",
  "device": "cpu",
  "compute_type": "int8",
  "language_summary": [
    "bn",
    "en",
    "hi"
  ],
  "segments": [
    {
      "id": 1,
      "start": 0.0,
      "end": 4.82,
      "text": "Today we're going to study electromagnetic induction.",
      "language": [
        "en"
      ],
      "confidence": null,
      "words": null
    },
    {
      "id": 2,
      "start": 5.10,
      "end": 9.72,
      "text": "अब हम Faraday's law के बारे में पढ़ेंगे।",
      "language": [
        "en",
        "hi"
      ],
      "confidence": null,
      "words": null
    },
    {
      "id": 3,
      "start": 10.20,
      "end": 15.60,
      "text": "এখানে আমরা দেখছি যে magnetic flux পরিবর্তন হচ্ছে।",
      "language": [
        "bn",
        "en"
      ],
      "confidence": null,
      "words": null
    }
  ],
  "raw_text": "Today we're going to study electromagnetic induction. अब हम Faraday's law के बारे में पढ़ेंगे। এখানে আমরা দেখছি যে magnetic flux পরিবর্তন হচ্ছে।",
  "created_at": "2026-10-06T16:30:00.000000Z"
}
```

---

## 13. Benchmarking

Use `benchmarks/benchmark_asr.py` to evaluate performance, processing time, and Real-Time Factor (RTF):

```bash
# Benchmark all recordings in the recordings directory
python benchmarks/benchmark_asr.py --dir recordings/ --model small

# Or specify individual files
python benchmarks/benchmark_asr.py recordings/test1.wav recordings/test2.wav --model small
```

**Real-Time Factor Formula**:
$$\text{RTF} = \frac{\text{Processing Time (s)}}{\text{Audio Duration (s)}}$$
- An RTF of `0.10` means 10 seconds of speech is transcribed in 1.0 second. Lower is faster.

---

## 14. Creating the Local Speech Evaluation Dataset

To evaluate your local deployment without committing private recordings to git, create a **2–3 minute audio test set** containing 9 targeted segments:

### Recommended Script for Evaluation Recording

1. **English Baseline (20s)**:
   > *"Good morning everyone. Today we are exploring Maxwell's equations and how time-varying electric and magnetic fields propagate as waves in free space."*
2. **Hindi Monolingual (20s)**:
   > *"अब हम विद्युत क्षेत्र और चुंबकीय क्षेत्र के मूल सिद्धांतों पर चर्चा करेंगे।"*
3. **Bengali Monolingual (20s)**:
   > *"এখানে আমরা দেখতে পাচ্ছি যে তড়িৎ প্রবাহ এবং চৌম্বক ক্ষেত্রের মধ্যে একটি গভীর সম্পর্ক রয়েছে।"*
4. **Hinglish Code-Switching (20s)**:
   > *"Ab is equation ko differentiate karne ke baad hum induced EMF calculate karenge, jo ki rate of change of flux ke barabar hota hai."*
5. **Banglish Code-Switching (20s)**:
   > *"Ekhane amra basically magnetic flux-er change-ta dekhchi, ar tar theke induced voltage derive korbo."*
6. **Bengali + English Mixed (20s)**:
   > *"এই equation-এর derivative নিলে we get the induced EMF, which opposes the original change."*
7. **Hindi + English Mixed (20s)**:
   > *"Is circuit ka total impedance calculate karne ke liye hume resistance aur reactance dono consider karna padega."*
8. **Trilingual Mixed (Bengali + Hindi + English) (20s)**:
   > *"এখানে basically আমরা देख सकते हैं कि the current is increasing exponentially over time."*
9. **Intentional Silence / Pauses (15s)**:
   > *(Silence for 5s)* *"Notice this curve."* *(Silence for 5s)* *"Any questions?"* *(Silence for 5s)*

### Recording the Evaluation Set
```bash
python -m speech_engine record --duration 180 --output-audio recordings/eval_suite_3min.wav
```
Then run the benchmark:
```bash
python benchmarks/benchmark_asr.py recordings/eval_suite_3min.wav --model small
```

---

## 15. Testing Suite

The test suite separates fast unit tests (with synthetic signals and mocked engines) from integration tests:

```bash
# Run all unit tests (completes in < 1 second, zero model download required)
pytest tests/ -v
```

Tests cover:
- `test_audio.py`: Loading, peak normalization, linear resampling, WAV export/import.
- `test_schema.py`: Pydantic validation, metric rounding, null confidence guarantee.
- `test_language.py`: Script detection (Devanagari, Bengali, Latin), Hinglish/Banglish token heuristics, trilingual code-switching.
- `test_vad.py`: Silence detection, speech bursts, interval padding.
- `test_asr.py`: Mock ASR execution, offline mode error enforcement, CLI parser validation.

---

## 16. Troubleshooting

1. **`ModuleNotFoundError: No module named 'speech_engine'`**:
   - Run commands with `PYTHONPATH=.` inside `backend/` or ensure `backend` is in your environment path:
     ```bash
     export PYTHONPATH="$(pwd)"
     ```
2. **`PortAudioError` / Microphone Unavailable**:
   - Check device ID with `python -m speech_engine devices`.
   - Pass the explicit ID: `python -m speech_engine record --device 0`.
3. **Memory Pressure on 8 GB RAM**:
   - If other heavy applications are open, use the `base` model:
     ```bash
     python -m speech_engine transcribe audio.wav --model base
     ```
   - `base` consumes only ~450 MB RAM compared to ~900 MB for `small`.
4. **MP3/M4A fails to load**:
   - Ensure FFmpeg is installed: `brew install ffmpeg`.
