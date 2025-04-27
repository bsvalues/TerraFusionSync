import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, ProgressBar } from '@terrafusion/ui';

interface SyncSystem {
  id: string;
  name: string;
  description: string;
  category: string;
}

export const NewSyncWizard: React.FC = () => {
  const navigate = useNavigate();
  
  // State for wizard steps
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 4;
  
  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [syncType, setSyncType] = useState('Full Sync');
  const [sourceSystem, setSourceSystem] = useState('');
  const [targetSystem, setTargetSystem] = useState('');
  const [isScheduled, setIsScheduled] = useState(false);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  const [advancedOptions, setAdvancedOptions] = useState(false);
  const [validationRules, setValidationRules] = useState(true);
  const [errorHandling, setErrorHandling] = useState('stop');
  
  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [systems, setSystems] = useState<SyncSystem[]>([]);
  const [systemsLoading, setSystemsLoading] = useState(true);
  
  // Load available systems for source and target dropdowns
  useEffect(() => {
    const fetchSystems = async () => {
      try {
        setSystemsLoading(true);
        const response = await fetch('/api/marketplace-sync/systems');
        if (!response.ok) {
          throw new Error(`Failed to fetch systems: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        setSystems(data);
      } catch (err) {
        console.error('Error fetching systems:', err);
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setSystemsLoading(false);
      }
    };

    fetchSystems();
  }, []);
  
  // Handle form submission
  const handleSubmit = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Build the payload
      const payload = {
        name,
        description,
        syncType,
        sourceSystem,
        targetSystem,
        scheduled: isScheduled,
        scheduleDate: isScheduled ? scheduleDate : null,
        scheduleTime: isScheduled ? scheduleTime : null,
        options: {
          validationRules,
          errorHandling
        }
      };
      
      // Send the request
      const response = await fetch('/api/marketplace-sync/operations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create sync operation: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Navigate to the created sync operation
      navigate(`/marketplace/sync/${data.id}`);
    } catch (err) {
      console.error('Error creating sync operation:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      setCurrentStep(4); // Move to the review step to show the error
    } finally {
      setIsLoading(false);
    }
  };
  
  // Navigation functions
  const goToNextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };
  
  const goToPreviousStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Rendering the step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div>
            <h2 className="text-lg font-medium mb-4">Basic Information</h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Sync Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Give your sync operation a descriptive name"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Describe the purpose of this sync operation"
                />
              </div>
              
              <div>
                <label htmlFor="syncType" className="block text-sm font-medium text-gray-700">
                  Sync Type <span className="text-red-500">*</span>
                </label>
                <select
                  id="syncType"
                  value={syncType}
                  onChange={(e) => setSyncType(e.target.value)}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                >
                  <option value="Full Sync">Full Sync</option>
                  <option value="Incremental Sync">Incremental Sync</option>
                  <option value="Delta Sync">Delta Sync</option>
                </select>
                <p className="mt-1 text-sm text-gray-500">
                  {syncType === 'Full Sync' 
                    ? 'Synchronizes all data from the source to the target.'
                    : syncType === 'Incremental Sync'
                    ? 'Only synchronizes data that has changed since the last sync.'
                    : 'Advanced mode that identifies precise changes in individual records.'}
                </p>
              </div>
            </div>
          </div>
        );
        
      case 2:
        return (
          <div>
            <h2 className="text-lg font-medium mb-4">Source and Target</h2>
            <div className="space-y-6">
              <div>
                <label htmlFor="sourceSystem" className="block text-sm font-medium text-gray-700">
                  Source System <span className="text-red-500">*</span>
                </label>
                {systemsLoading ? (
                  <div className="mt-1 flex items-center">
                    <div className="animate-spin h-5 w-5 border-t-2 border-b-2 border-blue-500 rounded-full mr-2"></div>
                    <span className="text-sm text-gray-500">Loading systems...</span>
                  </div>
                ) : (
                  <>
                    <select
                      id="sourceSystem"
                      value={sourceSystem}
                      onChange={(e) => setSourceSystem(e.target.value)}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    >
                      <option value="">Select a source system</option>
                      {systems.map((system) => (
                        <option key={`source-${system.id}`} value={system.id}>
                          {system.name} ({system.category})
                        </option>
                      ))}
                    </select>
                    {sourceSystem && (
                      <p className="mt-1 text-sm text-gray-500">
                        {systems.find(s => s.id === sourceSystem)?.description}
                      </p>
                    )}
                  </>
                )}
              </div>
              
              <div className="flex justify-center">
                <svg className="h-8 w-8 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>
              
              <div>
                <label htmlFor="targetSystem" className="block text-sm font-medium text-gray-700">
                  Target System <span className="text-red-500">*</span>
                </label>
                {systemsLoading ? (
                  <div className="mt-1 flex items-center">
                    <div className="animate-spin h-5 w-5 border-t-2 border-b-2 border-blue-500 rounded-full mr-2"></div>
                    <span className="text-sm text-gray-500">Loading systems...</span>
                  </div>
                ) : (
                  <>
                    <select
                      id="targetSystem"
                      value={targetSystem}
                      onChange={(e) => setTargetSystem(e.target.value)}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    >
                      <option value="">Select a target system</option>
                      {systems.map((system) => (
                        <option key={`target-${system.id}`} value={system.id} disabled={system.id === sourceSystem}>
                          {system.name} ({system.category})
                        </option>
                      ))}
                    </select>
                    {targetSystem && (
                      <p className="mt-1 text-sm text-gray-500">
                        {systems.find(s => s.id === targetSystem)?.description}
                      </p>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        );
        
      case 3:
        return (
          <div>
            <h2 className="text-lg font-medium mb-4">Schedule and Options</h2>
            <div className="space-y-6">
              <div>
                <div className="flex items-center">
                  <input
                    id="isScheduled"
                    type="checkbox"
                    checked={isScheduled}
                    onChange={(e) => setIsScheduled(e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="isScheduled" className="ml-2 block text-sm font-medium text-gray-700">
                    Schedule this sync for later
                  </label>
                </div>
              </div>
              
              {isScheduled && (
                <div className="ml-6 space-y-4 border-l-2 border-gray-200 pl-4">
                  <div>
                    <label htmlFor="scheduleDate" className="block text-sm font-medium text-gray-700">
                      Date <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      id="scheduleDate"
                      value={scheduleDate}
                      onChange={(e) => setScheduleDate(e.target.value)}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      required={isScheduled}
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="scheduleTime" className="block text-sm font-medium text-gray-700">
                      Time <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="time"
                      id="scheduleTime"
                      value={scheduleTime}
                      onChange={(e) => setScheduleTime(e.target.value)}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      required={isScheduled}
                    />
                  </div>
                </div>
              )}
              
              <div className="pt-4">
                <button
                  type="button"
                  onClick={() => setAdvancedOptions(!advancedOptions)}
                  className="text-sm font-medium text-blue-600 hover:text-blue-500 flex items-center"
                >
                  {advancedOptions ? 'Hide Advanced Options' : 'Show Advanced Options'}
                  <svg className={`ml-1 h-5 w-5 transform ${advancedOptions ? 'rotate-180' : ''}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
              
              {advancedOptions && (
                <div className="space-y-4 border-l-2 border-gray-200 pl-4">
                  <div>
                    <div className="flex items-center">
                      <input
                        id="validationRules"
                        type="checkbox"
                        checked={validationRules}
                        onChange={(e) => setValidationRules(e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="validationRules" className="ml-2 block text-sm font-medium text-gray-700">
                        Apply validation rules to sync data
                      </label>
                    </div>
                    <p className="mt-1 text-sm text-gray-500 ml-6">
                      Validates data against schema rules before sending to the target system.
                    </p>
                  </div>
                  
                  <div>
                    <label htmlFor="errorHandling" className="block text-sm font-medium text-gray-700">
                      Error Handling Strategy
                    </label>
                    <select
                      id="errorHandling"
                      value={errorHandling}
                      onChange={(e) => setErrorHandling(e.target.value)}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    >
                      <option value="stop">Stop on Error</option>
                      <option value="continue">Continue on Error</option>
                      <option value="retry">Retry Failed Items</option>
                    </select>
                    <p className="mt-1 text-sm text-gray-500">
                      {errorHandling === 'stop' 
                        ? 'Operation will stop if any error is encountered.'
                        : errorHandling === 'continue'
                        ? 'Operation will continue despite errors and log failures.'
                        : 'Failed items will be retried up to 3 times before being marked as failed.'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
        
      case 4:
        return (
          <div>
            <h2 className="text-lg font-medium mb-4">Review and Create</h2>
            
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4 text-red-700">
                <p className="font-medium">Error creating sync operation</p>
                <p className="text-sm mt-1">{error}</p>
              </div>
            )}
            
            <div className="rounded-md bg-blue-50 p-4 mb-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-blue-700">
                    Please review your sync configuration before creating the operation. Once created, you can monitor and manage the sync operation from the dashboard.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Sync Operation Summary
                </h3>
              </div>
              <div className="border-t border-gray-200">
                <dl>
                  <div className="bg-gray-50 px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">Name</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{name || '(Not provided)'}</dd>
                  </div>
                  <div className="bg-white px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">Description</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{description || '(Not provided)'}</dd>
                  </div>
                  <div className="bg-gray-50 px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">Sync Type</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{syncType}</dd>
                  </div>
                  <div className="bg-white px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">Source System</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {sourceSystem ? systems.find(s => s.id === sourceSystem)?.name : '(Not selected)'}
                    </dd>
                  </div>
                  <div className="bg-gray-50 px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">Target System</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {targetSystem ? systems.find(s => s.id === targetSystem)?.name : '(Not selected)'}
                    </dd>
                  </div>
                  <div className="bg-white px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                    <dt className="text-sm font-medium text-gray-500">Schedule</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                      {isScheduled 
                        ? `${scheduleDate} at ${scheduleTime}`
                        : 'Run immediately after creation'}
                    </dd>
                  </div>
                  {advancedOptions && (
                    <>
                      <div className="bg-gray-50 px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Validation Rules</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                          {validationRules ? 'Enabled' : 'Disabled'}
                        </dd>
                      </div>
                      <div className="bg-white px-4 py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Error Handling</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                          {errorHandling === 'stop' 
                            ? 'Stop on Error' 
                            : errorHandling === 'continue' 
                            ? 'Continue on Error'
                            : 'Retry Failed Items'}
                        </dd>
                      </div>
                    </>
                  )}
                </dl>
              </div>
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };
  
  // Validation for the current step
  const isStepValid = () => {
    switch (currentStep) {
      case 1:
        return name.trim() !== '';
      case 2:
        return sourceSystem !== '' && targetSystem !== '';
      case 3:
        return !isScheduled || (scheduleDate !== '' && scheduleTime !== '');
      default:
        return true;
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Create New Sync Operation</h1>
      
      {/* Progress bar */}
      <div className="mb-8">
        <ProgressBar 
          value={currentStep} 
          max={totalSteps}
          label={`Step ${currentStep} of ${totalSteps}`}
          showValue
        />
      </div>
      
      {/* Step content */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-8">
        {renderStepContent()}
      </div>
      
      {/* Navigation buttons */}
      <div className="flex justify-between">
        <div>
          {currentStep > 1 && (
            <Button 
              variant="secondary" 
              onClick={goToPreviousStep}
              disabled={isLoading}
            >
              Back
            </Button>
          )}
        </div>
        <div className="flex space-x-3">
          <Button 
            variant="secondary" 
            onClick={() => navigate('/marketplace/sync')}
            disabled={isLoading}
          >
            Cancel
          </Button>
          
          {currentStep < totalSteps ? (
            <Button 
              variant="primary" 
              onClick={goToNextStep}
              disabled={!isStepValid() || isLoading}
            >
              Next
            </Button>
          ) : (
            <Button 
              variant="primary" 
              onClick={handleSubmit}
              isLoading={isLoading}
              loadingText="Creating..."
              disabled={!isStepValid() || isLoading}
            >
              Create Sync Operation
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};