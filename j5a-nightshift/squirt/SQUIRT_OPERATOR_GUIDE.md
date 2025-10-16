# Squirt Operator Guide

**Version:** 1.0
**Date:** 2025-10-15
**Constitutional Authority:** J5A_CONSTITUTION.md
**Strategic Framework:** J5A_STRATEGIC_AI_PRINCIPLES.md

---

## Overview

Squirt is the business document automation system within the J5A ecosystem. It specializes in voice-to-document workflows for WaterWizard landscaping operations.

## Core Capabilities

### Voice Processing
- Voice memo transcription (faster-whisper)
- Short-form audio (<5 minutes typical)
- Immediate processing for business operations
- Business hours priority enforcement

### Document Generation
- Professional PDF invoices
- Service quotes and estimates
- Job completion reports
- Client communication documents

### Integration Points
- **J5A Queue Manager:** Task coordination and priority management
- **Sherlock:** Shared voice processing infrastructure
- **LibreOffice:** PDF generation and document formatting

## Operating Procedures

### 1. Voice Memo Processing

**For Business Hours Operations:**

```bash
# Immediate processing (business priority)
cd /home/johnny5/Squirt
./process_voice_memo.sh <audio_file>
```

**Constitutional Compliance:**
- Principle 1: Human agency in document review
- Principle 3: Reliable completion for business operations
- Principle 4: Efficient resource use for quick turnaround

### 2. Document Generation

**For Invoice Creation:**

```bash
# Generate PDF invoice from voice memo
python3 generate_invoice.py --voice <memo.mp3> --client <client_name>
```

**Strategic Principle Integration:**
- Principle 1: Executes generation, not just planning
- Principle 4: Remembers client preferences
- Principle 8: Audit trail for financial documents

### 3. Business Hours Priority

Squirt maintains absolute priority during business hours (6am-7pm Mon-Fri):

```bash
# Automatic priority enforcement
# Business hours: Squirt → immediate
# Off hours: Squirt → overnight queue
```

**Key Features:**
- LibreOffice priority during business operations
- No interference from Sherlock heavy processing
- Immediate turnaround for client documents

## Principle Integration

### Constitutional Principles

**Human Agency (Principle 1)**
- All invoices reviewed before sending
- Client communication requires approval
- Easy override for urgent situations

**Transparency (Principle 2)**
- Complete audit trail for financial documents
- Voice memo source retention
- Decision logging for document generation

**System Viability (Principle 3)**
- Reliable document generation
- Graceful error handling
- Backup of all source materials

**Resource Stewardship (Principle 4)**
- Business hours priority for LibreOffice
- Efficient voice processing
- Minimal impact on system resources

### Strategic Principles

**Tool-Augmented Reasoning (Principle 1)**
- Squirt generates documents, not just descriptions
- Automated workflow from voice to PDF
- Direct LibreOffice integration

**Active Memory (Principle 4)**
- Client preferences remembered
- Service history tracking
- Template customization per client

**Multi-Modal Integration (Principle 6)**
- Voice → Text → Document → PDF
- Unified workflow across modalities
- Seamless format transitions

## Common Operations

### Creating an Invoice from Voice Memo

```bash
# 1. Record voice memo (mobile phone)
# 2. Transfer to Squirt directory
cp ~/voice_memos/job_123.mp3 ~/Squirt/inbox/

# 3. Process with Squirt
./process_voice_memo.sh inbox/job_123.mp3

# 4. Review generated invoice
libreoffice ~/Squirt/output/invoice_job_123.pdf

# 5. Send to client
```

### Generating Service Quote

```bash
# From voice description
python3 generate_quote.py --voice service_description.mp3 --client "Smith Residence"

# Review and approve
cat ~/Squirt/output/quote_draft.txt
```

### Batch Processing (Off-Hours)

```bash
# Queue multiple memos for overnight processing
./batch_queue.sh inbox/*.mp3

# Review results next morning
ls -l ~/Squirt/output/
```

## Troubleshooting

### Voice Processing Issues

**Symptom:** Poor transcription accuracy
**Cause:** Background noise or unclear speech
**Solution:** Re-record memo in quiet environment

**Symptom:** Business hours processing delayed
**Cause:** System resources in use
**Solution:** Automatic priority should resolve; check J5A coordination

### Document Generation Issues

**Symptom:** PDF formatting incorrect
**Cause:** LibreOffice template issue
**Solution:** Verify templates in ~/Squirt/templates/

**Symptom:** Client information missing
**Cause:** First-time client (no memory)
**Solution:** Add to client database or provide details in memo

## Integration with J5A

Squirt operates as a high-priority subsystem within J5A:

```
J5A (Coordinator)
  ↓
Business Hours Detection
  ↓
Squirt Worker (Priority)
  ↓
[Voice] → [Text] → [Document] → [PDF]
  ↓
Client Communication
```

Business hours (6am-7pm Mon-Fri):
- Squirt has absolute priority
- Sherlock operations deferred
- LibreOffice resources protected
- Immediate turnaround for documents

## Best Practices

1. **Record clear voice memos** in quiet environment
2. **Include key details** (client name, job type, costs)
3. **Review generated documents** before sending to clients
4. **Maintain client database** for preferences and history
5. **Use batch processing** for multiple memos off-hours

## Client Memory Management

Squirt remembers client preferences:

```python
# First interaction
memory.remember_client({
    'name': 'Johnson Residence',
    'preferences': 'Organic fertilizer only',
    'billing': 'Monthly, email invoice'
})

# Future jobs automatically respect preferences
```

## Reference

- **Constitution:** `J5A_CONSTITUTION.md`
- **Strategic Principles:** `J5A_STRATEGIC_AI_PRINCIPLES.md`
- **Operator Manual:** `JOHNY5_AI_OPERATOR_MANUAL.md`
- **Cross-System Coordination:** Business hours priority enforcement

---

**Document Status:** Autonomous Implementation - Phase 3
**Last Updated:** 2025-10-15
