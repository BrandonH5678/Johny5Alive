# Harmonize Intelligent Model Selection Across J5A Implementation Plan

## Overview

**Goal:** Integrate IntelligentModelSelector validation into J5A overnight queue management protocols to ensure all audio/ML operations use constraint-aware model selection.

**Priority:** HIGH
**Risk Level:** LOW
**Estimated Tokens:** 35,000
**Estimated Duration:** 1.5 hours

## Current State Analysis

### What Works
- ✅ Squirt CLAUDE.md: Prominent IntelligentModelSelector auto-injection
- ✅ Sherlock CLAUDE.md: NEW section marked highest priority with validation examples
- ✅ Both systems have working examples and integration patterns

### What's Missing
- ❌ J5A CLAUDE.md: No explicit IntelligentModelSelector auto-injection
- ❌ J5A validation checkpoints: No model selection validation gate
- ❌ J5A overnight task definitions: No constraint-aware model selection requirements

### Gap Impact
- **Risk:** Overnight tasks could hard-code model selection, causing OOM crashes
- **Inconsistency:** Squirt/Sherlock enforce model selection, J5A doesn't validate it
- **Quality:** J5A could queue tasks that violate "system viability > quality" principle

---

## Implementation Phases

### Phase 1: Update J5A Context Injection (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** None
**Estimated Tokens:** 12,000
**Estimated Duration:** 30 minutes

**Tasks:**
1. Add IntelligentModelSelector section to J5A CLAUDE.md auto-injection
2. Include constraint-aware model selection in "MANDATORY AUTO-INJECTION" section
3. Add RED FLAGS for model selection violations
4. Provide correct implementation pattern examples

**Expected Outputs:**
- `/home/johnny5/Johny5Alive/CLAUDE.md` (updated with model selection protocols)

**Success Criteria:**
- Model selection auto-injection prominently featured (before line 100)
- RED FLAGS section includes model selection violations
- Example code shows IntelligentModelSelector usage
- Consistent with Squirt/Sherlock CLAUDE.md patterns

---

### Phase 2: Update J5A Operator Manual (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** Phase 1 complete
**Estimated Tokens:** 10,000
**Estimated Duration:** 20 minutes

**Tasks:**
1. Add Intelligent Model Selection to J5A validation checkpoint system
2. Insert new Checkpoint 0.5: Model Selection Validation (BLOCKING GATE)
3. Update "Critical Failure Indicators" with model selection violations
4. Add validation command examples for overnight tasks

**Expected Outputs:**
- `/home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md` (updated checkpoints)

**Success Criteria:**
- New blocking gate checkpoint added between Checkpoint 0 and 1
- Model selection validation commands provided
- Consistent with existing J5A validation philosophy
- References IntelligentModelSelector from subordinate systems

---

### Phase 3: Create Model Selection Validator Tool (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** Phase 2 complete
**Estimated Tokens:** 8,000
**Estimated Duration:** 25 minutes

**Tasks:**
1. Create `src/j5a_model_selection_validator.py`
2. Implement validation logic for task definitions
3. Check if task involves audio/ML processing
4. Verify IntelligentModelSelector usage in task code
5. Validate against RAM constraints (3.0GB safe threshold)

**Expected Outputs:**
- `/home/johnny5/Johny5Alive/src/j5a_model_selection_validator.py`

**Success Criteria:**
- Tool can scan task definitions for model selection violations
- Reports tasks with hard-coded model choices
- Validates memory constraints for selected models
- Integrates with existing J5A validation pipeline

---

### Phase 4: Integration Testing (Ready)

**Status:** Ready for execution
**Risk Level:** LOW
**Dependencies:** Phase 3 complete
**Estimated Tokens:** 5,000
**Estimated Duration:** 15 minutes

**Tasks:**
1. Test validator on sample task definitions
2. Verify correct detection of hard-coded models
3. Validate IntelligentModelSelector approval
4. Confirm integration with overnight queue manager

**Expected Outputs:**
- Test results confirming validator functionality
- Documentation of validation behavior

**Success Criteria:**
- Validator detects hard-coded model selection (negative test)
- Validator approves IntelligentModelSelector usage (positive test)
- Integration with J5A queue manager functional
- No false positives or false negatives

---

## Dependencies

**External:**
- None (IntelligentModelSelector already deployed in Squirt/Sherlock)

**Blocking Conditions:**
- None (all prerequisites satisfied)

**Hardware Requirements:**
- Standard J5A development environment (no special constraints)

---

## Rollback Plan

**If validation causes issues:**
1. Revert CLAUDE.md to previous version (backed up)
2. Revert JOHNY5_AI_OPERATOR_MANUAL.md to previous version
3. Remove `j5a_model_selection_validator.py`
4. Document rollback reason and blockers

**Recovery Strategy:**
- Changes are additive (new validation, not modification)
- Rollback is simple file restoration
- No database or state changes involved

---

## Test Oracle

**Validation Criteria:**

1. **Context Injection Test:**
   ```bash
   grep -i "IntelligentModelSelector" /home/johnny5/Johny5Alive/CLAUDE.md
   # Expected: Multiple matches in auto-injection section
   ```

2. **Checkpoint Validation:**
   ```bash
   grep "Checkpoint 0.5" /home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md
   # Expected: New blocking gate for model selection
   ```

3. **Validator Tool Test:**
   ```bash
   python3 src/j5a_model_selection_validator.py --test-mode
   # Expected: Pass both positive and negative test cases
   ```

4. **Integration Test:**
   ```bash
   # Create test task with hard-coded model
   python3 src/overnight_queue_manager.py --validate test_task_hardcoded.json
   # Expected: Validation failure with model selection violation
   ```

**Quality Metrics:**
- All tests pass
- Documentation consistent across J5A, Squirt, Sherlock
- No regressions in existing validation

---

## Notes

- **Low Risk:** Changes are additive validation, not core logic modification
- **High Value:** Prevents OOM crashes in overnight operations
- **Quick Win:** Most work is documentation updates
- **Cross-System Consistency:** Harmonizes with Squirt/Sherlock patterns

---

**Plan Status:** Ready for J5A overnight execution
**Created:** 2025-09-30
**Version:** 1.0
