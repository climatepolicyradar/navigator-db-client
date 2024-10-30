UPDATE corpus_type
SET valid_metadata = jsonb_set(
    valid_metadata,
    '{_event,event_type}',
    COALESCE(
        valid_metadata->'_event'->'event_type',
        jsonb_build_object(
            'allow_any', false,
            'allow_blanks', false,
            'allowed_values', (
                SELECT jsonb_agg(value)
                FROM jsonb_array_elements_text(
                    (
                        SELECT jsonb_path_query_first(
                            ct.valid_metadata,
                            '$.event_type.allowed_values'
                        )
                        FROM corpus_type ct
                        WHERE ct.name = corpus_type.name
                        LIMIT 1
                    )
                ) AS value
            )
        )
    )
)
WHERE NOT (valid_metadata ? '_event' AND valid_metadata->'_event' ? 'event_type');


WITH updated_values AS (
    SELECT
        name,
        CASE
            WHEN name IN ('Intl. agreements', 'Laws and Policies') THEN jsonb_build_array('Passed/Approved')
            WHEN name = 'GEF' THEN jsonb_build_array('Concept Approved')
            ELSE jsonb_build_array('Project Approved')
        END AS new_allowed_values
    FROM corpus_type
)
UPDATE corpus_type
SET valid_metadata = jsonb_set(
    valid_metadata,
    '{_event}',
    jsonb_build_object(
        'datetime_event_name',
        jsonb_build_object(
            'allow_any', false,
            'allow_blanks', false,
            'allowed_values', updated_values.new_allowed_values
        )
    )
)
FROM updated_values
WHERE corpus_type.name = updated_values.name
AND (
    NOT (valid_metadata ? '_event' AND valid_metadata->'_event' ? 'datetime_event_name')
    OR (valid_metadata->'_event'->'datetime_event_name' = '[]'::jsonb)
    OR valid_metadata->'_event' IS NULL
)
AND corpus_type.name IN (
    SELECT DISTINCT corpus_type_name
    FROM corpus
);
