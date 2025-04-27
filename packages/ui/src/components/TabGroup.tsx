import React, { useState } from 'react';

export interface Tab {
  id: string;
  label: string;
  content: React.ReactNode;
  disabled?: boolean;
}

export interface TabGroupProps {
  tabs: Tab[];
  defaultTab?: string;
  onChange?: (tabId: string) => void;
  variant?: 'pills' | 'underline' | 'blocks';
  className?: string;
}

export const TabGroup: React.FC<TabGroupProps> = ({
  tabs,
  defaultTab,
  onChange,
  variant = 'underline',
  className = '',
}) => {
  const initialTab = defaultTab || (tabs.length > 0 ? tabs[0].id : '');
  const [activeTab, setActiveTab] = useState(initialTab);

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    if (onChange) {
      onChange(tabId);
    }
  };

  // Get variant classes
  const getVariantClasses = (isActive: boolean, isDisabled: boolean) => {
    if (isDisabled) {
      return 'text-gray-400 cursor-not-allowed';
    }

    switch (variant) {
      case 'pills':
        return isActive
          ? 'bg-blue-100 text-blue-700 font-medium'
          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100';
      case 'blocks':
        return isActive
          ? 'bg-white text-blue-700 font-medium border-t border-l border-r border-gray-200'
          : 'bg-gray-100 text-gray-500 hover:text-gray-700 border border-gray-200';
      case 'underline':
      default:
        return isActive
          ? 'text-blue-600 border-b-2 border-blue-600 font-medium'
          : 'text-gray-500 hover:text-gray-700 hover:border-gray-300 border-b-2 border-transparent';
    }
  };

  return (
    <div className={`w-full ${className}`}>
      <div className={`border-b border-gray-200 ${variant === 'blocks' ? 'border-b-0' : ''}`}>
        <nav className="-mb-px flex space-x-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && handleTabChange(tab.id)}
              className={`py-2 px-4 text-sm inline-flex items-center ${getVariantClasses(
                activeTab === tab.id,
                !!tab.disabled
              )}`}
              aria-current={activeTab === tab.id ? 'page' : undefined}
              disabled={tab.disabled}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="mt-4">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            className={activeTab === tab.id ? 'block' : 'hidden'}
            role="tabpanel"
            aria-labelledby={`tab-${tab.id}`}
          >
            {tab.content}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TabGroup;