use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub ollama_url: String,
    pub default_model: String,
    pub port: u16,
    pub max_tokens: u32,
    pub temperature: f32,
    pub timeout_seconds: u64,
}

impl Config {
    pub fn from_env() -> Self {
        Self {
            ollama_url: env::var("OLLAMA_URL")
                .unwrap_or_else(|_| "http://localhost:11434".to_string()),
            default_model: env::var("AI_MODEL_NAME")
                .unwrap_or_else(|_| "llama2".to_string()),
            port: env::var("NARRATOR_AI_PORT")
                .unwrap_or_else(|_| "7100".to_string())
                .parse()
                .expect("Invalid port number"),
            max_tokens: env::var("AI_MAX_TOKENS")
                .unwrap_or_else(|_| "1000".to_string())
                .parse()
                .expect("Invalid max_tokens"),
            temperature: env::var("AI_TEMPERATURE")
                .unwrap_or_else(|_| "0.7".to_string())
                .parse()
                .expect("Invalid temperature"),
            timeout_seconds: env::var("AI_TIMEOUT_SECONDS")
                .unwrap_or_else(|_| "30".to_string())
                .parse()
                .expect("Invalid timeout"),
        }
    }
}