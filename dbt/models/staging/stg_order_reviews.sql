WITH sources AS (
    SELECT * from {{ source('raw_layer','order_reviews') }}
),

renamed AS (
    SELECT
    --keys
        review_id,
        order_id,

        -- review_info
        review_score,
        NULLIF(TRIM(review_comment_title), '') AS comment_title,
        NULLIF(TRIM(review_comment_message), '') AS comment_message,
        review_creation_date AS creation_date,
        review_answer_timestamp AS answer_timestamp,
        {{ dbt_utils.generate_surrogate_key(['review_id', 'order_id']) }} as review_key

    from sources
    WHERE
        review_id IS NOT NULL
        AND order_id IS NOT NULL
)

SELECT * from renamed
