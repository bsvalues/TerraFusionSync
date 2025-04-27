/**
 * Sync operation validator
 * Validates sync operation data before creation or update
 */

interface ValidationResult {
  valid: boolean;
  errors?: string[];
}

/**
 * Validate a sync operation
 */
export function validateSyncOperation(data: any): ValidationResult {
  const errors: string[] = [];
  
  // Check required fields
  if (!data.name) errors.push('Name is required');
  if (!data.source) errors.push('Source system is required');
  if (!data.target) errors.push('Target system is required');
  if (!data.dataType) errors.push('Data type is required');
  
  // Check field mapping if fields are provided
  if (data.fields && Array.isArray(data.fields)) {
    if (!data.fieldMapping || typeof data.fieldMapping !== 'object') {
      errors.push('Field mapping is required when fields are specified');
    } else {
      // Check that all fields have mappings
      for (const field of data.fields) {
        if (!data.fieldMapping[field]) {
          errors.push(`Field "${field}" is missing from field mapping`);
        }
      }
    }
  }
  
  // Check schedule
  if (data.schedule) {
    if (!data.schedule.frequency) errors.push('Schedule frequency is required');
    if (!data.schedule.startDate) errors.push('Schedule start date is required');
    if (!data.schedule.startTime) errors.push('Schedule start time is required');
    
    // Validate frequency
    const validFrequencies = ['once', 'daily', 'weekly', 'monthly'];
    if (!validFrequencies.includes(data.schedule.frequency)) {
      errors.push(`Invalid frequency: ${data.schedule.frequency}. Must be one of: ${validFrequencies.join(', ')}`);
    }
    
    // Validate date format
    if (data.schedule.startDate && !isValidDate(data.schedule.startDate)) {
      errors.push('Start date must be in YYYY-MM-DD format');
    }
    
    // Validate time format
    if (data.schedule.startTime && !isValidTime(data.schedule.startTime)) {
      errors.push('Start time must be in HH:MM format');
    }
  }
  
  return {
    valid: errors.length === 0,
    errors: errors.length > 0 ? errors : undefined
  };
}

/**
 * Validate date format (YYYY-MM-DD)
 */
function isValidDate(dateString: string): boolean {
  const regex = /^\d{4}-\d{2}-\d{2}$/;
  if (!regex.test(dateString)) return false;
  
  const date = new Date(dateString);
  return !isNaN(date.getTime());
}

/**
 * Validate time format (HH:MM)
 */
function isValidTime(timeString: string): boolean {
  const regex = /^([01]\d|2[0-3]):([0-5]\d)$/;
  return regex.test(timeString);
}