select event_id, session_id, user_id, event_name, event_timestamp
from {{ source('raw', 'raw_events') }}
