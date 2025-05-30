import React from 'react';
import { Card } from '../core/Card';
import { Button } from '../core/Button';
import { StatusBadge } from '../data-display/StatusBadge';
import { ProgressBar } from '../data-display/ProgressBar';
import { cn } from '../../utils/cn';

export interface SyncOperationCardProps {
  /**
   * Unique identifier for the sync operation
   */
  id: string;
  
  /**
   * Name of the sync operation
   */
  name: string;
  
  /**
   * Optional description of the sync operation
   */
  description?: string;
  
  /**
   * Source system identifier
   */
  source: string;
  
  /**
   * Target system identifier
   */
  target: string;
  
  /**
   * Type of data being synced
   */
  dataType: string;
  
  /**
   * Current status of the operation
   */
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'scheduled';
  
  /**
   * Last run timestamp
   */
  lastRunAt?: string;
  
  /**
   * Next scheduled run timestamp
   */
  nextRunAt?: string;
  
  /**
   * Total records to process
   */
  totalRecords?: number;
  
  /**
   * Number of records processed so far
   */
  processedRecords?: number;
  
  /**
   * Number of records that failed processing
   */
  failedRecords?: number;
  
  /**
   * Error message if the operation failed
   */
  errorMessage?: string;
  
  /**
   * Handler for view details button click
   */
  onViewDetails?: (id: string) => void;
  
  /**
   * Handler for run/retry button click
   */
  onRun?: (id: string) => void;
  
  /**
   * Handler for cancel button click
   */
  onCancel?: (id: string) => void;
  
  /**
   * Whether the card is in a loading state
   */
  isLoading?: boolean;
  
  /**
   * Additional class name for the component
   */
  className?: string;
  
  /**
   * Whether to show action buttons
   * @default true
   */
  showActions?: boolean;
  
  /**
   * Whether to make the entire card clickable
   * @default true
   */
  clickable?: boolean;
}

/**
 * SyncOperationCard Component
 * 
 * A specialized card component for displaying sync operations
 */
export const SyncOperationCard: React.FC<SyncOperationCardProps> = ({
  id,
  name,
  description,
  source,
  target,
  dataType,
  status,
  lastRunAt,
  nextRunAt,
  totalRecords,
  processedRecords,
  failedRecords,
  errorMessage,
  onViewDetails,
  onRun,
  onCancel,
  isLoading = false,
  className,
  showActions = true,
  clickable = true,
}) => {
  // Format date for display
  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'N/A';
    
    try {
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date);
    } catch (error) {
      return 'Invalid date';
    }
  };
  
  // Handle view details click
  const handleViewDetails = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onViewDetails) {
      onViewDetails(id);
    }
  };
  
  // Handle run/retry click
  const handleRun = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onRun) {
      onRun(id);
    }
  };
  
  // Handle cancel click
  const handleCancel = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onCancel) {
      onCancel(id);
    }
  };
  
  // Handle card click
  const handleCardClick = () => {
    if (clickable && onViewDetails) {
      onViewDetails(id);
    }
  };
  
  // Determine the run button label based on status
  const getRunButtonLabel = (): string => {
    switch (status) {
      case 'failed':
        return 'Retry';
      case 'completed':
      case 'cancelled':
      case 'pending':
      case 'scheduled':
        return 'Run Now';
      case 'running':
        return 'Running...';
      default:
        return 'Run Now';
    }
  };
  
  // Determine if run button should be disabled
  const isRunButtonDisabled = status === 'running' || isLoading;
  
  // Calculate completion percentage
  const completionPercentage = 
    status === 'running' && 
    typeof totalRecords === 'number' && 
    typeof processedRecords === 'number' && 
    totalRecords > 0
      ? (processedRecords / totalRecords) * 100
      : 0;
  
  return (
    <Card
      className={cn(
        'transition-all duration-200',
        clickable && 'cursor-pointer hover:shadow-md',
        className
      )}
      onClick={handleCardClick}
    >
      <div className="flex flex-col">
        {/* Header section with status */}
        <div className="flex flex-wrap justify-between items-start mb-3">
          <StatusBadge status={status} className="mb-2" />
          
          <div className="text-sm text-gray-500">
            {lastRunAt && (
              <div>Last run: {formatDate(lastRunAt)}</div>
            )}
            {nextRunAt && status === 'scheduled' && (
              <div>Next run: {formatDate(nextRunAt)}</div>
            )}
          </div>
        </div>
        
        {/* Content section */}
        <div className="mb-4">
          <h3 className="text-lg font-medium text-gray-900 mb-1">{name}</h3>
          
          {description && (
            <p className="text-gray-600 text-sm mb-2">{description}</p>
          )}
          
          <div className="flex flex-wrap gap-2 text-xs text-gray-500 mt-2">
            <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5">
              Source: {source}
            </span>
            <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5">
              Target: {target}
            </span>
            <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5">
              Data: {dataType}
            </span>
          </div>
        </div>
        
        {/* Progress bar for running operations */}
        {status === 'running' && totalRecords && processedRecords && (
          <div className="mb-4">
            <ProgressBar 
              value={processedRecords} 
              max={totalRecords}
              showLabel
              labelFormat="fraction"
            />
          </div>
        )}
        
        {/* Error message */}
        {status === 'failed' && errorMessage && (
          <div className="mb-4 p-2 bg-error-50 border-l-4 border-error-500 text-error-700 text-sm">
            <div className="font-medium">Error:</div>
            <div>{errorMessage}</div>
          </div>
        )}
        
        {/* Results summary for completed operations */}
        {status === 'completed' && totalRecords && (
          <div className="mb-4 flex gap-4 text-sm">
            <div>
              <span className="font-medium">Total:</span> {totalRecords}
            </div>
            {processedRecords !== undefined && (
              <div>
                <span className="font-medium">Processed:</span> {processedRecords}
              </div>
            )}
            {failedRecords !== undefined && failedRecords > 0 && (
              <div className="text-error-600">
                <span className="font-medium">Failed:</span> {failedRecords}
              </div>
            )}
          </div>
        )}
        
        {/* Action buttons */}
        {showActions && (
          <div className="flex flex-wrap gap-2 mt-2 pt-3 border-t border-gray-100">
            <Button
              variant="outline"
              size="sm"
              onClick={handleViewDetails}
            >
              View Details
            </Button>
            
            {status !== 'cancelled' && (
              <Button
                variant={status === 'failed' ? 'error' : 'primary'}
                size="sm"
                onClick={handleRun}
                isLoading={isLoading}
                disabled={isRunButtonDisabled}
              >
                {getRunButtonLabel()}
              </Button>
            )}
            
            {status === 'running' && onCancel && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancel}
                disabled={isLoading}
              >
                Cancel
              </Button>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

export default SyncOperationCard;