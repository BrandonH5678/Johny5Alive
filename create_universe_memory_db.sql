-- ================================================================
-- J5A UNIVERSE MEMORY DATABASE SCHEMA
-- Unified Active Memory for Squirt, J5A, and Sherlock
-- Constitutional Basis: Principles 2 (Transparency), 4 (Resource Stewardship), 6 (AI Sentience)
-- ================================================================

-- ================================================================
-- UNIFIED ENTITY REGISTRY
-- Cross-system entity tracking
-- ================================================================

CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,  -- UUID or system-specific ID
    entity_type TEXT NOT NULL,   -- client, source, speaker, person, organization, concept, project, job_site
    entity_name TEXT NOT NULL,
    system_origin TEXT NOT NULL,  -- squirt, j5a, sherlock
    attributes JSON NOT NULL,     -- Flexible schema per entity type

    -- Metadata
    created_timestamp TEXT NOT NULL,
    last_updated_timestamp TEXT NOT NULL,
    usage_count INTEGER DEFAULT 0,

    -- Cross-references
    related_entities JSON,        -- Links to other entity_ids
    aliases JSON                  -- Alternative names/spellings
);

CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_system ON entities(system_origin);
CREATE INDEX idx_entities_name ON entities(entity_name);

-- ================================================================
-- SYSTEM PERFORMANCE TRACKING
-- Unified metrics across all systems
-- ================================================================

CREATE TABLE IF NOT EXISTS system_performance (
    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identification
    system_name TEXT NOT NULL,    -- squirt, j5a, sherlock
    subsystem_name TEXT,          -- invoice, estimate, contract, claude_queue, intelligence_extraction, etc.
    task_type TEXT NOT NULL,      -- specific operation type
    task_id TEXT,                 -- Optional reference to specific task

    -- Timing
    timestamp TEXT NOT NULL,
    duration_seconds REAL,

    -- Outcome
    success BOOLEAN NOT NULL,
    failure_reason TEXT,

    -- Quality
    quality_score REAL,           -- 0.0-1.0 normalized quality
    quality_dimensions JSON,      -- Detailed quality breakdown

    -- Metrics (system-specific)
    metrics JSON NOT NULL,

    -- Context (what conditions existed)
    context JSON NOT NULL,

    -- Resources
    memory_usage_gb REAL,
    cpu_temperature REAL,
    thermal_constraint_hit BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_performance_system ON system_performance(system_name, subsystem_name);
CREATE INDEX idx_performance_timestamp ON system_performance(timestamp);
CREATE INDEX idx_performance_success ON system_performance(success);
CREATE INDEX idx_performance_task_type ON system_performance(task_type);

-- ================================================================
-- SESSION MEMORY
-- Significant events, incidents, learnings
-- ================================================================

CREATE TABLE IF NOT EXISTS session_memory (
    session_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    system_name TEXT NOT NULL,

    -- Event classification
    event_type TEXT NOT NULL,     -- success, failure, anomaly, breakthrough, pattern_discovered
    event_description TEXT NOT NULL,
    impact_assessment TEXT,       -- high, medium, low

    -- Learning
    learnings JSON,               -- Structured learnings from this session
    patterns_discovered JSON,     -- New patterns identified

    -- Context
    related_performance_ids JSON,  -- Links to performance records
    related_entity_ids JSON,      -- Links to involved entities

    -- Human oversight
    human_validated BOOLEAN DEFAULT FALSE,
    human_validation_timestamp TEXT,
    human_notes TEXT
);

CREATE INDEX idx_session_memory_system ON session_memory(system_name);
CREATE INDEX idx_session_memory_type ON session_memory(event_type);
CREATE INDEX idx_session_memory_timestamp ON session_memory(timestamp);

-- ================================================================
-- CONTEXT REFRESH
-- Evergreen knowledge that guides operations
-- ================================================================

CREATE TABLE IF NOT EXISTS context_refresh (
    context_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Classification
    category TEXT NOT NULL,       -- priorities, active_projects, learned_patterns, quality_standards
    system_name TEXT,             -- NULL for cross-system context

    -- Content
    content TEXT NOT NULL,        -- Markdown-formatted context
    content_type TEXT DEFAULT 'markdown',  -- markdown, json, yaml

    -- Lifecycle
    effective_timestamp TEXT NOT NULL,
    expires_timestamp TEXT,       -- NULL if permanent
    currently_active BOOLEAN DEFAULT TRUE,
    superseded_by INTEGER,        -- References another context_id

    -- Metadata
    author TEXT,                  -- human or system
    update_frequency TEXT,        -- daily, weekly, monthly, as_needed

    FOREIGN KEY (superseded_by) REFERENCES context_refresh(context_id)
);

CREATE INDEX idx_context_category ON context_refresh(category);
CREATE INDEX idx_context_system ON context_refresh(system_name);
CREATE INDEX idx_context_active ON context_refresh(currently_active);

-- ================================================================
-- DECISION PROVENANCE
-- Track all significant decisions with reasoning
-- ================================================================

CREATE TABLE IF NOT EXISTS decision_history (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identification
    timestamp TEXT NOT NULL,
    system_name TEXT NOT NULL,
    subsystem_name TEXT,
    decision_point TEXT NOT NULL,  -- What decision was made

    -- Decision details
    decision_made TEXT NOT NULL,
    alternatives_considered JSON NOT NULL,

    -- Reasoning (CRITICAL for transparency)
    reasoning TEXT NOT NULL,
    retrieve_inputs JSON,          -- What data was retrieved
    reason_factors JSON,           -- Factors considered

    -- Constitutional alignment
    constitutional_principles JSON NOT NULL,  -- Which principles guided decision
    human_agency_preserved BOOLEAN DEFAULT TRUE,

    -- Outcome tracking
    outcome_measured BOOLEAN DEFAULT FALSE,
    outcome_quality REAL,
    outcome_notes TEXT,

    -- Human oversight
    human_overridden BOOLEAN DEFAULT FALSE,
    override_reason TEXT,
    override_timestamp TEXT,

    -- Links
    related_performance_id INTEGER,
    related_session_id TEXT,

    FOREIGN KEY (related_performance_id) REFERENCES system_performance(performance_id),
    FOREIGN KEY (related_session_id) REFERENCES session_memory(session_id)
);

CREATE INDEX idx_decision_system ON decision_history(system_name);
CREATE INDEX idx_decision_timestamp ON decision_history(timestamp);
CREATE INDEX idx_decision_point ON decision_history(decision_point);

-- ================================================================
-- ADAPTIVE PARAMETERS
-- System parameters that adapt based on learning
-- ================================================================

CREATE TABLE IF NOT EXISTS adaptive_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identification
    parameter_name TEXT NOT NULL,
    parameter_category TEXT NOT NULL,  -- model_selection, threshold, timeout, labor_rate_modifier, etc.
    system_name TEXT NOT NULL,
    subsystem_name TEXT,

    -- Value
    parameter_value JSON NOT NULL,    -- Serialized value (can be any type)
    parameter_type TEXT NOT NULL,     -- float, int, string, bool, dict, list

    -- Lifecycle
    effective_timestamp TEXT NOT NULL,
    superseded_timestamp TEXT,
    superseded_by INTEGER,
    currently_active BOOLEAN DEFAULT TRUE,

    -- Adaptation reasoning
    adaptation_reason TEXT NOT NULL,
    supporting_evidence JSON,         -- Performance IDs or other evidence
    confidence REAL NOT NULL,         -- 0.0-1.0 confidence in adaptation

    -- Human oversight
    human_approved BOOLEAN DEFAULT FALSE,
    human_approval_timestamp TEXT,
    human_notes TEXT,

    -- Effectiveness tracking
    effectiveness_measured BOOLEAN DEFAULT FALSE,
    effectiveness_score REAL,
    measurement_period_days INTEGER,
    measurement_sample_size INTEGER,

    FOREIGN KEY (superseded_by) REFERENCES adaptive_parameters(parameter_id)
);

CREATE INDEX idx_adaptive_system ON adaptive_parameters(system_name, subsystem_name);
CREATE INDEX idx_adaptive_active ON adaptive_parameters(currently_active);
CREATE INDEX idx_adaptive_category ON adaptive_parameters(parameter_category);
CREATE INDEX idx_adaptive_name ON adaptive_parameters(parameter_name);

-- ================================================================
-- QUALITY BENCHMARKS
-- Target quality levels per system/task
-- ================================================================

CREATE TABLE IF NOT EXISTS quality_benchmarks (
    benchmark_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Scope
    system_name TEXT NOT NULL,
    subsystem_name TEXT,
    metric_name TEXT NOT NULL,

    -- Benchmark levels
    benchmark_type TEXT NOT NULL,  -- minimum, target, excellent
    benchmark_value REAL NOT NULL,

    -- Context
    set_timestamp TEXT NOT NULL,
    set_by TEXT NOT NULL,          -- human or system
    reasoning TEXT,

    -- Lifecycle
    currently_active BOOLEAN DEFAULT TRUE,
    superseded_by INTEGER,
    superseded_timestamp TEXT,

    FOREIGN KEY (superseded_by) REFERENCES quality_benchmarks(benchmark_id)
);

CREATE INDEX idx_benchmark_system ON quality_benchmarks(system_name, subsystem_name);
CREATE INDEX idx_benchmark_metric ON quality_benchmarks(metric_name);
CREATE INDEX idx_benchmark_active ON quality_benchmarks(currently_active);

-- ================================================================
-- LEARNING OUTCOMES
-- Captured insights and their impact
-- ================================================================

CREATE TABLE IF NOT EXISTS learning_outcomes (
    outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,

    -- Learning classification
    learning_category TEXT NOT NULL,  -- model_selection, parameter_tuning, error_pattern, workflow_optimization, pricing_calibration
    system_name TEXT NOT NULL,
    subsystem_name TEXT,

    -- Learning description
    learning_description TEXT NOT NULL,
    evidence_performance_ids JSON,   -- Supporting performance records
    evidence_decision_ids JSON,      -- Supporting decisions
    confidence_score REAL NOT NULL,  -- 0.0-1.0

    -- Action taken
    system_refinement_applied BOOLEAN DEFAULT FALSE,
    refinement_description TEXT,
    refinement_code_path TEXT,       -- Path to code implementing refinement

    -- Validation
    human_validated BOOLEAN DEFAULT FALSE,
    human_validation_timestamp TEXT,
    validation_notes TEXT,

    -- Effectiveness tracking
    effectiveness_measured BOOLEAN DEFAULT FALSE,
    effectiveness_score REAL,
    measurement_episode_count INTEGER,

    -- Transfer potential
    cross_system_applicable BOOLEAN DEFAULT FALSE,
    target_systems JSON              -- Systems that might benefit from this learning
);

CREATE INDEX idx_learning_system ON learning_outcomes(system_name, subsystem_name);
CREATE INDEX idx_learning_category ON learning_outcomes(learning_category);
CREATE INDEX idx_learning_validated ON learning_outcomes(human_validated);
CREATE INDEX idx_learning_timestamp ON learning_outcomes(timestamp);

-- ================================================================
-- CROSS-SYSTEM LEARNING TRANSFERS
-- Track when learnings move between systems
-- ================================================================

CREATE TABLE IF NOT EXISTS learning_transfers (
    transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,

    -- Source and target
    source_learning_id INTEGER NOT NULL,
    source_system TEXT NOT NULL,
    target_system TEXT NOT NULL,

    -- Transfer details
    transfer_type TEXT NOT NULL,  -- pattern, parameter, strategy, template
    adaptation_description TEXT NOT NULL,

    -- Effectiveness
    transfer_success BOOLEAN,
    effectiveness_score REAL,
    notes TEXT,

    FOREIGN KEY (source_learning_id) REFERENCES learning_outcomes(outcome_id)
);

CREATE INDEX idx_transfer_source ON learning_transfers(source_system);
CREATE INDEX idx_transfer_target ON learning_transfers(target_system);
CREATE INDEX idx_transfer_timestamp ON learning_transfers(timestamp);

-- ================================================================
-- WATERWIZARD-SPECIFIC: JOB SITE MODIFIERS
-- Site-specific conditions that affect labor/material estimates
-- ================================================================

CREATE TABLE IF NOT EXISTS site_modifiers (
    modifier_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Link to job site entity
    job_site_entity_id TEXT NOT NULL,
    job_site_name TEXT NOT NULL,

    -- Soil characteristics
    soil_type TEXT,                -- clay, sandy, rocky, loam, compacted, mixed, etc.
    soil_quality_rating REAL,      -- 0.0-1.0 (1.0 = ideal for work)
    soil_drainage TEXT,            -- excellent, good, moderate, poor, very_poor

    -- Slope characteristics
    slope_type TEXT,               -- flat, gentle, moderate, steep, extreme
    slope_percentage REAL,         -- Actual slope grade percentage
    slope_stability TEXT,          -- stable, moderate, unstable

    -- Vegetation characteristics
    vegetation_type TEXT,          -- grass_only, light_brush, heavy_brush, trees_small, trees_large, forest
    vegetation_density REAL,       -- 0.0-1.0 (1.0 = completely overgrown)
    vegetation_removal_difficulty REAL,  -- 0.0-1.0 (1.0 = most difficult)

    -- Space/access characteristics
    space_type TEXT,               -- open_access, tight_access, very_tight, overhead_obstacles, underground_utilities
    access_difficulty REAL,        -- 0.0-1.0 (1.0 = most difficult)
    equipment_restrictions TEXT,   -- none, light_only, hand_tools_only, etc.

    -- Learned multipliers (from actual vs. estimate variance)
    labor_rate_multiplier REAL DEFAULT 1.0,     -- Learned adjustment based on this site
    material_waste_multiplier REAL DEFAULT 1.0,  -- Additional material needed
    time_multiplier REAL DEFAULT 1.0,            -- How much longer jobs take

    -- Tracking
    jobs_completed_count INTEGER DEFAULT 0,
    total_variance_labor_hours REAL DEFAULT 0.0,
    total_variance_material_cost REAL DEFAULT 0.0,

    -- Metadata
    created_timestamp TEXT NOT NULL,
    last_updated_timestamp TEXT NOT NULL,

    FOREIGN KEY (job_site_entity_id) REFERENCES entities(entity_id)
);

CREATE INDEX idx_site_modifiers_entity ON site_modifiers(job_site_entity_id);
CREATE INDEX idx_site_modifiers_soil ON site_modifiers(soil_type);
CREATE INDEX idx_site_modifiers_slope ON site_modifiers(slope_type);
CREATE INDEX idx_site_modifiers_vegetation ON site_modifiers(vegetation_type);
CREATE INDEX idx_site_modifiers_space ON site_modifiers(space_type);

-- ================================================================
-- WATERWIZARD-SPECIFIC: ESTIMATE VS. ACTUAL TRACKING
-- Track accuracy of estimates compared to actual job performance
-- ================================================================

CREATE TABLE IF NOT EXISTS estimate_actuals (
    comparison_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Job identification
    job_id TEXT NOT NULL,
    client_entity_id TEXT NOT NULL,
    job_site_entity_id TEXT,
    job_type TEXT NOT NULL,         -- irrigation_install, deck_build, landscape, etc.

    -- Estimate data
    estimate_timestamp TEXT NOT NULL,
    estimate_labor_hours REAL NOT NULL,
    estimate_labor_cost REAL NOT NULL,
    estimate_materials_cost REAL NOT NULL,
    estimate_total_cost REAL NOT NULL,
    estimate_generation_time_seconds REAL,  -- How long to create estimate
    estimate_human_input_time_seconds REAL, -- Human time required
    estimate_template_usage_percent REAL,   -- % from templates vs. custom
    estimate_custom_scopes_count INTEGER,   -- Number of custom scopes created
    estimate_custom_scopes_total_chars INTEGER,  -- Size of custom work

    -- Actual data (populated on job completion)
    actual_timestamp TEXT,
    actual_labor_hours REAL,
    actual_labor_cost REAL,
    actual_materials_cost REAL,
    actual_total_cost REAL,

    -- Variance calculations
    labor_hours_variance REAL,      -- actual - estimate
    labor_cost_variance REAL,
    materials_cost_variance REAL,
    total_cost_variance REAL,
    labor_hours_variance_percent REAL,
    labor_cost_variance_percent REAL,
    materials_cost_variance_percent REAL,

    -- Satisfaction metrics
    customer_satisfaction_score REAL,  -- 0.0-1.0
    employee_satisfaction_score REAL,  -- 0.0-1.0 (ease of execution)
    management_satisfaction_score REAL, -- 0.0-1.0 (profitability)

    -- Context factors (for learning)
    site_conditions JSON,           -- Captured soil/slope/vegetation/space conditions
    weather_conditions JSON,        -- Weather impact
    complications_encountered JSON, -- Unexpected issues

    -- Metadata
    created_timestamp TEXT NOT NULL,
    completed_timestamp TEXT,

    FOREIGN KEY (client_entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (job_site_entity_id) REFERENCES entities(entity_id)
);

CREATE INDEX idx_estimate_actuals_job ON estimate_actuals(job_id);
CREATE INDEX idx_estimate_actuals_client ON estimate_actuals(client_entity_id);
CREATE INDEX idx_estimate_actuals_site ON estimate_actuals(job_site_entity_id);
CREATE INDEX idx_estimate_actuals_type ON estimate_actuals(job_type);
CREATE INDEX idx_estimate_actuals_timestamp ON estimate_actuals(estimate_timestamp);
CREATE INDEX idx_estimate_actuals_completed ON estimate_actuals(completed_timestamp);

-- ================================================================
-- INITIAL QUALITY BENCHMARKS
-- Set initial targets for key metrics
-- ================================================================

-- Squirt invoice/estimate benchmarks
INSERT OR IGNORE INTO quality_benchmarks (system_name, subsystem_name, metric_name, benchmark_type, benchmark_value, set_timestamp, set_by, reasoning)
VALUES
    ('squirt', 'invoice', 'generation_time_seconds', 'target', 30.0, datetime('now'), 'system', 'Target: <30 seconds per invoice'),
    ('squirt', 'invoice', 'generation_time_seconds', 'excellent', 15.0, datetime('now'), 'system', 'Excellent: <15 seconds per invoice'),
    ('squirt', 'invoice', 'client_acceptance_rate', 'target', 0.90, datetime('now'), 'system', 'Target: 90% accepted without edits'),
    ('squirt', 'invoice', 'client_acceptance_rate', 'excellent', 0.95, datetime('now'), 'system', 'Excellent: 95% accepted without edits'),

    ('squirt', 'estimate', 'generation_time_seconds', 'target', 120.0, datetime('now'), 'system', 'Target: <2 minutes with human input'),
    ('squirt', 'estimate', 'generation_time_seconds', 'excellent', 60.0, datetime('now'), 'system', 'Excellent: <1 minute'),
    ('squirt', 'estimate', 'labor_variance_percent', 'target', 0.10, datetime('now'), 'system', 'Target: within 10% of actual'),
    ('squirt', 'estimate', 'labor_variance_percent', 'excellent', 0.05, datetime('now'), 'system', 'Excellent: within 5% of actual'),
    ('squirt', 'estimate', 'materials_variance_percent', 'target', 0.15, datetime('now'), 'system', 'Target: within 15% of actual'),
    ('squirt', 'estimate', 'materials_variance_percent', 'excellent', 0.08, datetime('now'), 'system', 'Excellent: within 8% of actual'),
    ('squirt', 'estimate', 'customer_satisfaction', 'target', 0.85, datetime('now'), 'system', 'Target: 85% satisfaction'),
    ('squirt', 'estimate', 'customer_satisfaction', 'excellent', 0.92, datetime('now'), 'system', 'Excellent: 92% satisfaction');

-- ================================================================
-- DATABASE VERSION TRACKING
-- ================================================================

CREATE TABLE IF NOT EXISTS database_version (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_number TEXT NOT NULL,
    applied_timestamp TEXT NOT NULL,
    description TEXT
);

INSERT INTO database_version (version_number, applied_timestamp, description)
VALUES ('1.0.0', datetime('now'), 'Initial schema with WaterWizard site modifiers and estimate tracking');
