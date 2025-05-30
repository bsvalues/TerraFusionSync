use actix_web::{web, HttpResponse, Responder};
use common::error::Error;
use common::models::gis_export::CountyConfiguration;
use serde::{Deserialize, Serialize};
use crate::AppState;

pub async fn get_county_config(
    county_id: web::Path<String>,
    state: web::Data<AppState>,
) -> impl Responder {
    match state.export_service.get_county_configuration(&county_id).await {
        Ok(config) => {
            HttpResponse::Ok().json(config)
        },
        Err(e) => {
            log::error!("Failed to get county configuration: {}", e);
            
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

pub async fn get_county_layers(
    county_id: web::Path<String>,
    state: web::Data<AppState>,
) -> impl Responder {
    match state.export_service.get_county_layers(&county_id).await {
        Ok(layers) => {
            HttpResponse::Ok().json(layers)
        },
        Err(e) => {
            log::error!("Failed to get county layers: {}", e);
            
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