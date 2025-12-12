# Podcast Processing Workflow: Transcription, Diarization, and AI Correction

**Version:** 1.0
**Last Updated:** 2025-12-11
**Target Audience:** AI Operators (Claude Code) - Context Refresh Reference
**Purpose:** Comprehensive technical reference for autonomous audio transcription and intelligence extraction workflows in the J5A ecosystem

---

## Part I: Architecture Overview

The podcast processing pipeline is a sophisticated **4-phase system** that divides work between deterministic mechanical operations (Night Shift) and AI-powered reasoning (Claude). This division respects J5A Constitutional Principles while optimizing resource usage and output quality.

### The Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ NIGHT SHIFT PIPELINE (Deterministic - No LLM)                   │
│ Heavy processing during off-hours (7pm-6am, weekends)           │
└─────────────────────────────────────────────────────────────────┘

Phase 1: DISCOVERY              Phase 2: ACQUISITION
  ↓                               ↓
Locate audio URL            Download to disk
(RSS parsing + fallback)      (with retries)
  ↓                               ↓
  └───────────────┬───────────────┘
                  ↓
          Phase 3: TRANSCRIPTION
          Whisper Large-v3 → Raw Transcript
          (No speaker labels)
                  ↓
          Queue to Claude

┌─────────────────────────────────────────────────────────────────┐
│ CLAUDE QUEUE (AI Reasoning - Contextual Analysis)               │
│ Complex analysis requiring reasoning and domain knowledge        │
└─────────────────────────────────────────────────────────────────┘

                  ↓
          Phase 4: INTELLIGENCE EXTRACTION
          (Claude Sonnet - Human operator processes)
                  ↓
      ┌─────────────────────────────────────┐
      │ Speaker Inference (Contextual)      │
      │ + Name Corrections                  │
      │ + Domain Vocabulary Enhancement     │
      │ + Entity Extraction with Reasoning  │
      └─────────────────────────────────────┘
                  ↓
          Structured Intelligence Outputs
          (JSON + Markdown reports)
```

### Design Philosophy

> **"Night Shift handles mechanical data acquisition; Claude handles complex analytical reasoning; Optimal division of labor by capability"**

**Why This Architecture Works:**

1. **Whisper is optimized for speed and cost**
   - Fast deterministic transcription
   - No API costs (local inference)
   - Suitable for unattended processing
   - Runs during off-hours without competing for resources

2. **Claude is optimized for reasoning**
   - Contextual understanding of domain
   - Speaker inference through conversation analysis
   - Name disambiguation and corrections
   - Evidence assessment and gap identification
   - Scheduled during optimal API times

3. **Resource efficiency**
   - Heavy GPU work (Whisper) during off-hours
   - API work (Claude) during business hours
   - Minimal resource contention
   - Both systems operating at peak efficiency

4. **Constitutional compliance**
   - **Principle 3 (System Viability):** Completion prioritized, graceful degradation
   - **Principle 4 (Resource Stewardship):** Off-hours processing respects thermal/memory limits
   - **Principle 7 (Autonomous Workflows):** Unattended overnight processing with safety gates
   - **Principle 2 (Transparency):** Full audit trail and decision logging

---

## Part II: Phase-by-Phase Implementation

### Phase 1: DISCOVERY (Deterministic - No LLM)

**Purpose:** Locate the audio file for a target episode

**Process:**
1. Parse podcast RSS feed using stdlib `xml.etree.ElementTree`
2. Match episode by number or title
3. Extract audio URL from `<enclosure>` tag
4. Fallback to web scraping if RSS fails (RWF + BeautifulSoup)

**Implementation File:** `/home/johnny5/Johny5Alive/j5a-nightshift/ops/fetchers/podcast_intelligence_pipeline.py`
**Implementation Lines:** 93-258

**Key Methods:**
- `discover_episode_audio_url()` - Main entry point
- `_parse_rss_feed()` - RSS parsing with episode number/title matching
- `_scrape_episode_page()` - Web scraping fallback with RWF

**Output:**
- Audio URL (direct link to MP3/M4A/M3U8)
- Episode metadata (title, date, duration, description)

**Example:**
```python
pipeline = PodcastIntelligencePipeline(
    rss_feed_url="https://feeds.megaphone.fm/weaponized"
)
audio_url, metadata = pipeline.discover_episode_audio_url(
    episode_number=91
)
# Returns: ("https://media.megaphone.fm/weaponized_ep91.mp3", {...})
```

---

### Phase 2: ACQUISITION (Deterministic - No LLM)

**Purpose:** Download audio file to local storage

**Process:**
1. Determine file format from URL
2. For MP3/M4A: Use `curl` with retry logic and redirect following
3. For HLS streams (.m3u8): Use `ffmpeg` to convert to continuous stream
4. Validate file was created and has content

**Implementation File:** `/home/johnny5/Johny5Alive/j5a-nightshift/ops/fetchers/podcast_intelligence_pipeline.py`
**Implementation Lines:** 260-318

**Key Features:**
- Retry logic: 5 retries with 3-second delays
- Timeout: 30 minutes per download
- HLS stream handling via ffmpeg
- File validation post-download

**Output:**
- Downloaded audio file at `ops/outputs/podcast_intelligence/audio/episode_91.mp3`
- File size validation

**Example:**
```bash
# Downloaded audio ready for transcription
-rw-r--r-- 1 user user 487M Dec 11 10:30 episode_91.mp3
```

---

### Phase 3: TRANSCRIPTION (Deterministic - No LLM)

**Purpose:** Convert audio to text using OpenAI Whisper

**Process:**
1. Run `whisper` command with Large model
2. Process audio with specified language (English)
3. Generate multiple output formats (TXT, JSON, SRT, etc.)
4. Save outputs with incremental checkpoints

**Implementation File:** `/home/johnny5/Johny5Alive/j5a-nightshift/ops/fetchers/podcast_intelligence_pipeline.py`
**Implementation Lines:** 320-377

**Key Details:**
- Model: `whisper large-v3` (12GB, ~1-2 hour processing time)
- **CRITICAL:** Produces raw transcript with NO speaker labels
- Incremental saves prevent data loss (Operation Gladio lesson)
- Timeout: 2 hours per episode
- Output formats: txt, json, srt, vtt

**Important Note on Diarization:**
- **Documentation claims:** Multi-speaker diarization is performed
- **Reality:** Whisper outputs provide NO speaker identification
- **Files are misleadingly labeled** as "diarized" (e.g., `episode_91_transcript_diarized.txt`) but contain undiarized transcripts
- **Actual speaker identification happens in Phase 4** through Claude's contextual reasoning

**Output Files:**
```
ops/outputs/podcast_intelligence/transcripts/
├── episode_91_transcript.txt       # Raw text with timestamps
├── episode_91_transcript.json       # Structured segments
└── [other formats]
```

**JSON Structure Example:**
```json
{
  "text": "[full transcript text]",
  "segments": [
    {
      "id": 0,
      "seek": 0,
      "start": 0.0,
      "end": 15.5,
      "text": "[first few seconds of speech]",
      "tokens": [...],
      "temperature": 0.0,
      "avg_logprob": -0.45,
      "compression_ratio": 1.35,
      "no_speech_prob": 0.001
    }
    // ... more segments
  ]
}
```

**Note:** No speaker field or diarization information present

---

### Phase 4: INTELLIGENCE EXTRACTION (Claude Sonnet - AI Reasoning)

**Purpose:** Apply contextual reasoning to the raw transcript to extract intelligence, correct errors, and attribute speakers

**Process:**

1. **Queue job to Claude** - Create structured job definition with transcript and metadata
2. **Human operator processes** - AI operator (you) reads job and generates analysis
3. **Claude applies contextual reasoning:**
   - Infer speakers from conversation patterns, known speaker list, topic knowledge
   - Correct proper nouns (Jeremy "Cornell" → "Corbell")
   - Expand and correct acronyms (AERO → AARO)
   - Extract and categorize claims
   - Build entity relationships
   - Construct timeline
   - Identify evidence gaps
4. **Generate structured outputs** - Multiple JSON and markdown files for database ingestion

**Implementation Files:**
- Pipeline handoff: `/home/johnny5/Johny5Alive/j5a-nightshift/ops/fetchers/podcast_intelligence_pipeline.py` (lines 379-447)
- Claude job template: `/home/johnny5/Johny5Alive/queue/claude/weaponized_ep91_sherlock_analysis_template.json`
- Job queue directory: `/home/johnny5/Johny5Alive/queue/claude/`

**Job Queuing:**
```python
def queue_claude_intelligence_extraction(
    transcript_txt: Path,
    transcript_json: Path,
    metadata: Dict,
    episode_number: int
) -> Path:
    """Queue intelligence extraction job to Claude Queue"""
    claude_job = {
        "job_id": f"weaponized_ep{episode_number}_intelligence_...",
        "type": "sherlock_intelligence_extraction",
        "inputs": {
            "transcript_txt": str(transcript_txt.absolute()),
            "transcript_json": str(transcript_json.absolute()),
            "metadata": metadata,
            "podcast_name": "WEAPONIZED with Jeremy Corbell & George Knapp"
        },
        "instructions": [
            "Extract and categorize CLAIMS",
            "Extract ENTITIES with relationships",
            "Build TIMELINE of events",
            "Identify EVIDENCE GAPS",
            "Prepare output for Sherlock database"
        ]
    }
    # Write to Claude queue directory for human operator to process
```

**Claude Analysis Workflow:**

Claude receives the raw transcript and structured metadata, then applies reasoning to:

1. **Speaker Inference** (NOT acoustic diarization)
   - Analyze speaking patterns and vocabulary
   - Match to known speaker list: Jeremy Corbell, George Knapp
   - Cross-reference with conversation flow
   - Infer guest speakers from context clues

2. **Name Correction**
   - Cross-reference Whisper output with known entities
   - Example: "Jeremy Cornell" → "Jeremy Corbell" (host of Weaponized podcast)
   - Apply domain vocabulary knowledge

3. **Claim Extraction and Categorization**
   - Verifiable facts
   - Witness testimony
   - Speculation
   - Opinion
   - Speaker attribution for each claim

4. **Entity Extraction**
   - Individuals (roles, affiliations, testimony provided)
   - Organizations (government programs, private companies)
   - Locations (bases, facilities, regions)
   - Events (incidents, hearings, investigations)
   - Relationships between entities

5. **Timeline Reconstruction**
   - Chronological ordering of events
   - Event correlation
   - Temporal references preservation

6. **Evidence Gap Analysis**
   - Claims needing verification
   - Timeline conflicts or inconsistencies
   - Missing documentation
   - Suggested follow-up research areas

**Outputs Generated:**

```
ops/outputs/sherlock_intelligence/
├── weaponized_ep91_overview.json           # Summary statistics
├── weaponized_ep91_claims.json             # Claims with speaker attribution
├── weaponized_ep91_entities.json           # Named entities (corrected)
├── weaponized_ep91_timeline.json           # Chronological events
├── weaponized_ep91_evidence_gaps.json      # Missing information
└── weaponized_ep91_intelligence_summary.md # Human-readable report
```

**Example Output Structure:**

```json
{
  "claims": [
    {
      "id": "claim_001",
      "text": "The AARO office has received credible reports of anomalous craft",
      "speaker": "Jeremy Corbell",
      "timestamp": "00:12:34",
      "category": "verifiable_fact",
      "confidence": "high",
      "verification_status": "credible_source"
    }
  ],
  "entities": [
    {
      "id": "entity_corbell_jeremy",
      "name": "Jeremy Corbell",
      "type": "individual",
      "role": "podcast_host, uap_investigator",
      "affiliations": ["Weaponized Podcast"]
    }
  ],
  "timeline": [
    {
      "date": "2024-01-15",
      "event": "Congressional hearing on UAP",
      "description": "...",
      "speakers": ["individual_reference"]
    }
  ]
}
```

---

## Part III: Diarization - Current State vs Future Roadmap

### Current State: Speaker Inference (NOT True Diarization)

**What Actually Happens:**

1. Whisper transcribes audio but provides NO speaker labels
2. Files are created with names like `episode_91_transcript_diarized.txt` (misleading - not actually diarized)
3. Raw transcript contains only spoken text with timestamps, no speaker attribution
4. **Claude infers speakers** during Phase 4 using:
   - Known speaker list provided in job metadata
   - Speaking style and vocabulary patterns
   - Topic knowledge (e.g., "Jeremy Corbell discusses his investigations")
   - Conversation flow analysis
   - Domain-specific context

**Limitations of Current Approach:**

- Inference-based, not acoustic fingerprinting
- Relies on contextual knowledge of speakers
- May struggle with unknown guests or new speakers
- No cross-episode speaker tracking
- Cannot identify speakers solely by voice characteristics

**Why This Works Despite Limitations:**

- For known-host podcasts (Weaponized), hosts speak frequently and are identifiable
- Guest speakers are often introduced verbally ("We're speaking with...")
- Topic context provides strong hints about speaker identity
- Claude's reasoning is sophisticated enough for typical podcast patterns

---

### Future Roadmap: Acoustic Diarization

**Goal:** Implement true speaker diarization using voice fingerprinting and acoustic similarity

**Proposed Implementation:**

1. **Add Diarization Library**
   - Option A: `resemblyzer` (speaker embedding extraction)
   - Option B: `pyannote.audio` (end-to-end speaker diarization)
   - Recommendation: pyannote.audio (more modern, better accuracy)

2. **Integration Point:**
   - Insert between Phase 3 (Whisper) and Phase 4 (Claude)
   - Process audio segments from Whisper to generate speaker embeddings
   - Cluster segments by acoustic similarity
   - Assign persistent speaker IDs

3. **Architecture:**
   ```
   Phase 3 Output (transcript.json)
           ↓
   Extract audio segments for clustering
           ↓
   Generate voice embeddings per segment
           ↓
   Cluster embeddings by similarity
           ↓
   Assign speaker IDs (Speaker 0, Speaker 1, etc.)
           ↓
   Map to known speakers if available
           ↓
   Produce diarized transcript with speaker labels
           ↓
   Phase 4 Input (actual diarized transcript)
   ```

4. **Benefits:**
   - True acoustic identification independent of context
   - Robust for unknown or new speakers
   - Cross-episode speaker tracking (same voice across episodes)
   - Improved accuracy for overlapping speech
   - Speaker identification without relying on contextual knowledge

5. **Implementation Tasks:**
   ```python
   # New file: j5a-nightshift/ops/processors/diarizer.py
   class AudioDiarizer:
       def __init__(self, model='pyannote/speaker-diarization'):
           # Load pre-trained diarization model

       def diarize_audio(self, audio_file: Path) -> Dict:
           # Generate speaker embeddings
           # Cluster similar voices
           # Assign speaker IDs
           # Return {segment_id: speaker_id} mapping

       def map_speakers_to_transcript(
           self,
           transcript_json: Path,
           speaker_mapping: Dict
       ) -> Path:
           # Enhance transcript JSON with speaker labels
           # Return diarized_transcript.json

       def build_speaker_profile(self, episode_number: int) -> Dict:
           # Create speaker profiles from diarization
           # For future cross-episode tracking
   ```

6. **Validation & Testing:**
   - Test on known multi-speaker podcast (Weaponized)
   - Compare Claude inference vs acoustic diarization accuracy
   - Measure performance impact on Phase 3 processing time
   - Build speaker database for cross-episode tracking

7. **Estimate Timeline:**
   - Implementation: 2-3 weeks
   - Testing: 1-2 weeks
   - Integration: 1 week
   - Total: 4-6 weeks to full deployment

---

## Part IV: AI-Powered Transcript Correction Mechanism

### How Claude Improves Raw Transcripts

The AI correction is not a separate "correction phase" - it's **integrated into Phase 4 intelligence extraction**. Claude simultaneously:
1. Analyzes the raw transcript
2. Applies contextual reasoning
3. Corrects errors and infers missing information
4. Produces structured intelligence outputs

### Correction Categories

#### 1. Speaker Attribution

**Problem:** Whisper produces raw text with no speaker labels

**Claude Solution:**
- Analyze speaking style and patterns
- Cross-reference with known speaker list: Jeremy Corbell, George Knapp
- Use topic knowledge and conversation flow
- Infer guest speakers from context clues

**Example:**
```
Raw Whisper:
"we need to understand the government's perspective on this issue..."

Claude Analysis:
- Formal, investigative tone → likely Jeremy Corbell or George Knapp
- Topic: government perspective on UAP → hosts discussing guest
- Cross-reference: Known hosts discussing their investigation
- Attribution: George Knapp

Output:
{
  "speaker": "George Knapp",
  "text": "we need to understand the government's perspective on this issue..."
}
```

#### 2. Name Corrections

**Problem:** Whisper misrecognizes proper nouns

**Claude Solution:**
- Entity database lookup
- Domain knowledge (known people in UAP field)
- Contextual fit (role and affiliations)
- Credential assessment

**Example:**
```
Raw Whisper Output:
"Jeremy Cornell has been investigating these anomalies..."

Claude Correction Chain:
1. Recognize "Cornell" is likely a Whisper error
2. Cross-reference known people in domain
3. Find "Jeremy Corbell" - podcast host, investigator
4. Verify fit: speaking about investigations → correct
5. Check Weaponized Podcast hosts → Jeremy Corbell is co-host

Output:
{
  "raw_text": "Jeremy Cornell has been investigating",
  "corrected_text": "Jeremy Corbell has been investigating",
  "correction_type": "proper_noun",
  "confidence": 0.95
}
```

#### 3. Domain Vocabulary

**Problem:** Whisper struggles with domain-specific acronyms and terminology

**Claude Solution:**
- Domain knowledge of UAP research and government structure
- Acronym expansion and correction
- Technical term standardization

**Example:**
```
Raw Whisper:
"The AERO office has been coordinating..."

Claude Analysis:
1. Recognize "AERO" is likely Whisper error in UAP context
2. Domain knowledge: "AARO" = All-domain Anomaly Resolution Office
3. Verify fit: government office coordinating UAP research → AARO
4. Check credibility: AARO is real government office

Output:
{
  "raw_text": "AERO office",
  "corrected_text": "AARO office",
  "expansion": "All-domain Anomaly Resolution Office",
  "entity_type": "government_organization",
  "verification": "credible"
}
```

#### 4. Contextual Understanding

**Problem:** Raw transcripts lack semantic understanding

**Claude Solution:**
- Distinguish verifiable facts from speculation
- Assess speaker credibility
- Connect claims to evidence
- Identify contradictions and gaps

**Example:**
```
Raw Transcript Segment:
"We saw these anomalies moving at supersonic speeds without conventional propulsion..."

Claude Analysis:
Speaker: Jeremy Corbell (investigator, credible source)
Claim Type: Witness testimony (not direct observation)
Fact vs Speculation: Unverified claim (needs corroboration)
Key Terms: Anomalies, supersonic speed, propulsion
Evidence Status: Mentioned in Congressional hearings
Credibility Assessment: Corbell citing credible sources

Output:
{
  "claim": "Anomalies observed moving at supersonic speeds without conventional propulsion",
  "speaker": "Jeremy Corbell",
  "type": "witness_testimony",
  "confidence": "medium",
  "requires_verification": true,
  "related_evidence": ["Congressional UAP hearing testimony"]
}
```

---

## Part V: Implementation Pattern

### Input → Process → Output Flow

**Input:**
- Raw Whisper transcript (text and JSON)
- Episode metadata (title, date, duration, hosts)
- Known speaker list
- Domain context (podcast focus, credibility assessment criteria)

**Process (Claude's Intelligence Extraction):**
1. Read raw transcript into context window
2. Apply metadata and domain knowledge
3. Analyze claims with speaker attribution
4. Extract and map entities
5. Build timeline from temporal references
6. Identify gaps and verification needs
7. Format outputs for database ingestion

**Output Files:**

```
artifacts/claude/2025-12-11/sherlock/
├── weaponized_ep91_overview.json
│   ├── episode_metadata
│   ├── processing_summary
│   ├── total_claims_extracted
│   └── speaker_attribution_confidence
│
├── weaponized_ep91_claims.json
│   ├── [
│   │   {
│   │     "id": "claim_001",
│   │     "text": "claim text",
│   │     "speaker": "Jeremy Corbell",
│   │     "timestamp": "HH:MM:SS",
│   │     "type": "verifiable_fact|witness_testimony|speculation|opinion",
│   │     "confidence": "high|medium|low",
│   │     "verification_status": "verified|credible_source|unverified",
│   │     "sources": ["Congressional hearing", ...]
│   │   }
│   │ ]
│
├── weaponized_ep91_entities.json
│   ├── individuals: [{name, role, affiliations, appearances}]
│   ├── organizations: [{name, type, jurisdiction, programs}]
│   ├── locations: [{name, type, significance}]
│   ├── events: [{date, description, participants}]
│   └── relationships: [{from_entity, relationship_type, to_entity}]
│
├── weaponized_ep91_timeline.json
│   ├── [{date, event, description, speakers, significance}]
│
├── weaponized_ep91_evidence_gaps.json
│   ├── unverified_claims: [...]
│   ├── timeline_conflicts: [...]
│   ├── missing_documentation: [...]
│   └── follow_up_research: [...]
│
└── weaponized_ep91_intelligence_summary.md
    ├── Executive Summary
    ├── Key Claims
    ├── Notable Entities
    ├── Timeline of Events
    ├── Evidence Assessment
    └── Follow-up Research Recommendations
```

---

## Part VI: Implementation Reference

### Key Files and Locations

**Core Pipeline Implementation:**
- `/home/johnny5/Johny5Alive/j5a-nightshift/ops/fetchers/podcast_intelligence_pipeline.py` (612 lines)
  - `PodcastIntelligencePipeline` class
  - All 4 phases + Claude queuing
  - Complete inline documentation

**Claude Job Template:**
- `/home/johnny5/Johny5Alive/queue/claude/weaponized_ep91_sherlock_analysis_template.json`
  - Job structure for intelligence extraction
  - Analysis requirements
  - Output specifications

**Execution Scripts:**
- `/home/johnny5/Johny5Alive/j5a-nightshift/weaponized_ep*.sh`
  - Shell script wrappers for complete pipeline
  - Chunked processing for memory efficiency

**Worker Implementation:**
- `/home/johnny5/Johny5Alive/j5a-nightshift/j5a_worker.py`
  - Processes queued jobs
  - Executes pipeline phases
  - Handles errors and checkpoints

**Operational Documentation:**
- `/home/johnny5/Johny5Alive/j5a-nightshift/sherlock/SHERLOCK_OPERATOR_GUIDE.md`
  - Operating procedures
  - Troubleshooting guidance
  - Integration points

---

### Running the Pipeline

#### Complete Pipeline (Phases 1-4)

```bash
cd /home/johnny5/Johny5Alive/j5a-nightshift

# Run phases 1-3 (automatic)
python3 ops/fetchers/podcast_intelligence_pipeline.py \
  --rss-feed https://feeds.megaphone.fm/weaponized \
  --episode-number 91 \
  --output-dir ops/outputs/podcast_intelligence \
  --auto-queue-claude

# This will:
# 1. Discover Episode 91 in RSS feed
# 2. Download audio file
# 3. Transcribe with Whisper Large-v3
# 4. Queue intelligence extraction job to Claude
# 5. Print summary of outputs
```

#### Phase 4 Only (Intelligence Extraction)

```bash
# Assuming transcript already generated in Phase 3

python3 -c "
from ops.fetchers.podcast_intelligence_pipeline import PodcastIntelligencePipeline
from pathlib import Path

pipeline = PodcastIntelligencePipeline(
    rss_feed_url='https://feeds.megaphone.fm/weaponized',
    output_dir='ops/outputs/podcast_intelligence'
)

# Queue intelligence extraction
claude_job = pipeline.queue_claude_intelligence_extraction(
    transcript_txt=Path('ops/outputs/podcast_intelligence/transcripts/episode_91_transcript.txt'),
    transcript_json=Path('ops/outputs/podcast_intelligence/transcripts/episode_91_transcript.json'),
    metadata={'episode_number': 91, 'title': 'Episode 91'},
    episode_number=91
)

print(f'Claude job queued: {claude_job}')
# Then human operator processes the queued job
"
```

#### Chunked Processing (for long episodes)

```bash
# For episodes >90 minutes, use chunked processing
./weaponized_ep91_chunked.sh

# This:
# 1. Splits audio into 10-minute chunks
# 2. Transcribes each chunk sequentially
# 3. Saves checkpoints after each chunk
# 4. Merges results with proper timestamps
# 5. Queues complete transcript to Claude
```

---

### Monitoring Progress

**Phase 3 Transcription:**
```bash
# Watch Whisper progress (runs 1-2 hours)
watch -n 10 'du -sh ops/outputs/podcast_intelligence/transcripts/'

# Check for transcript files
ls -lh ops/outputs/podcast_intelligence/transcripts/
```

**Phase 4 Claude Jobs:**
```bash
# Check queued jobs
ls -la queue/claude/weaponized_ep91_*.json

# Monitor Claude queue processing
tail -f logs/claude_queue_processor.log
```

---

## Part VII: Known Gaps and Future Enhancements

### Critical Gap: True Diarization Missing

**Current State:**
- Documentation claims "multi-speaker diarization (resemblyzer)" exists
- **Implementation reality:** NO diarization implementation found in codebase
- Whisper produces undiarized transcripts
- Files misleadingly named as "diarized"
- Speaker identification happens through Claude's contextual reasoning in Phase 4

**Impact:**
- Speaker inference works well for known-host podcasts
- May struggle with unknown guests or new voices
- No acoustic-based speaker tracking across episodes
- Relies on contextual knowledge rather than voice fingerprinting

**Recommended Fix:**
See "Future Roadmap: Acoustic Diarization" in Part III (above)

---

### Enhancement Roadmap (Priority Order)

#### Priority 1: Implement True Acoustic Diarization
- **Timeline:** 4-6 weeks
- **Impact:** Eliminates misleading "diarized" label, improves accuracy
- **Technical:** Add pyannote.audio or resemblyzer library
- See Part III for detailed implementation plan

#### Priority 2: Cross-Episode Speaker Database
- **Timeline:** 2-3 weeks (after Priority 1)
- **Impact:** Track speakers across multiple episodes, improve consistency
- **Technical:** Build speaker embedding database, enable fuzzy matching

#### Priority 3: Automatic Speaker Profile Building
- **Timeline:** 1-2 weeks
- **Impact:** Learn speaker characteristics over time, improve future diarization
- **Technical:** Store embeddings, build speaker profiles

#### Priority 4: Overlap Detection and Handling
- **Timeline:** 2 weeks
- **Impact:** Better handling of simultaneous speakers
- **Technical:** Pyannote can detect overlaps, post-process timestamps

#### Priority 5: Multi-Language Support
- **Timeline:** 1-2 weeks (after core diarization stable)
- **Impact:** Support international podcasts
- **Technical:** Extend Whisper to other languages, test diarization

---

## Part VIII: Constitutional Alignment

### How This Workflow Implements J5A Principles

**Principle 2: Transparency**
- Every phase logs outputs and decisions
- Audit trail from RSS discovery through Claude analysis
- Intermediate files preserved for review
- JSON outputs include confidence scores and reasoning

**Principle 3: System Viability**
- Incremental saves (Operation Gladio lesson): Prevent complete data loss on crash
- Completion prioritized: Better to deliver 95% accurate transcript than crash mid-processing
- Graceful degradation: If Whisper struggles, fallback to smaller model
- Checkpoint-based recovery: Resume from last saved segment if process interrupted

**Principle 4: Resource Stewardship**
- Night Shift processing during off-hours: Respects business hours priority
- Whisper Large requires 12GB: Scheduled when system has capacity
- Sequential processing: Prevents thermal constraint violations
- Memory-aware chunking: Long episodes split into manageable segments

**Principle 7: Autonomous Workflows**
- Fully unattended operation (Phases 1-3): No human intervention needed
- Safety gates: Thermal and memory constraints enforced
- Status logging: Morning report summarizes overnight work
- Error recovery: Checkpoint system enables resume on failure

---

## Part IX: Troubleshooting and Common Issues

### Phase 1: Discovery Issues

**Problem:** "Failed to discover audio URL via RSS or web scraping"

**Solutions:**
1. Verify RSS feed URL is correct and accessible
2. Try alternative episode number or title format
3. Check if episode is in RSS feed at all
4. Verify internet connectivity for URL fetching

### Phase 2: Download Issues

**Problem:** "curl failed: Connection timeout after 1800 seconds"

**Solutions:**
1. Episode audio file may be very large (>1GB)
2. Internet connection may be unstable
3. Source server may have download limits
4. Try alternate RSS feed mirror if available

### Phase 3: Transcription Issues

**Problem:** "Whisper: CUDA out of memory" or system freeze

**Solutions:**
1. Use chunked processing: `./weaponized_ep91_chunked.sh`
2. Check system has 12GB available: `free -h`
3. Check CPU temperature: `watch sensors`
4. Retry later if thermal constraint hit

**Problem:** "Transcript accuracy is poor"

**Solutions:**
1. Check if audio quality is adequate
2. Try with Whisper medium model (7GB, slightly lower quality)
3. Verify language setting (default: English)
4. Check if podcast has heavy accents or overlapping speech

### Phase 4: Claude Intelligence Extraction Issues

**Problem:** "Speaker attribution is incorrect"

**Solutions:**
1. This is a known limitation of contextual inference (see Part III)
2. Provide better context in metadata if possible
3. Claude will improve with accurate speaker information
4. Implement acoustic diarization for ground truth speaker labels

**Problem:** "Claude didn't extract all entities or claims"

**Solutions:**
1. Check if transcript is in Claude's context window (max 200k tokens)
2. Split into multiple jobs if episode is very long
3. Provide more explicit instructions for what to extract
4. Use follow-up queries for missed content

---

## Part X: Quick Reference

### Phases at a Glance

| Phase | Name | Purpose | Type | Tool | Time | Output |
|-------|------|---------|------|------|------|--------|
| 1 | DISCOVERY | Find audio URL | Deterministic | RSS/Web | <1min | URL + metadata |
| 2 | ACQUISITION | Download audio | Deterministic | curl/ffmpeg | 5-15min | Audio file |
| 3 | TRANSCRIPTION | Speech-to-text | Deterministic | Whisper | 60-120min | Transcript |
| 4 | INTELLIGENCE EXTRACTION | Reasoning + correction | AI-Reasoning | Claude | 15-30min | JSON + Markdown |

### Critical Files

| File | Purpose | Lines |
|------|---------|-------|
| `podcast_intelligence_pipeline.py` | Complete pipeline implementation | 612 |
| `weaponized_ep91_sherlock_analysis_template.json` | Claude job specification | 73 |
| `SHERLOCK_OPERATOR_GUIDE.md` | Operational procedures | 100+ |

### Key Constraints

| Constraint | Limit | Impact |
|-----------|-------|--------|
| Whisper memory | 12GB | Use chunked processing for long episodes |
| Episode duration | <180 min recommended | Longer episodes may hit timeout |
| Thermal limit | 80°C | System throttles; schedule during cool hours |
| API token window | 200k tokens | Split very long transcripts into multiple jobs |

---

## Conclusion

The podcast processing workflow demonstrates sophisticated division of labor between deterministic mechanical processing (Night Shift) and AI-powered reasoning (Claude). While current speaker identification relies on contextual inference rather than acoustic diarization, the system effectively produces high-quality intelligence analysis suitable for research and evidence assessment.

The documented gaps (especially the missing diarization implementation) provide clear opportunities for enhancement, with a detailed roadmap for implementing acoustic speaker identification and cross-episode speaker tracking.

This workflow exemplifies J5A Constitutional Principles in action: transparent operations, system viability through checkpoints, resource stewardship, and autonomous unattended processing during off-hours.

---

**Document Version:** 1.0
**Last Updated:** 2025-12-11
**Next Review:** 2026-01-11
**Maintainer:** Claude Code (J5A AI Operators)
