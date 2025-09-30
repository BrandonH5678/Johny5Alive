# Johny5Alive - Multi-System AI Management

**Umbrella management system for coordinating AI-driven systems on the Johny5 Mac Mini**

## Overview

Johny5Alive provides centralized coordination and development management for multiple AI systems:

- **Squirt**: Production business document automation (WaterWizard landscaping)
- **Sherlock**: AI research system for deep content analysis
- **Future systems**: Framework ready for additional AI applications

## Quick Start

### Load Current Protocols
```bash
python3 ai_operator_helper.py protocols
```

### Check System Status
```bash
python3 ai_operator_helper.py status
```

### Complete a Milestone
```bash
python3 ai_operator_helper.py milestone "Your milestone description"
```

### Confirm Manual Updated
```bash
python3 ai_operator_helper.py updated
```

## System Architecture

```
Johny5Alive (Umbrella Manager)
├── Squirt (Production - Business Priority)
│   ├── Document automation
│   ├── Voice memo transcription (planned)
│   └── LibreOffice integration
├── Sherlock (Development - Research Priority)
│   ├── Voice processing & diarization
│   ├── Auto-anchor detection
│   └── Evidence pipeline
└── Future Systems
    └── Framework ready for expansion
```

## Resource Coordination

### Business Hours (6am-7pm Mon-Fri)
- **Squirt**: Full priority (LibreOffice, memory, CPU)
- **Sherlock**: Background processing only
- **Development**: Squirt-focused maintenance

### After Hours/Weekends
- **Sherlock**: Full development priority
- **Heavy processing**: Long-form audio, model training
- **Cross-system**: Integration testing

## Key Components

### `JOHNY5_AI_OPERATOR_MANUAL.md`
Single source of truth for system status, milestones, and protocols

### `src/protocol_manager.py`
Core system for context injection and resource coordination

### `ai_operator_helper.py`
CLI interface for protocols, milestones, and system management

### `development_log.json`
Automatic tracking of milestones and development progress

## Development Workflow

1. **Before starting work**: Load protocols to understand current status
2. **During development**: Monitor resource usage and system priorities
3. **After completing milestones**: Log completion and update manual
4. **Regular updates**: Keep documentation current with system changes

## Integration with Existing Systems

### Squirt Integration
- Respects existing LibreOffice monitoring
- Inherits business-critical priority handling
- Extends visual validation patterns

### Sherlock Integration
- Coordinates with existing voice processing pipeline
- Manages supervised vs. unsupervised diarization
- Handles resource allocation for model loading

## Future Expansion

The system is designed to easily accommodate additional AI systems:

1. Add system definition to `protocol_manager.py`
2. Update resource allocation matrix
3. Add system-specific monitoring
4. Update manual with new coordination rules

## Monitoring and Logging

- **Real-time resource monitoring**: Memory, CPU, LibreOffice status
- **Development progress tracking**: Milestone completion and documentation
- **Cross-system coordination**: Priority handling and conflict resolution
- **Business hours awareness**: Automatic priority adjustment

---

**🤖 Remember**: Always update the manual when completing milestones. The system depends on accurate documentation for proper coordination.