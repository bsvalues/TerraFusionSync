import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, ProgressBar, TabGroup } from '@terrafusion/ui';

// Step interfaces
interface SystemSelection {
  source: string;
  target: string;
}

interface DataSettings {
  dataType: string;
  fields: string[];
  filters: string;
  mapping: Record<string, string>;
}

interface ScheduleSettings {
  frequency: 'once' | 'hourly' | 'daily' | 'weekly' | 'monthly';
  startDate: string;
  startTime: string;
  endDate?: string;
  isRecurring: boolean;
}

// Supported systems options
const availableSystems = [
  { id: 'erp', name: 'ERP System' },
  { id: 'crm', name: 'CRM Platform' },
  { id: 'ecommerce', name: 'E-commerce Platform' },
  { id: 'warehouse', name: 'Warehouse Management' },
  { id: 'marketplace', name: 'Online Marketplace' },
  { id: 'accounting', name: 'Accounting System' },
];

// Data types
const dataTypes = [
  { id: 'products', name: 'Products', fields: ['sku', 'name', 'description', 'price', 'inventory', 'category'] },
  { id: 'customers', name: 'Customers', fields: ['id', 'name', 'email', 'phone', 'address', 'segment'] },
  { id: 'orders', name: 'Orders', fields: ['id', 'customer_id', 'date', 'total', 'status', 'items'] },
  { id: 'inventory', name: 'Inventory', fields: ['sku', 'quantity', 'location', 'status', 'last_updated'] },
  { id: 'pricing', name: 'Pricing', fields: ['sku', 'base_price', 'discount', 'special_price', 'effective_date'] },
];

export const NewSyncWizard: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [wizardName, setWizardName] = useState('');
  const [systems, setSystems] = useState<SystemSelection>({ source: '', target: '' });
  const [dataSettings, setDataSettings] = useState<DataSettings>({
    dataType: '',
    fields: [],
    filters: '',
    mapping: {},
  });
  const [scheduleSettings, setScheduleSettings] = useState<ScheduleSettings>({
    frequency: 'once',
    startDate: new Date().toISOString().split('T')[0],
    startTime: '00:00',
    isRecurring: false,
  });

  // Progress tracking
  const totalSteps = 4;
  const progress = Math.round((currentStep / totalSteps) * 100);

  // Handle form submissions for each step
  const handleSystemsSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (systems.source && systems.target) {
      setCurrentStep(2);
    }
  };

  const handleDataSettingsSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (dataSettings.dataType && dataSettings.fields.length > 0) {
      setCurrentStep(3);
    }
  };

  const handleScheduleSettingsSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentStep(4);
  };

  const handleFinalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Combine all data
    const syncConfig = {
      name: wizardName,
      systems,
      dataSettings,
      scheduleSettings,
    };
    
    try {
      // In a real implementation, this would send to an API
      console.log('Creating sync operation with:', syncConfig);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Redirect to the sync dashboard with success message
      navigate('/sync-dashboard?created=true');
    } catch (error) {
      console.error('Error creating sync operation:', error);
      alert('Failed to create sync operation. Please try again.');
    }
  };

  // Handle going back to previous step
  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Cancel wizard and return to dashboard
  const handleCancel = () => {
    const confirmed = window.confirm('Are you sure you want to cancel? All progress will be lost.');
    if (confirmed) {
      navigate('/sync-dashboard');
    }
  };

  // Handle systems selection
  const handleSystemChange = (field: 'source' | 'target', value: string) => {
    setSystems({ ...systems, [field]: value });
  };

  // Handle data type selection
  const handleDataTypeChange = (dataTypeId: string) => {
    const selectedDataType = dataTypes.find(dt => dt.id === dataTypeId);
    if (selectedDataType) {
      setDataSettings({
        ...dataSettings,
        dataType: dataTypeId,
        fields: [], // Reset fields when data type changes
        mapping: {},
      });
    }
  };

  // Toggle field selection in data settings
  const toggleFieldSelection = (field: string) => {
    if (dataSettings.fields.includes(field)) {
      setDataSettings({
        ...dataSettings,
        fields: dataSettings.fields.filter(f => f !== field),
        // Remove any mapping for this field
        mapping: Object.entries(dataSettings.mapping)
          .filter(([key]) => key !== field)
          .reduce((obj, [key, value]) => ({ ...obj, [key]: value }), {}),
      });
    } else {
      setDataSettings({
        ...dataSettings,
        fields: [...dataSettings.fields, field],
        // Add default mapping (same field name)
        mapping: { ...dataSettings.mapping, [field]: field },
      });
    }
  };

  // Update field mapping
  const updateFieldMapping = (sourceField: string, targetField: string) => {
    setDataSettings({
      ...dataSettings,
      mapping: { ...dataSettings.mapping, [sourceField]: targetField },
    });
  };

  // Render wizard step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <form onSubmit={handleSystemsSubmit} className="space-y-6">
            <div>
              <label htmlFor="wizardName" className="block text-sm font-medium text-gray-700">
                Sync Operation Name
              </label>
              <input
                type="text"
                id="wizardName"
                value={wizardName}
                onChange={(e) => setWizardName(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="e.g., Product Catalog Sync"
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="sourceSystem" className="block text-sm font-medium text-gray-700">
                  Source System
                </label>
                <select
                  id="sourceSystem"
                  value={systems.source}
                  onChange={(e) => handleSystemChange('source', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  required
                >
                  <option value="">Select Source System</option>
                  {availableSystems.map((system) => (
                    <option key={system.id} value={system.id}>
                      {system.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="targetSystem" className="block text-sm font-medium text-gray-700">
                  Target System
                </label>
                <select
                  id="targetSystem"
                  value={systems.target}
                  onChange={(e) => handleSystemChange('target', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  required
                >
                  <option value="">Select Target System</option>
                  {availableSystems
                    .filter((system) => system.id !== systems.source)
                    .map((system) => (
                      <option key={system.id} value={system.id}>
                        {system.name}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            {systems.source && systems.target && (
              <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded-md">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm leading-5 text-blue-700">
                      Data will be synchronized from {availableSystems.find(s => s.id === systems.source)?.name} to {availableSystems.find(s => s.id === systems.target)?.name}.
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-between pt-4">
              <Button variant="secondary" onClick={handleCancel}>
                Cancel
              </Button>
              <Button type="submit" disabled={!systems.source || !systems.target || !wizardName}>
                Next: Configure Data
              </Button>
            </div>
          </form>
        );

      case 2:
        const selectedDataType = dataTypes.find(dt => dt.id === dataSettings.dataType);
        
        return (
          <form onSubmit={handleDataSettingsSubmit} className="space-y-6">
            <div>
              <label htmlFor="dataType" className="block text-sm font-medium text-gray-700">
                Data Type
              </label>
              <select
                id="dataType"
                value={dataSettings.dataType}
                onChange={(e) => handleDataTypeChange(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              >
                <option value="">Select Data Type</option>
                {dataTypes.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.name}
                  </option>
                ))}
              </select>
            </div>

            {selectedDataType && (
              <>
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Field Selection</h3>
                  <p className="text-xs text-gray-500 mb-3">
                    Select the fields you want to include in the synchronization.
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    {selectedDataType.fields.map((field) => (
                      <div key={field} className="flex items-center">
                        <input
                          type="checkbox"
                          id={`field-${field}`}
                          checked={dataSettings.fields.includes(field)}
                          onChange={() => toggleFieldSelection(field)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 rounded"
                        />
                        <label htmlFor={`field-${field}`} className="ml-2 text-sm text-gray-700">
                          {field}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                {dataSettings.fields.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Field Mapping</h3>
                    <p className="text-xs text-gray-500 mb-3">
                      Specify how fields from the source should map to the target.
                    </p>
                    <div className="space-y-3">
                      {dataSettings.fields.map((field) => (
                        <div key={field} className="grid grid-cols-5 gap-4 items-center">
                          <div className="col-span-2">
                            <span className="text-sm text-gray-700">{field}</span>
                          </div>
                          <div className="col-span-1 flex justify-center">
                            <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                            </svg>
                          </div>
                          <div className="col-span-2">
                            <input
                              type="text"
                              value={dataSettings.mapping[field] || field}
                              onChange={(e) => updateFieldMapping(field, e.target.value)}
                              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
                              placeholder="Target Field Name"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <label htmlFor="filters" className="block text-sm font-medium text-gray-700">
                    Filters (Optional)
                  </label>
                  <textarea
                    id="filters"
                    value={dataSettings.filters}
                    onChange={(e) => setDataSettings({ ...dataSettings, filters: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    placeholder="e.g., category = 'electronics' AND price > 100"
                    rows={3}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Enter conditions to filter the records. Use SQL-like syntax.
                  </p>
                </div>
              </>
            )}

            <div className="flex justify-between pt-4">
              <Button variant="secondary" onClick={handleBack}>
                Back
              </Button>
              <Button
                type="submit"
                disabled={!dataSettings.dataType || dataSettings.fields.length === 0}
              >
                Next: Schedule
              </Button>
            </div>
          </form>
        );

      case 3:
        return (
          <form onSubmit={handleScheduleSettingsSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Frequency
                </label>
                <select
                  value={scheduleSettings.frequency}
                  onChange={(e) => setScheduleSettings({
                    ...scheduleSettings,
                    frequency: e.target.value as any,
                    isRecurring: e.target.value !== 'once'
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="once">One-time</option>
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>

              <div>
                <div className="flex items-center h-9">
                  <input
                    type="checkbox"
                    id="isRecurring"
                    checked={scheduleSettings.isRecurring}
                    onChange={(e) => setScheduleSettings({
                      ...scheduleSettings,
                      isRecurring: e.target.checked,
                      frequency: e.target.checked ? (scheduleSettings.frequency === 'once' ? 'daily' : scheduleSettings.frequency) : 'once'
                    })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 rounded"
                  />
                  <label htmlFor="isRecurring" className="ml-2 text-sm text-gray-700">
                    Recurring Sync
                  </label>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="startDate" className="block text-sm font-medium text-gray-700">
                  Start Date
                </label>
                <input
                  type="date"
                  id="startDate"
                  value={scheduleSettings.startDate}
                  onChange={(e) => setScheduleSettings({ ...scheduleSettings, startDate: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  min={new Date().toISOString().split('T')[0]}
                  required
                />
              </div>

              <div>
                <label htmlFor="startTime" className="block text-sm font-medium text-gray-700">
                  Start Time
                </label>
                <input
                  type="time"
                  id="startTime"
                  value={scheduleSettings.startTime}
                  onChange={(e) => setScheduleSettings({ ...scheduleSettings, startTime: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            {scheduleSettings.isRecurring && (
              <div>
                <label htmlFor="endDate" className="block text-sm font-medium text-gray-700">
                  End Date (Optional)
                </label>
                <input
                  type="date"
                  id="endDate"
                  value={scheduleSettings.endDate || ''}
                  onChange={(e) => setScheduleSettings({ ...scheduleSettings, endDate: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  min={scheduleSettings.startDate}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Leave blank for indefinite recurrence.
                </p>
              </div>
            )}

            <div className="flex justify-between pt-4">
              <Button variant="secondary" onClick={handleBack}>
                Back
              </Button>
              <Button type="submit">
                Next: Review
              </Button>
            </div>
          </form>
        );

      case 4:
        const sourceSystem = availableSystems.find(s => s.id === systems.source)?.name;
        const targetSystem = availableSystems.find(s => s.id === systems.target)?.name;
        const dataTypeName = dataTypes.find(dt => dt.id === dataSettings.dataType)?.name;
        
        const frequencyText = {
          once: 'One-time',
          hourly: 'Hourly',
          daily: 'Daily',
          weekly: 'Weekly',
          monthly: 'Monthly',
        }[scheduleSettings.frequency];

        return (
          <form onSubmit={handleFinalSubmit} className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Review Sync Configuration</h3>
            
            <Card className="mt-4">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-500">Name</h4>
                  <p className="text-base font-medium text-gray-900">{wizardName}</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Source System</h4>
                    <p className="text-base font-medium text-gray-900">{sourceSystem}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Target System</h4>
                    <p className="text-base font-medium text-gray-900">{targetSystem}</p>
                  </div>
                </div>
              </div>
            </Card>
            
            <Card className="mt-4">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-500">Data Type</h4>
                  <p className="text-base font-medium text-gray-900">{dataTypeName}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-500">Selected Fields</h4>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {dataSettings.fields.map(field => (
                      <span 
                        key={field} 
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {field} → {dataSettings.mapping[field]}
                      </span>
                    ))}
                  </div>
                </div>
                {dataSettings.filters && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Filters</h4>
                    <p className="text-sm text-gray-700 bg-gray-50 p-2 rounded mt-1 font-mono">
                      {dataSettings.filters}
                    </p>
                  </div>
                )}
              </div>
            </Card>
            
            <Card className="mt-4">
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Frequency</h4>
                    <p className="text-base font-medium text-gray-900">{frequencyText}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Type</h4>
                    <p className="text-base font-medium text-gray-900">
                      {scheduleSettings.isRecurring ? 'Recurring' : 'One-time'}
                    </p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Start Date</h4>
                    <p className="text-base font-medium text-gray-900">
                      {new Date(scheduleSettings.startDate).toLocaleDateString()} at {scheduleSettings.startTime}
                    </p>
                  </div>
                  {scheduleSettings.isRecurring && scheduleSettings.endDate && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-500">End Date</h4>
                      <p className="text-base font-medium text-gray-900">
                        {new Date(scheduleSettings.endDate).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </Card>

            <div className="flex justify-between pt-4">
              <Button variant="secondary" onClick={handleBack}>
                Back
              </Button>
              <Button type="submit">
                Create Sync Operation
              </Button>
            </div>
          </form>
        );
        
      default:
        return null;
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">New Sync Operation</h1>
        <p className="text-gray-600">Configure a new data synchronization operation</p>
      </div>
      
      <div className="mb-8">
        <ProgressBar
          progress={progress}
          showPercentage
          label={`Step ${currentStep} of ${totalSteps}`}
          color="blue"
          size="md"
        />
      </div>
      
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="p-6">
          <TabGroup
            tabs={[
              { id: '1', label: 'Systems', content: null, disabled: currentStep !== 1 },
              { id: '2', label: 'Data', content: null, disabled: currentStep < 2 },
              { id: '3', label: 'Schedule', content: null, disabled: currentStep < 3 },
              { id: '4', label: 'Review', content: null, disabled: currentStep < 4 },
            ]}
            defaultTab={currentStep.toString()}
            onChange={(tabId) => {
              const step = parseInt(tabId);
              if (step <= currentStep) {
                setCurrentStep(step);
              }
            }}
          />
          
          <div className="mt-6">
            {renderStepContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewSyncWizard;