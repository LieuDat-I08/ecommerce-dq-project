WITH source AS (

    SELECT * FROM {{ source('raw_layer', 'sellers') }}

),

renamed AS (

    SELECT
        -- Keys
        seller_id,

        -- Location
        LPAD(CAST(seller_zip_code_prefix AS STRING), 5, '0') AS zip_code_prefix,
        LOWER(TRIM(seller_city))                             AS city,
        UPPER(TRIM(seller_state))                            AS state

    FROM source
    WHERE seller_id IS NOT NULL

)

SELECT * FROM renamed