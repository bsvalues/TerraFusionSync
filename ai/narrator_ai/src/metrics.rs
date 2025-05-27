use prometheus::{Counter, Histogram, Registry, Gauge, IntCounterVec, HistogramVec};
use std::sync::Arc;

#[derive(Clone)]
pub struct Metrics {
    pub registry: Arc<Registry>,
    pub ai_tasks_total: IntCounterVec,
    pub ai_latency_seconds: HistogramVec,
    pub ai_errors_total: IntCounterVec,
    pub ollama_health: Gauge,
    pub active_requests: Gauge,
}

pub fn setup_metrics() -> Metrics {
    let registry = Arc::new(Registry::new());

    // Counter for total AI tasks processed
    let ai_tasks_total = IntCounterVec::new(
        prometheus::Opts::new("ai_tasks_total", "Total number of AI tasks processed")
            .namespace("narrator_ai"),
        &["task_type", "model_name", "status"]
    ).expect("Failed to create ai_tasks_total metric");

    // Histogram for AI task latency
    let ai_latency_seconds = HistogramVec::new(
        prometheus::HistogramOpts::new("ai_latency_seconds", "AI task processing latency in seconds")
            .namespace("narrator_ai")
            .buckets(vec![0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]),
        &["task_type", "model_name"]
    ).expect("Failed to create ai_latency_seconds metric");

    // Counter for AI errors
    let ai_errors_total = IntCounterVec::new(
        prometheus::Opts::new("ai_errors_total", "Total number of AI processing errors")
            .namespace("narrator_ai"),
        &["task_type", "error_type"]
    ).expect("Failed to create ai_errors_total metric");

    // Gauge for Ollama health status
    let ollama_health = Gauge::new(
        "ollama_health_status", 
        "Health status of Ollama service (1 = healthy, 0 = unhealthy)"
    ).expect("Failed to create ollama_health metric");

    // Gauge for active requests
    let active_requests = Gauge::new(
        "active_requests_count",
        "Number of currently active AI requests"
    ).expect("Failed to create active_requests metric");

    // Register all metrics
    registry.register(Box::new(ai_tasks_total.clone())).expect("Failed to register ai_tasks_total");
    registry.register(Box::new(ai_latency_seconds.clone())).expect("Failed to register ai_latency_seconds");
    registry.register(Box::new(ai_errors_total.clone())).expect("Failed to register ai_errors_total");
    registry.register(Box::new(ollama_health.clone())).expect("Failed to register ollama_health");
    registry.register(Box::new(active_requests.clone())).expect("Failed to register active_requests");

    Metrics {
        registry,
        ai_tasks_total,
        ai_latency_seconds,
        ai_errors_total,
        ollama_health,
        active_requests,
    }
}

impl Metrics {
    pub fn record_task_start(&self, task_type: &str) {
        self.active_requests.inc();
    }

    pub fn record_task_completion(&self, task_type: &str, model_name: &str, duration_seconds: f64, success: bool) {
        // Record latency
        self.ai_latency_seconds
            .with_label_values(&[task_type, model_name])
            .observe(duration_seconds);

        // Record task completion
        let status = if success { "success" } else { "failure" };
        self.ai_tasks_total
            .with_label_values(&[task_type, model_name, status])
            .inc();

        // Decrease active requests
        self.active_requests.dec();
    }

    pub fn record_error(&self, task_type: &str, error_type: &str) {
        self.ai_errors_total
            .with_label_values(&[task_type, error_type])
            .inc();
        
        self.active_requests.dec();
    }

    pub fn update_ollama_health(&self, healthy: bool) {
        self.ollama_health.set(if healthy { 1.0 } else { 0.0 });
    }
}