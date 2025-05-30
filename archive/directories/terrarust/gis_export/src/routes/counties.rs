use actix_web::{web, HttpResponse, Responder, get};
use serde::{Deserialize, Serialize};
use terrafusion_common::{Result, Error};
use terrafusion_common::models::geo::*;
use crate::AppState;

/// Configure county routes
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(list_counties)
       .service(get_county_config)
       .service(get_county_layers);
}

/// List available counties
#[get("")]
async fn list_counties(app_state: web::Data<AppState>) -> Result<impl Responder> {
    log::info!("Listing available counties");
    
    // TODO: Implement database query for counties
    let counties = vec![
        serde_json::json!({
            "id": "benton-wa",
            "name": "Benton County, WA",
            "state": "Washington",
            "supported_formats": ["SHAPEFILE", "GEOJSON", "KML", "CSV"]
        }),
        serde_json::json!({
            "id": "franklin-wa", 
            "name": "Franklin County, WA",
            "state": "Washington",
            "supported_formats": ["SHAPEFILE", "GEOJSON", "KML"]
        })
    ];
    
    Ok(web::Json(serde_json::json!({
        "counties": counties
    })))
}

/// Get county configuration
#[get("/{county_id}/config")]
async fn get_county_config(
    path: web::Path<String>,
    app_state: web::Data<AppState>,
) -> Result<impl Responder> {
    let county_id = path.into_inner();
    log::info!("Getting config for county: {}", county_id);
    
    // TODO: Implement database query for county configuration
    let config = CountyGisConfig {
        county_id: county_id.clone(),
        name: format!("County {}", county_id),
        supported_formats: vec![
            GisExportFormat::Shapefile,
            GisExportFormat::GeoJson,
            GisExportFormat::Kml,
            GisExportFormat::Csv,
        ],
        default_projection: "EPSG:4326".to_string(),
        available_projections: vec!["EPSG:4326".to_string(), "EPSG:3857".to_string()],
        max_export_area_sq_km: Some(1000.0),
        max_export_features: Some(10000),
        default_parameters: serde_json::json!({}),
    };
    
    Ok(web::Json(config))
}

/// Get available layers for a county
#[get("/{county_id}/layers")]
async fn get_county_layers(
    path: web::Path<String>,
    app_state: web::Data<AppState>,
) -> Result<impl Responder> {
    let county_id = path.into_inner();
    log::info!("Getting layers for county: {}", county_id);
    
    // TODO: Implement database query for county layers
    let layers = vec![
        GisLayer {
            id: "parcels".to_string(),
            name: "Tax Parcels".to_string(),
            description: "Property tax parcels".to_string(),
            geometry_type: GeometryType::Polygon,
            attributes: vec![
                GisAttribute {
                    name: "parcel_id".to_string(),
                    description: Some("Parcel identifier".to_string()),
                    data_type: AttributeDataType::String,
                    is_required: true,
                    is_exportable: true,
                    default_value: None,
                },
                GisAttribute {
                    name: "owner_name".to_string(),
                    description: Some("Property owner name".to_string()),
                    data_type: AttributeDataType::String,
                    is_required: false,
                    is_exportable: true,
                    default_value: None,
                },
                GisAttribute {
                    name: "assessed_value".to_string(),
                    description: Some("Assessed property value".to_string()),
                    data_type: AttributeDataType::Float,
                    is_required: false,
                    is_exportable: true,
                    default_value: None,
                },
            ],
            is_enabled: true,
            county_id: county_id.clone(),
            source_table: Some("parcels".to_string()),
            source_query: None,
            style: None,
        },
        GisLayer {
            id: "roads".to_string(),
            name: "Road Network".to_string(),
            description: "County road network".to_string(),
            geometry_type: GeometryType::LineString,
            attributes: vec![
                GisAttribute {
                    name: "road_name".to_string(),
                    description: Some("Road name".to_string()),
                    data_type: AttributeDataType::String,
                    is_required: true,
                    is_exportable: true,
                    default_value: None,
                },
                GisAttribute {
                    name: "road_type".to_string(),
                    description: Some("Type of road".to_string()),
                    data_type: AttributeDataType::String,
                    is_required: false,
                    is_exportable: true,
                    default_value: None,
                },
            ],
            is_enabled: true,
            county_id: county_id.clone(),
            source_table: Some("roads".to_string()),
            source_query: None,
            style: None,
        },
    ];
    
    Ok(web::Json(serde_json::json!({
        "layers": layers
    })))
}