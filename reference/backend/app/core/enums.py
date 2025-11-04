from enum import Enum

class BaseJobStatus(str, Enum):
    """
    Defines the fundamental lifecycle statuses applicable to all types of jobs
    in the system. This provides a consistent, high-level view of any job's state.
    """
    PENDING = "pending"          # The job has been created and is awaiting processing.
    IN_PROGRESS = "in_progress"  # The job is actively being processed.
    COMPLETED = "completed"      # The job finished all its tasks successfully.
    FAILED = "failed"            # The job terminated due to an unrecoverable error.
    CANCELLED = "cancelled"      # The job was cancelled by a user or the system.

class ModelStatus(str, Enum):
    """Defines the loading status of an AI model."""
    NOT_LOADED = "NOT_LOADED"
    LOADING = "LOADING"
    LOADED = "LOADED"
    FAILED = "FAILED"
