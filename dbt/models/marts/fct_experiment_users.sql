-- Grain: one row per user assigned to the checkout experiment.
-- Outcomes are measured from first exposure (assigned_at) to the end of the window.
with assignments as (
    select * from {{ ref('stg_experiment_assignments') }}
    where experiment_id = '{{ var("experiment_id") }}'
),

exposed_sessions as (
    select a.user_id, s.session_id, s.session_start, s.device, s.purchased, s.net_revenue_eur
    from assignments a
    join {{ ref('fct_sessions') }} s
      on s.user_id = a.user_id
     and s.session_start >= a.assigned_at
     and s.session_start < cast('{{ var("experiment_end") }}' as timestamp)
),

first_device as (
    select user_id, device as first_exposure_device
    from (select *, row_number() over (partition by user_id order by session_start, session_id) as n from exposed_sessions)
    where n = 1
),

per_user as (
    select
        user_id,
        count(*)                    as exposed_sessions,
        sum(purchased)              as purchasing_sessions,
        max(purchased)              as converted,
        sum(net_revenue_eur)        as revenue_eur
    from exposed_sessions
    group by user_id
)

select
    a.user_id,
    a.experiment_id,
    a.variant,
    a.assigned_at,
    d.first_exposure_device,
    p.exposed_sessions,
    p.purchasing_sessions,
    p.converted,
    p.revenue_eur
from assignments a
join per_user p using (user_id)
join first_device d using (user_id)
