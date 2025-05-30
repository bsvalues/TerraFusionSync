use actix_web::{web, HttpResponse, Responder};
use common::error::{Error, Result};
use common::models::gis_export::{CountyConfiguration, LayerDefinition};
use serde::{Deserialize, Serialize};
use crate::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct CountyResponse {
    pub id: String,
    pub name: String,
    pub state: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CountiesResponse {
    pub counties: Vec<CountyResponse>,
    pub total_count: i64,
}

/// Get all available counties
pub async fn get_all_counties(
    state: web::Data<AppState>,
) -> impl Responder {
    // In a real implementation, this would query the database
    // For now, return a stub response
    let counties = vec![
        CountyResponse {
            id: "TEST_COUNTY".to_string(),
            name: "Test County".to_string(),
            state: "WA".to_string(),
        },
        CountyResponse {
            id: "ANOTHER_COUNTY".to_string(),
            name: "Another County".to_string(),
            state: "OR".to_string(),
        },
    ];
    
    HttpResponse::Ok().json(CountiesResponse {
        counties,
        total_count: counties.len() as i64,
    })
}

/// Get county configuration
pub async fn get_county_config(
    county_id: web::Path<String>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Call the service
    match state.services.gis_export.get_county_config(&county_id).await {
        Ok(config) => {
            HttpResponse::Ok().json(config)
        },
        Err(e) => {
            log::error!("Failed to get county configuration for {}: {}", county_id, e);
            
            // Return appropriate error status
            let status_code = match e {
                Error::NotFound(_) => 404,
                _ => 500,
            };
            
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(web::Json(
                    serde_json::json!({
                        "error": format!("Failed to get county configuration: {}", e),
                        "status": status_code
                    })
                ))
        }
    }
}

/// Get county layers
pub async fn get_county_layers(
    county_id: web::Path<String>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Call the service
    match state.services.gis_export.get_county_layers(&county_id).await {
        Ok(layers) => {
            HttpResponse::Ok().json(layers)
        },
        Err(e) => {
            log::error!("Failed to get county layers for {}: {}", county_id, e);
            
            // Return appropriate error status
            let status_code = match e {
                Error::NotFound(_) => 404,
                _ => 500,
            };
            
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(web::Json(
                    serde_json::json!({
                        "error": format!("Failed to get county layers: {}", e),
                        "status": status_code
                    })
                ))
        }
    }
}