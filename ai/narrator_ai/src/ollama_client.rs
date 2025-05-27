use anyhow::{Result, anyhow};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::time::Duration;
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize)]
pub struct OllamaRequest {
    pub model: String,
    pub prompt: String,
    pub stream: bool,
    pub options: OllamaOptions,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OllamaOptions {
    pub num_predict: u32,
    pub temperature: f32,
    pub top_k: u32,
    pub top_p: f32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OllamaResponse {
    pub model: String,
    pub created_at: String,
    pub response: String,
    pub done: bool,
    pub context: Option<Vec<u32>>,
    pub total_duration: Option<u64>,
    pub load_duration: Option<u64>,
    pub prompt_eval_count: Option<u32>,
    pub prompt_eval_duration: Option<u64>,
    pub eval_count: Option<u32>,
    pub eval_duration: Option<u64>,
}

pub struct OllamaClient {
    client: Client,
    base_url: String,
}

impl OllamaClient {
    pub fn new(base_url: String, timeout_seconds: u64) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(timeout_seconds))
            .build()
            .expect("Failed to create HTTP client");

        Self { client, base_url }
    }

    pub async fn generate_text(
        &self,
        model: &str,
        prompt: &str,
        max_tokens: u32,
        temperature: f32,
    ) -> Result<String> {
        let request = OllamaRequest {
            model: model.to_string(),
            prompt: prompt.to_string(),
            stream: false,
            options: OllamaOptions {
                num_predict: max_tokens,
                temperature,
                top_k: 40,
                top_p: 0.9,
            },
        };

        let url = format!("{}/api/generate", self.base_url);
        
        log::debug!("Sending request to Ollama: {}", url);
        
        let response = self
            .client
            .post(&url)
            .json(&request)
            .send()
            .await
            .map_err(|e| anyhow!("Failed to send request to Ollama: {}", e))?;

        if !response.status().is_success() {
            return Err(anyhow!(
                "Ollama API returned error: {} - {}",
                response.status(),
                response.text().await.unwrap_or_default()
            ));
        }

        let ollama_response: OllamaResponse = response
            .json()
            .await
            .map_err(|e| anyhow!("Failed to parse Ollama response: {}", e))?;

        Ok(ollama_response.response)
    }

    pub async fn check_health(&self) -> Result<bool> {
        let url = format!("{}/api/tags", self.base_url);
        
        match self.client.get(&url).send().await {
            Ok(response) => Ok(response.status().is_success()),
            Err(_) => Ok(false),
        }
    }

    pub async fn list_models(&self) -> Result<Vec<String>> {
        let url = format!("{}/api/tags", self.base_url);
        
        let response = self
            .client
            .get(&url)
            .send()
            .await
            .map_err(|e| anyhow!("Failed to get model list: {}", e))?;

        if !response.status().is_success() {
            return Err(anyhow!("Failed to get models from Ollama"));
        }

        #[derive(Deserialize)]
        struct ModelsResponse {
            models: Vec<ModelInfo>,
        }

        #[derive(Deserialize)]
        struct ModelInfo {
            name: String,
        }

        let models_response: ModelsResponse = response
            .json()
            .await
            .map_err(|e| anyhow!("Failed to parse models response: {}", e))?;

        Ok(models_response
            .models
            .into_iter()
            .map(|m| m.name)
            .collect())
    }
}

// Specialized prompts for property assessment tasks
pub struct PromptTemplates;

impl PromptTemplates {
    pub fn summarize_property(text: &str) -> String {
        format!(
            "Summarize this property assessment data in clear, professional language suitable for county staff. \
            Focus on key details like property type, location, and important characteristics. \
            Keep the summary concise but informative:\n\n{}\n\nSummary:",
            text
        )
    }

    pub fn classify_property_type(text: &str) -> String {
        format!(
            "Classify this property into one of these categories: Residential, Commercial, Industrial, Agricultural, or Mixed-Use. \
            Provide the classification and a brief explanation:\n\n{}\n\nClassification:",
            text
        )
    }

    pub fn explain_assessment_data(text: &str) -> String {
        format!(
            "Explain this property assessment data in simple terms that a property owner or county resident could understand. \
            Focus on what the data means and why it matters:\n\n{}\n\nExplanation:",
            text
        )
    }
}