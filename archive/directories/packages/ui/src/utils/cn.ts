import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility function to combine and merge Tailwind CSS classes
 * 
 * Uses clsx for conditional class names and tailwind-merge to
 * handle conflicting Tailwind classes appropriately
 * 
 * @param {...ClassValue[]} inputs - Class values to be merged
 * @returns {string} - Merged className string
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}