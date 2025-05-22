use crate::config::TelemetrySettings;
use opentelemetry::global;
use opentelemetry::sdk::propagation::TraceContextPropagator;
use prometheus::{Registry, Counter, Gauge, Histogram, HistogramOpts, IntCounter, IntGauge, Opts};
use std::sync::Arc;
use tracing_subscriber::{layer::SubscriberExt, EnvFilter, Registry as TracingRegistry};

#[derive(Clone)]
pub struct TelemetryService {
    registry: Arc<Registry>,
    pub sync_operations_total: IntCounter,
    pub sync_operations_in_progress: IntGauge,
    pub sync_operations_failed: IntCounter,
    pub gis_exports_total: IntCounter,
    pub gis_exports_in_progress: IntGauge,
    pub gis_export_duration: Histogram,
}

impl TelemetryService {
    pub fn new() -> Self {
        let registry = Registry::new();
        
        let sync_operations_total = IntCounter::new(
            "sync_operations_total", 
            "Total number of sync operations"
        ).unwrap();
        
        let sync_operations_in_progress = IntGauge::new(
            "sync_operations_in_progress",
            "Number of sync operations currently in progress"
        ).unwrap();
        
        let sync_operations_failed = IntCounter::new(
            "sync_operations_failed",
            "Total number of failed sync operations"
        ).unwrap();
        
        let gis_exports_total = IntCounter::new(
            "gis_exports_total",
            "Total number of GIS exports"
        ).unwrap();
        
        let gis_exports_in_progress = IntGauge::new(
            "gis_exports_in_progress",
            "Number of GIS exports currently in progress"
        ).unwrap();
        
        let gis_export_duration = Histogram::with_opts(
            HistogramOpts::new(
                "gis_export_duration_seconds",
                "Duration of GIS export operations in seconds"
            )
            .buckets(vec![0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0])
        ).unwrap();
        
        registry.register(Box::new(sync_operations_total.clone())).unwrap();
        registry.register(Box::new(sync_operations_in_progress.clone())).unwrap();
        registry.register(Box::new(sync_operations_failed.clone())).unwrap();
        registry.register(Box::new(gis_exports_total.clone())).unwrap();
        registry.register(Box::new(gis_exports_in_progress.clone())).unwrap();
        registry.register(Box::new(gis_export_duration.clone())).unwrap();
        
        Self {
            registry: Arc::new(registry),
            sync_operations_total,
            sync_operations_in_progress,
            sync_operations_failed,
            gis_exports_total,
            gis_exports_in_progress,
            gis_export_duration,
        }
    }
    
    pub fn init_tracing(settings: &TelemetrySettings) -> tracing::Subscriber {
        // Set global propagator
        global::set_text_map_propagator(TraceContextPropagator::new());
        
        // Create a tracing layer
        let env_filter = EnvFilter::try_from_default_env()
            .unwrap_or_else(|_| EnvFilter::new("info"));
            
        let subscriber = TracingRegistry::default().with(env_filter);
        
        // TODO: Add OpenTelemetry tracing when jaeger_endpoint is available
        // This would be set up based on our jaeger_endpoint configuration
        
        subscriber
    }
    
    pub fn metrics(&self) -> String {
        use prometheus::Encoder;
        let encoder = prometheus::TextEncoder::new();
        let mut buffer = Vec::new();
        
        encoder.encode(&self.registry.gather(), &mut buffer).unwrap();
        String::from_utf8(buffer).unwrap()
    }
}