import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { Toast, ToastContainer, ToastPosition, ToastVariant } from './Toast';

// Toast item type
export interface ToastItem {
  id: string;
  message: string;
  title?: string;
  variant?: ToastVariant;
  duration?: number | null;
  action?: {
    label: string;
    onClick: (id: string) => void;
  };
}

// Toast context state
interface ToastState {
  toasts: ToastItem[];
  position: ToastPosition;
}

// Toast actions
type ToastAction =
  | { type: 'ADD_TOAST'; toast: ToastItem }
  | { type: 'REMOVE_TOAST'; id: string }
  | { type: 'SET_POSITION'; position: ToastPosition };

// Toast context type
interface ToastContextType {
  toasts: ToastItem[];
  position: ToastPosition;
  addToast: (toast: Omit<ToastItem, 'id'>) => string;
  removeToast: (id: string) => void;
  setPosition: (position: ToastPosition) => void;
}

// Create the context
const ToastContext = createContext<ToastContextType | undefined>(undefined);

// Toast reducer
const toastReducer = (state: ToastState, action: ToastAction): ToastState => {
  switch (action.type) {
    case 'ADD_TOAST':
      return {
        ...state,
        toasts: [...state.toasts, action.toast],
      };
    case 'REMOVE_TOAST':
      return {
        ...state,
        toasts: state.toasts.filter((toast) => toast.id !== action.id),
      };
    case 'SET_POSITION':
      return {
        ...state,
        position: action.position,
      };
    default:
      return state;
  }
};

// Generate a unique ID
const generateId = (): string => {
  return Math.random().toString(36).substr(2, 9);
};

// Toast provider
export const ToastProvider: React.FC<{
  children: React.ReactNode;
  defaultPosition?: ToastPosition;
}> = ({ children, defaultPosition = 'top-right' }) => {
  const [state, dispatch] = useReducer(toastReducer, {
    toasts: [],
    position: defaultPosition,
  });

  // Add a toast
  const addToast = useCallback((toast: Omit<ToastItem, 'id'>): string => {
    const id = generateId();
    dispatch({
      type: 'ADD_TOAST',
      toast: { id, ...toast },
    });
    return id;
  }, []);

  // Remove a toast
  const removeToast = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_TOAST', id });
  }, []);

  // Set position
  const setPosition = useCallback((position: ToastPosition) => {
    dispatch({ type: 'SET_POSITION', position });
  }, []);

  return (
    <ToastContext.Provider
      value={{
        toasts: state.toasts,
        position: state.position,
        addToast,
        removeToast,
        setPosition,
      }}
    >
      {children}
      <ToastContainer position={state.position}>
        {state.toasts.map((toast) => (
          <Toast
            key={toast.id}
            id={toast.id}
            title={toast.title}
            message={toast.message}
            variant={toast.variant}
            duration={toast.duration}
            action={toast.action}
            onDismiss={removeToast}
          />
        ))}
      </ToastContainer>
    </ToastContext.Provider>
  );
};

// Custom hook to use the toast context
export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  
  return context;
};

// Convenience functions
export const useToastFunctions = () => {
  const { addToast } = useToast();
  
  return {
    /**
     * Show an information toast
     */
    info: (message: string, options?: Partial<Omit<ToastItem, 'id' | 'message' | 'variant'>>) => {
      return addToast({ message, variant: 'info', ...options });
    },
    
    /**
     * Show a success toast
     */
    success: (message: string, options?: Partial<Omit<ToastItem, 'id' | 'message' | 'variant'>>) => {
      return addToast({ message, variant: 'success', ...options });
    },
    
    /**
     * Show a warning toast
     */
    warning: (message: string, options?: Partial<Omit<ToastItem, 'id' | 'message' | 'variant'>>) => {
      return addToast({ message, variant: 'warning', ...options });
    },
    
    /**
     * Show an error toast
     */
    error: (message: string, options?: Partial<Omit<ToastItem, 'id' | 'message' | 'variant'>>) => {
      return addToast({ message, variant: 'error', ...options });
    },
  };
};