-- ================================================================
-- J5A UNIVERSE MEMORY DATABASE SCHEMA V2
-- Simplified schema matching Python UniverseMemoryManager
-- ================================================================

-- ================================================================
-- ENTITIES - Cross-system entity registry
-- ================================================================
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    system_origin TEXT NOT NULL,
    attributes JSON NOT NULL,
    created_timestamp TEXT NOT NULL,
    last_updated_timestamp TEXT NOT NULL,
    usage_count INTEGER DEFAULT 0,
    related_entities JSON,
    aliases JSON
);

CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_system ON entities(system_origin);

-- ================================================================
-- SYSTEM PERFORMANCE - Simple metrics tracking
-- ================================================================
CREATE TABLE IF NOT EXISTS system_performance (
    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name TEXT NOT NULL,
    subsystem_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT NOT NULL,
    measurement_timestamp TEXT NOT NULL,
    context JSON
);

CREATE INDEX idx_performance_system ON system_performance(system_name, subsystem_name);
CREATE INDEX idx_performance_metric ON system_performance(metric_name);
CREATE INDEX idx_performance_timestamp ON system_performance(measurement_timestamp);

-- ================================================================
-- SESSION MEMORY - Significant events
-- ================================================================
CREATE TABLE IF NOT EXISTS session_memory (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name TEXT NOT NULL,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_summary TEXT NOT NULL,
    importance_score REAL NOT NULL,
    event_timestamp TEXT NOT NULL,
    full_context JSON,
    related_entities JSON
);

CREATE INDEX idx_session_system ON session_memory(system_name);
CREATE INDEX idx_session_importance ON session_memory(importance_score);

-- ================================================================
-- CONTEXT REFRESH - Evergreen knowledge
-- ================================================================
CREATE TABLE IF NOT EXISTS context_refresh (
    context_id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name TEXT NOT NULL,
    knowledge_key TEXT NOT NULL,
    knowledge_summary TEXT NOT NULL,
    full_content TEXT NOT NULL,
    last_refreshed_timestamp TEXT NOT NULL,
    refresh_priority REAL NOT NULL,
    usage_count INTEGER DEFAULT 0
);

CREATE INDEX idx_context_system ON context_refresh(system_name);
CREATE INDEX idx_context_priority ON context_refresh(refresh_priority);
CREATE UNIQUE INDEX idx_context_key ON context_refresh(system_name, knowledge_key);

-- ================================================================
-- DECISION HISTORY - Decision provenance
-- ================================================================
CREATE TABLE IF NOT EXISTS decision_history (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name TEXT NOT NULL,
    decision_type TEXT NOT NULL,
    decision_summary TEXT NOT NULL,
    decision_rationale TEXT NOT NULL,
    constitutional_compliance JSON NOT NULL,
    strategic_alignment JSON NOT NULL,
    decision_timestamp TEXT NOT NULL,
    decided_by TEXT NOT NULL,
    outcome_expected TEXT NOT NULL,
    outcome_actual TEXT,
    parameters_used JSON
);

CREATE INDEX idx_decision_system ON decision_history(system_name);
CREATE INDEX idx_decision_type ON decision_history(decision_type);
CREATE INDEX idx_decision_timestamp ON decision_history(decision_timestamp);

-- ================================================================
-- ADAPTIVE PARAMETERS - Learned settings
-- ================================================================
CREATE TABLE IF NOT EXISTS adaptive_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name TEXT NOT NULL,
    parameter_name TEXT NOT NULL,
    parameter_value REAL NOT NULL,
    parameter_context TEXT NOT NULL,
    learning_source TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    last_updated_timestamp TEXT NOT NULL,
    update_count INTEGER DEFAULT 1
);

CREATE INDEX idx_adaptive_system ON adaptive_parameters(system_name);
CREATE INDEX idx_adaptive_confidence ON adaptive_parameters(confidence_score);
CREATE UNIQUE INDEX idx_adaptive_key ON adaptive_parameters(system_name, parameter_name, parameter_context);

-- ================================================================
-- QUALITY BENCHMARKS - Target quality levels
-- ================================================================
CREATE TABLE IF NOT EXISTS quality_benchmarks (
    benchmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name TEXT NOT NULL,
    subsystem_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    benchmark_type TEXT NOT NULL,
    benchmark_value REAL NOT NULL,
    set_timestamp TEXT NOT NULL,
    set_by TEXT NOT NULL,
    reasoning TEXT
);

CREATE INDEX idx_benchmark_system ON quality_benchmarks(system_name, subsystem_name);
CREATE INDEX idx_benchmark_metric ON quality_benchmarks(metric_name);
CREATE UNIQUE INDEX idx_benchmark_key ON quality_benchmarks(system_name, subsystem_name, metric_name, benchmark_type);

-- ================================================================
-- LEARNING OUTCOMES - Captured insights
-- ================================================================
CREATE TABLE IF NOT EXISTS learning_outcomes (
    learning_id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name TEXT NOT NULL,
    learning_category TEXT NOT NULL,
    insight_summary TEXT NOT NULL,
    insight_detail TEXT NOT NULL,
    evidence JSON NOT NULL,
    confidence_score REAL NOT NULL,
    learned_timestamp TEXT NOT NULL,
    applies_to_systems JSON NOT NULL,
    human_validated BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_learning_system ON learning_outcomes(system_name);
CREATE INDEX idx_learning_category ON learning_outcomes(learning_category);
CREATE INDEX idx_learning_confidence ON learning_outcomes(confidence_score);

-- ================================================================
-- LEARNING TRANSFERS - Cross-system knowledge sharing
-- ================================================================
CREATE TABLE IF NOT EXISTS learning_transfers (
    transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    learning_id INTEGER NOT NULL,
    source_system TEXT NOT NULL,
    target_system TEXT NOT NULL,
    transfer_method TEXT NOT NULL,
    adaptation_required TEXT NOT NULL,
    transfer_timestamp TEXT NOT NULL,
    transfer_success BOOLEAN NOT NULL,
    impact_summary TEXT,
    FOREIGN KEY (learning_id) REFERENCES learning_outcomes(learning_id)
);

CREATE INDEX idx_transfer_source ON learning_transfers(source_system);
CREATE INDEX idx_transfer_target ON learning_transfers(target_system);
CREATE INDEX idx_transfer_success ON learning_transfers(transfer_success);

-- ================================================================
-- SITE MODIFIERS - WaterWizard site characteristics
-- ================================================================
CREATE TABLE IF NOT EXISTS site_modifiers (
    modifier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_site_entity_id TEXT NOT NULL,
    job_site_name TEXT NOT NULL,
    soil_type TEXT,
    soil_quality_rating REAL,
    soil_drainage TEXT,
    slope_type TEXT,
    slope_percentage REAL,
    slope_stability TEXT,
    vegetation_type TEXT,
    vegetation_density REAL,
    vegetation_removal_difficulty REAL,
    space_type TEXT,
    access_difficulty REAL,
    equipment_restrictions TEXT,
    labor_rate_multiplier REAL DEFAULT 1.0,
    material_waste_multiplier REAL DEFAULT 1.0,
    time_multiplier REAL DEFAULT 1.0,
    jobs_completed_count INTEGER DEFAULT 0,
    total_variance_labor_hours REAL DEFAULT 0.0,
    total_variance_material_cost REAL DEFAULT 0.0,
    FOREIGN KEY (job_site_entity_id) REFERENCES entities(entity_id)
);

CREATE INDEX idx_site_modifiers_entity ON site_modifiers(job_site_entity_id);
CREATE UNIQUE INDEX idx_site_modifiers_key ON site_modifiers(job_site_entity_id);

-- ================================================================
-- ESTIMATE ACTUALS - WaterWizard estimate vs. actual
-- ================================================================
CREATE TABLE IF NOT EXISTS estimate_actuals (
    comparison_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    client_entity_id TEXT NOT NULL,
    job_site_entity_id TEXT,
    job_type TEXT NOT NULL,
    estimate_timestamp TEXT NOT NULL,
    estimate_labor_hours REAL NOT NULL,
    estimate_labor_cost REAL NOT NULL,
    estimate_materials_cost REAL NOT NULL,
    estimate_total_cost REAL NOT NULL,
    estimate_generation_time_seconds REAL,
    estimate_human_input_time_seconds REAL,
    estimate_template_usage_percent REAL,
    estimate_custom_scopes_count INTEGER,
    estimate_custom_scopes_total_chars INTEGER,
    actual_timestamp TEXT,
    actual_labor_hours REAL,
    actual_labor_cost REAL,
    actual_materials_cost REAL,
    actual_total_cost REAL,
    labor_hours_variance REAL,
    labor_cost_variance REAL,
    materials_cost_variance REAL,
    total_cost_variance REAL,
    labor_hours_variance_percent REAL,
    labor_cost_variance_percent REAL,
    materials_cost_variance_percent REAL,
    customer_satisfaction_score REAL,
    employee_satisfaction_score REAL,
    management_satisfaction_score REAL,
    site_conditions JSON,
    weather_conditions JSON,
    complications_encountered JSON,
    FOREIGN KEY (client_entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (job_site_entity_id) REFERENCES entities(entity_id)
);

CREATE INDEX idx_estimate_actuals_job ON estimate_actuals(job_id);
CREATE INDEX idx_estimate_actuals_client ON estimate_actuals(client_entity_id);
CREATE INDEX idx_estimate_actuals_type ON estimate_actuals(job_type);
CREATE UNIQUE INDEX idx_estimate_actuals_key ON estimate_actuals(job_id);

-- ================================================================
-- DATABASE VERSION
-- ================================================================
CREATE TABLE IF NOT EXISTS database_version (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_number TEXT NOT NULL,
    applied_timestamp TEXT NOT NULL,
    description TEXT
);

INSERT INTO database_version (version_number, applied_timestamp, description)
VALUES ('2.0.0', datetime('now'), 'Simplified schema matching Python UniverseMemoryManager');

-- ================================================================
-- INITIAL QUALITY BENCHMARKS
-- ================================================================
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
