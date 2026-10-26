select user_id, experiment_id, variant, assigned_at
from {{ source('raw', 'raw_experiment_assignments') }}
