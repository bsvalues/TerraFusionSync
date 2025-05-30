import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Spinner } from 'reactstrap';

// Animated Badge component
export const AnimatedBadge = ({ color, children, className = '', ...props }) => {
  return (
    <motion.span
      className={`badge bg-${color} ${className}`}
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      {...props}
    >
      {children}
    </motion.span>
  );
};

// Animated Card component
export const AnimatedCard = ({ children, className = '', ...props }) => {
  return (
    <motion.div
      className={`card shadow-sm ${className}`}
      initial={{ y: 10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: -10, opacity: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ y: -2, boxShadow: '0 8px 20px rgba(0,0,0,0.1)' }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

// Animated Button component
export const AnimatedButton = ({ color, children, className = '', ...props }) => {
  return (
    <motion.button
      className={`btn btn-${color} ${className}`}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      {...props}
    >
      {children}
    </motion.button>
  );
};

// Animated Table Row component
export const AnimatedTableRow = ({ index = 0, children, ...props }) => {
  return (
    <motion.tr
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
      whileHover={{ backgroundColor: 'rgba(0,0,0,0.03)' }}
      {...props}
    >
      {children}
    </motion.tr>
  );
};

// Animated Progress Bar component
export const AnimatedProgress = ({ value, color = 'primary', className = '', ...props }) => {
  return (
    <div className={`progress ${className}`} {...props}>
      <motion.div
        className={`progress-bar bg-${color}`}
        initial={{ width: '0%' }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin="0"
        aria-valuemax="100"
      />
    </div>
  );
};

// Animated Spinner component
export const AnimatedSpinner = ({ color = 'primary', ...props }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1, rotate: 360 }}
      transition={{ duration: 0.5, type: 'spring' }}
      {...props}
    >
      <Spinner color={color} />
    </motion.div>
  );
};

// Animated Alert component
export const AnimatedAlert = ({ color, children, className = '', ...props }) => {
  return (
    <motion.div
      className={`alert alert-${color} ${className}`}
      initial={{ opacity: 0, scale: 0.9, y: -10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: -10 }}
      transition={{ duration: 0.3 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

// Animated List component
export const AnimatedList = ({ children }) => {
  return (
    <AnimatePresence>
      {children}
    </AnimatePresence>
  );
};

// Animate items when they're created or deleted
export const AnimatedItem = ({ children, index = 0, ...props }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

// Animated Count component for number transitions
export const AnimatedCount = ({ value, className = '', ...props }) => {
  return (
    <motion.span
      className={className}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      key={value}
      {...props}
    >
      <motion.span
        key={value}
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 20, opacity: 0 }}
        transition={{ duration: 0.3 }}
      >
        {value}
      </motion.span>
    </motion.span>
  );
};

// Data refresh animation
export const DataRefreshIndicator = ({ isRefreshing }) => {
  return (
    <AnimatePresence>
      {isRefreshing && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="position-fixed top-0 start-50 translate-middle-x"
          style={{ zIndex: 1050 }}
        >
          <motion.div
            className="alert alert-info d-inline-block py-1 px-3 shadow"
            animate={{ y: ['-100%', '0%'] }}
            exit={{ y: '-100%' }}
            transition={{ duration: 0.3 }}
          >
            <small>
              <Spinner size="sm" className="me-2" />
              Refreshing data...
            </small>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Animated Notification component
export const AnimatedNotification = ({ message, isVisible, type = 'info', onClose }) => {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="position-fixed top-0 end-0 m-3"
          style={{ zIndex: 1060 }}
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 50 }}
          transition={{ duration: 0.3 }}
        >
          <div className={`alert alert-${type} shadow d-flex align-items-center`}>
            <div className="flex-grow-1">
              {message}
            </div>
            {onClose && (
              <button
                type="button"
                className="btn-close ms-2"
                aria-label="Close"
                onClick={onClose}
              />
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};