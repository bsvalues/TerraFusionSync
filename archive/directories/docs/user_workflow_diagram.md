# TerraFusion Platform - User Workflow Diagram

## Main User Flows

```
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│               │       │               │       │               │
│  Login Page   ├──────►│  Dashboard    ├──────►│ Feature Select │
│               │       │               │       │               │
└───────────────┘       └───────────────┘       └───────┬───────┘
                                                        │
                                                        ▼
                        ┌─────────────────────────────────────────────────┐
                        │                                                 │
                        ▼                                                 ▼
             ┌───────────────────┐                           ┌──────────────────┐
             │                   │                           │                  │
             │  Sync Operations  │                           │   GIS Export     │
             │                   │                           │                  │
             └───────┬───────────┘                           └──────┬───────────┘
                     │                                              │
     ┌───────────────┼───────────────────┐             ┌────────────┼───────────────┐
     │               │                   │             │            │               │
     ▼               ▼                   ▼             ▼            ▼               ▼
┌─────────┐    ┌──────────┐      ┌────────────┐   ┌─────────┐  ┌─────────┐   ┌──────────┐
│         │    │          │      │            │   │         │  │         │   │          │
│ View    │    │ Create   │      │ Monitor    │   │ Create  │  │ View    │   │ Download │
│ Pairs   │    │ Pair     │      │ Operations │   │ Export  │  │ Jobs    │   │ Results  │
│         │    │          │      │            │   │         │  │         │   │          │
└─────────┘    └──────────┘      └────────────┘   └─────────┘  └─────────┘   └──────────┘
```

## GIS Export Detailed Workflow

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│             │      │             │      │             │      │             │
│  Select     │─────►│  Configure  │─────►│  Submit     │─────►│  Monitor    │
│  County     │      │  Export     │      │  Job        │      │  Status     │
│             │      │             │      │             │      │             │
└─────────────┘      └─────────────┘      └─────────────┘      └──────┬──────┘
                                                                      │
                                                                      │
                                   ┌─────────────────────────────────┐│
                                   │                                 ││
                                   ▼                                 ▼▼
                        ┌─────────────────┐             ┌─────────────────┐
                        │                 │             │                 │
                        │  Error/Failure  │             │  Success/       │
                        │  State          │             │  Download       │
                        │                 │             │                 │
                        └─────────────────┘             └─────────────────┘
```

## Decision Points and State Transitions

### Authentication 
- **Entry Point**: Login page
- **Decision Point**: Valid credentials? → Yes: Dashboard, No: Error message
- **State Transition**: Unauthenticated → Authenticated

### Dashboard
- **Entry Point**: Post-login or navigation
- **Decision Point**: Select feature
- **State Transition**: Overview → Feature context

### Sync Operations
- **Entry Point**: Dashboard or direct navigation
- **Decision Points**:
  - View existing pairs
  - Create new pair
  - Monitor operations
- **State Transitions**:
  - New pair: Configuration → Validation → Saved
  - Operations: Pending → Running → Completed/Failed

### GIS Export
- **Entry Point**: Dashboard or direct navigation
- **Decision Points**:
  - Select county and format
  - Configure export parameters 
  - Submit job
  - Monitor status
  - Download or handle errors
- **State Transitions**:
  - Job: Created → Pending → Running → Completed/Failed
  - Download: Available → Downloaded
  
### Feedback Loops
- Success feedback:
  - Sync pair created: Success message → View pairs
  - Sync operation completed: Success notification → View results
  - GIS Export completed: Success message → Download option

- Error feedback:
  - Authentication fails: Error message → Retry
  - Validation fails: Error indicators → Fix inputs
  - Operation fails: Error notification → View details/Retry