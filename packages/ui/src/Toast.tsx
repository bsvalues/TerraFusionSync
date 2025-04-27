import React from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';
export type ToastPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';

export interface ToastProps {
  id: string;
  type: ToastType;
  title?: string;
  description?: string;
  duration?: number;
  onClose: (id: string) => void;
  isClosable?: boolean;
}

const typeStyles: Record<ToastType, { bgColor: string; icon: JSX.Element }> = {
  success: {
    bgColor: 'bg-green-100 border-l-4 border-green-500',
    icon: (
      <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
  },
  error: {
    bgColor: 'bg-red-100 border-l-4 border-red-500',
    icon: (
      <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
  },
  warning: {
    bgColor: 'bg-yellow-100 border-l-4 border-yellow-500',
    icon: (
      <svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
  },
  info: {
    bgColor: 'bg-blue-100 border-l-4 border-blue-500',
    icon: (
      <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
};

export const Toast: React.FC<ToastProps> = ({
  id,
  type,
  title,
  description,
  onClose,
  isClosable = true,
}) => {
  React.useEffect(() => {
    const timer = setTimeout(() => {
      onClose(id);
    }, 5000); // Default duration

    return () => clearTimeout(timer);
  }, [id, onClose]);

  const { bgColor, icon } = typeStyles[type];

  return (
    <div className={`flex items-start p-4 mb-4 w-full max-w-sm rounded-md shadow-md ${bgColor}`}>
      <div className="flex-shrink-0">{icon}</div>
      <div className="ml-3 flex-1">
        {title && <h3 className="text-sm font-medium">{title}</h3>}
        {description && <div className="mt-1 text-sm text-gray-600">{description}</div>}
      </div>
      {isClosable && (
        <button
          type="button"
          className="ml-4 inline-flex text-gray-400 focus:outline-none focus:text-gray-500 rounded-md p-1.5 hover:bg-gray-200"
          onClick={() => onClose(id)}
        >
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      )}
    </div>
  );
};

export const ToastContainer: React.FC<{
  position?: ToastPosition;
  children: React.ReactNode;
}> = ({ position = 'top-right', children }) => {
  const positionStyles: Record<ToastPosition, string> = {
    'top-right': 'top-0 right-0',
    'top-left': 'top-0 left-0',
    'bottom-right': 'bottom-0 right-0',
    'bottom-left': 'bottom-0 left-0',
    'top-center': 'top-0 left-1/2 transform -translate-x-1/2',
    'bottom-center': 'bottom-0 left-1/2 transform -translate-x-1/2',
  };

  return (
    <div
      className={`fixed ${positionStyles[position]} p-4 w-full max-w-sm pointer-events-none z-50 flex flex-col items-end`}
    >
      {children}
    </div>
  );
};