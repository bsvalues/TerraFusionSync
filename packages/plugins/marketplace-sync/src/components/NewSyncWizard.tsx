import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, ProgressBar } from '@terrafusion/ui';

interface SyncSystem {
  id: string;
  name: string;
  icon: string;
  description: string;
  category: string;
}

interface SyncConfiguration {
  name: string;
  description: string;
  sourceSystem: string | null;
  targetSystem: string | null;
  syncType: 'full' | 'incremental' | null;
  schedule: 'manual' | 'hourly' | 'daily' | 'weekly' | 'monthly' | null;
}

const AVAILABLE_SYSTEMS: SyncSystem[] = [
  {
    id: 'crm1',
    name: 'SalesForceCRM',
    icon: '💼',
    description: 'CRM system for customer relationship management',
    category: 'CRM'
  },
  {
    id: 'warehouse1',
    name: 'TerraWarehouse',
    icon: '🏭',
    description: 'Warehouse management system',
    category: 'Logistics'
  },
  {
    id: 'ecommerce1',
    name: 'ShopifyConnect',
    icon: '🛒',
    description: 'E-commerce platform connector',
    category: 'E-commerce'
  },
  {
    id: 'accounting1',
    name: 'QuickBooks',
    icon: '📊',
    description: 'Accounting software',
    category: 'Finance'
  },
  {
    id: 'datawarehouse1',
    name: 'TerraDW',
    icon: '🗄️',
    description: 'Enterprise data warehouse',
    category: 'Data'
  },
  {
    id: 'marketing1',
    name: 'MarketingHub',
    icon: '📱',
    description: 'Marketing automation platform',
    category: 'Marketing'
  }
];

export const NewSyncWizard: React.FC = () => {
  const [step, setStep] = useState(1);
  const [configuration, setConfiguration] = useState<SyncConfiguration>({
    name: '',
    description: '',
    sourceSystem: null,
    targetSystem: null,
    syncType: null,
    schedule: null
  });
  const navigate = useNavigate();

  const handleNext = () => {
    setStep(step + 1);
  };

  const handleBack = () => {
    setStep(step - 1);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real implementation, this would submit the configuration to the API
    console.log('Sync configuration submitted:', configuration);
    navigate('/marketplace/sync');
  };

  const updateConfiguration = (updates: Partial<SyncConfiguration>) => {
    setConfiguration((prev) => ({ ...prev, ...updates }));
  };

  const selectSystem = (systemId: string, type: 'source' | 'target') => {
    if (type === 'source') {
      updateConfiguration({ sourceSystem: systemId });
    } else {
      updateConfiguration({ targetSystem: systemId });
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-4">Create New Sync Operation</h1>
        <ProgressBar 
          value={step} 
          max={4} 
          showValue 
          size="md" 
          colorScheme="blue" 
          label="Wizard Progress" 
        />
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        {step === 1 && (
          <div>
            <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="syncName" className="block text-sm font-medium text-gray-700 mb-1">
                  Sync Operation Name
                </label>
                <input
                  type="text"
                  id="syncName"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={configuration.name}
                  onChange={(e) => updateConfiguration({ name: e.target.value })}
                  placeholder="e.g., Weekly Customer Data Sync"
                />
              </div>
              <div>
                <label htmlFor="syncDescription" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  id="syncDescription"
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={configuration.description}
                  onChange={(e) => updateConfiguration({ description: e.target.value })}
                  placeholder="Describe the purpose of this sync operation"
                />
              </div>
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <h2 className="text-xl font-semibold mb-4">Select Source System</h2>
            <p className="text-gray-600 mb-4">Choose the system you want to sync data from:</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {AVAILABLE_SYSTEMS.map((system) => (
                <div 
                  key={system.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    configuration.sourceSystem === system.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                  }`}
                  onClick={() => selectSystem(system.id, 'source')}
                >
                  <div className="flex items-start">
                    <div className="text-3xl mr-3">{system.icon}</div>
                    <div>
                      <h3 className="font-medium">{system.name}</h3>
                      <p className="text-sm text-gray-600">{system.description}</p>
                      <span className="inline-block mt-2 px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full">
                        {system.category}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <h2 className="text-xl font-semibold mb-4">Select Target System</h2>
            <p className="text-gray-600 mb-4">Choose the system you want to sync data to:</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {AVAILABLE_SYSTEMS
                .filter(system => system.id !== configuration.sourceSystem)
                .map((system) => (
                  <div 
                    key={system.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                      configuration.targetSystem === system.id 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                    }`}
                    onClick={() => selectSystem(system.id, 'target')}
                  >
                    <div className="flex items-start">
                      <div className="text-3xl mr-3">{system.icon}</div>
                      <div>
                        <h3 className="font-medium">{system.name}</h3>
                        <p className="text-sm text-gray-600">{system.description}</p>
                        <span className="inline-block mt-2 px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full">
                          {system.category}
                        </span>
                      </div>
                    </div>
                  </div>
              ))}
            </div>
          </div>
        )}

        {step === 4 && (
          <div>
            <h2 className="text-xl font-semibold mb-4">Sync Configuration</h2>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-base font-medium mb-2">Sync Type</h3>
                <div className="flex flex-col space-y-2">
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      className="form-radio h-5 w-5 text-blue-600"
                      name="syncType"
                      value="full"
                      checked={configuration.syncType === 'full'}
                      onChange={() => updateConfiguration({ syncType: 'full' })}
                    />
                    <span className="ml-2">Full Sync (All Data)</span>
                  </label>
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      className="form-radio h-5 w-5 text-blue-600"
                      name="syncType"
                      value="incremental"
                      checked={configuration.syncType === 'incremental'}
                      onChange={() => updateConfiguration({ syncType: 'incremental' })}
                    />
                    <span className="ml-2">Incremental Sync (New & Changed Data Only)</span>
                  </label>
                </div>
              </div>
              
              <div>
                <h3 className="text-base font-medium mb-2">Schedule</h3>
                <select
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={configuration.schedule || ''}
                  onChange={(e) => updateConfiguration({ schedule: e.target.value as any })}
                >
                  <option value="">Select a schedule...</option>
                  <option value="manual">Manual (On demand only)</option>
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-base font-medium mb-2">Summary</h3>
                <div className="space-y-2 text-sm">
                  <p><strong>Name:</strong> {configuration.name || 'Not specified'}</p>
                  <p><strong>Source:</strong> {AVAILABLE_SYSTEMS.find(s => s.id === configuration.sourceSystem)?.name || 'Not selected'}</p>
                  <p><strong>Target:</strong> {AVAILABLE_SYSTEMS.find(s => s.id === configuration.targetSystem)?.name || 'Not selected'}</p>
                  <p><strong>Type:</strong> {configuration.syncType === 'full' ? 'Full Sync' : configuration.syncType === 'incremental' ? 'Incremental Sync' : 'Not selected'}</p>
                  <p><strong>Schedule:</strong> {configuration.schedule ? configuration.schedule.charAt(0).toUpperCase() + configuration.schedule.slice(1) : 'Not selected'}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-between mt-8">
          {step > 1 ? (
            <Button variant="secondary" onClick={handleBack}>
              Back
            </Button>
          ) : (
            <div></div> // Empty div to maintain spacing
          )}
          
          {step < 4 ? (
            <Button 
              onClick={handleNext}
              disabled={
                (step === 1 && !configuration.name) ||
                (step === 2 && !configuration.sourceSystem) ||
                (step === 3 && !configuration.targetSystem)
              }
            >
              Next
            </Button>
          ) : (
            <Button 
              variant="success"
              onClick={handleSubmit}
              disabled={!configuration.syncType || !configuration.schedule}
            >
              Create Sync
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};