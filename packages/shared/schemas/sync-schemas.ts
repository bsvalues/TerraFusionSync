import { z } from 'zod';

// Base schemas for sync operations
export const CreateSyncSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  source: z.string().min(1, 'Source system is required'),
  target: z.string().min(1, 'Target system is required'),
  dataType: z.string().min(1, 'Data type is required'),
  fields: z.array(z.string()).min(1, 'At least one field must be selected'),
  fieldMapping: z.record(z.string()),
  filters: z.string().optional(),
  schedule: z.object({
    frequency: z.enum(['once', 'hourly', 'daily', 'weekly', 'monthly']),
    startDate: z.string(),
    startTime: z.string(),
    endDate: z.string().optional(),
    isRecurring: z.boolean()
  })
});

export const UpdateSyncSchema = z.object({
  name: z.string().optional(),
  status: z.enum(['active', 'paused', 'cancelled']).optional(),
  schedule: z.object({
    frequency: z.enum(['once', 'hourly', 'daily', 'weekly', 'monthly']),
    startDate: z.string(),
    startTime: z.string(),
    endDate: z.string().optional(),
    isRecurring: z.boolean()
  }).optional()
});

export const FilterSyncSchema = z.object({
  page: z.number().optional().default(1),
  limit: z.number().optional().default(20),
  status: z.enum(['active', 'completed', 'failed', 'pending', 'scheduled']).optional(),
  source: z.string().optional(),
  target: z.string().optional(),
  dataType: z.string().optional(),
  fromDate: z.string().optional(),
  toDate: z.string().optional()
});

// Extract types from the schemas for TypeScript usage
export type CreateSyncInput = z.infer<typeof CreateSyncSchema>;
export type UpdateSyncInput = z.infer<typeof UpdateSyncSchema>;
export type FilterSyncInput = z.infer<typeof FilterSyncSchema>;