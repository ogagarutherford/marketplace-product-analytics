select
    session_id,
    user_id,
    session_start,
    cast(session_start as date)  as session_date,
    channel,
    device,
    is_returning
from {{ source('raw', 'raw_sessions') }}
