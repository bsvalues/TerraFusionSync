use actix_web::{web, HttpResponse, Result};
use serde::{Deserialize, Serialize};
use std::time::Instant;
use uuid::Uuid;

use crate::config::Config;
use crate::metrics::Metrics;
use crate::ollama_client::{OllamaClient, PromptTemplates};

#[derive(Debug, Deserialize)]
pub struct TextRequest {
    pub text: String,
    pub model: Option<String>,
    pub max_tokens: Option<u32>,
    pub temperature: Option<f32>,
}

#[derive(Debug, Serialize)]
pub struct TextResponse {
    pub id: String,
    pub result: String,
    pub model_used: String,
    pub processing_time_ms: u64,
    pub success: bool,
}

#[derive(Debug, Serialize)]
pub struct ErrorResponse {
    pub error: String,
    pub details: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub service: String,
    pub version: String,
    pub status: String,
    pub ollama_connected: bool,
    pub available_models: Vec<String>,
    pub timestamp: String,
}

pub async fn index() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok().json(serde_json::json!({
        "service": "NarratorAI",
        "version": env!("CARGO_PKG_VERSION"),
        "description": "AI-powered natural language processing for TerraFusion Platform",
        "endpoints": {
            "health": "GET /api/v1/health",
            "summarize": "POST /api/v1/summarize",
            "classify": "POST /api/v1/classify",
            "explain": "POST /api/v1/explain",
            "metrics": "GET /api/v1/metrics"
        },
        "example_request": {
            "text": "This is a 2-story residential home located in tax district 503...",
            "model": "llama2",
            "max_tokens": 500,
            "temperature": 0.7
        }
    })))
}

pub async fn health_check(
    config: web::Data<Config>,
    metrics: web::Data<Metrics>,
) -> Result<HttpResponse> {
    let client = OllamaClient::new(config.ollama_url.clone(), config.timeout_seconds);
    
    let (ollama_connected, available_models) = match client.check_health().await {
        Ok(true) => {
            let models = client.list_models().await.unwrap_or_default();
            metrics.update_ollama_health(true);
            (true, models)
        }
        _ => {
            metrics.update_ollama_health(false);
            (false, vec![])
        }
    };

    let status = if ollama_connected { "healthy" } else { "degraded" };

    Ok(HttpResponse::Ok().json(HealthResponse {
        service: "NarratorAI".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        status: status.to_string(),
        ollama_connected,
        available_models,
        timestamp: chrono::Utc::now().to_rfc3339(),
    }))
}

pub async fn summarize_text(
    req: web::Json<TextRequest>,
    config: web::Data<Config>,
    metrics: web::Data<Metrics>,
) -> Result<HttpResponse> {
    let start_time = Instant::now();
    let task_type = "summarize";
    let request_id = Uuid::new_v4().to_string();
    
    metrics.record_task_start(task_type);

    let model = req.model.as_ref().unwrap_or(&config.default_model).clone();
    let max_tokens = req.max_tokens.unwrap_or(config.max_tokens);
    let temperature = req.temperature.unwrap_or(config.temperature);

    let client = OllamaClient::new(config.ollama_url.clone(), config.timeout_seconds);
    let prompt = PromptTemplates::summarize_property(&req.text);

    match client.generate_text(&model, &prompt, max_tokens, temperature).await {
        Ok(result) => {
            let duration = start_time.elapsed();
            metrics.record_task_completion(task_type, &model, duration.as_secs_f64(), true);

            log::info!("Summarization completed: {} chars -> {} chars", req.text.len(), result.len());

            Ok(HttpResponse::Ok().json(TextResponse {
                id: request_id,
                result,
                model_used: model,
                processing_time_ms: duration.as_millis() as u64,
                success: true,
            }))
        }
        Err(e) => {
            metrics.record_error(task_type, "ollama_error");
            log::error!("Summarization failed: {}", e);

            Ok(HttpResponse::ServiceUnavailable().json(ErrorResponse {
                error: "AI processing failed".to_string(),
                details: Some(e.to_string()),
            }))
        }
    }
}

pub async fn classify_text(
    req: web::Json<TextRequest>,
    config: web::Data<Config>,
    metrics: web::Data<Metrics>,
) -> Result<HttpResponse> {
    let start_time = Instant::now();
    let task_type = "classify";
    let request_id = Uuid::new_v4().to_string();
    
    metrics.record_task_start(task_type);

    let model = req.model.as_ref().unwrap_or(&config.default_model).clone();
    let max_tokens = req.max_tokens.unwrap_or(config.max_tokens);
    let temperature = req.temperature.unwrap_or(config.temperature);

    let client = OllamaClient::new(config.ollama_url.clone(), config.timeout_seconds);
    let prompt = PromptTemplates::classify_property_type(&req.text);

    match client.generate_text(&model, &prompt, max_tokens, temperature).await {
        Ok(result) => {
            let duration = start_time.elapsed();
            metrics.record_task_completion(task_type, &model, duration.as_secs_f64(), true);

            log::info!("Classification completed for text of {} chars", req.text.len());

            Ok(HttpResponse::Ok().json(TextResponse {
                id: request_id,
                result,
                model_used: model,
                processing_time_ms: duration.as_millis() as u64,
                success: true,
            }))
        }
        Err(e) => {
            metrics.record_error(task_type, "ollama_error");
            log::error!("Classification failed: {}", e);

            Ok(HttpResponse::ServiceUnavailable().json(ErrorResponse {
                error: "AI processing failed".to_string(),
                details: Some(e.to_string()),
            }))
        }
    }
}

pub async fn explain_data(
    req: web::Json<TextRequest>,
    config: web::Data<Config>,
    metrics: web::Data<Metrics>,
) -> Result<HttpResponse> {
    let start_time = Instant::now();
    let task_type = "explain";
    let request_id = Uuid::new_v4().to_string();
    
    metrics.record_task_start(task_type);

    let model = req.model.as_ref().unwrap_or(&config.default_model).clone();
    let max_tokens = req.max_tokens.unwrap_or(config.max_tokens);
    let temperature = req.temperature.unwrap_or(config.temperature);

    let client = OllamaClient::new(config.ollama_url.clone(), config.timeout_seconds);
    let prompt = PromptTemplates::explain_assessment_data(&req.text);

    match client.generate_text(&model, &prompt, max_tokens, temperature).await {
        Ok(result) => {
            let duration = start_time.elapsed();
            metrics.record_task_completion(task_type, &model, duration.as_secs_f64(), true);

            log::info!("Explanation completed for text of {} chars", req.text.len());

            Ok(HttpResponse::Ok().json(TextResponse {
                id: request_id,
                result,
                model_used: model,
                processing_time_ms: duration.as_millis() as u64,
                success: true,
            }))
        }
        Err(e) => {
            metrics.record_error(task_type, "ollama_error");
            log::error!("Explanation failed: {}", e);

            Ok(HttpResponse::ServiceUnavailable().json(ErrorResponse {
                error: "AI processing failed".to_string(),
                details: Some(e.to_string()),
            }))
        }
    }
}

pub async fn get_metrics(metrics: web::Data<Metrics>) -> Result<HttpResponse> {
    use prometheus::Encoder;
    
    let encoder = prometheus::TextEncoder::new();
    let metric_families = metrics.registry.gather();
    let mut buffer = Vec::new();
    
    encoder.encode(&metric_families, &mut buffer).unwrap();
    let metrics_text = String::from_utf8(buffer).unwrap();

    Ok(HttpResponse::Ok()
        .content_type("text/plain; version=0.0.4; charset=utf-8")
        .body(metrics_text))
}