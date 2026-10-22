WITH sources AS (
    SELECT * FROM {{source('raw_layer','customers')}}
),

renamed AS (
    SELECT

        customer_id,
        customer_unique_id,
        -- cột zip code đổi sang string với 5 số 
        LPAD(CAST(customer_zip_code_prefix AS string), 5, '0')
            AS zip_code_prefix,
        LOWER(TRIM(customer_city)) AS city,
        UPPER(TRIM(customer_state)) AS state

    from sources
    WHERE customer_id is not null
)

SELECT * from renamed
