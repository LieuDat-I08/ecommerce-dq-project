WITH source AS (

    SELECT * FROM {{ source('raw_layer', 'geolocation') }}

),

cleaned AS (

    SELECT
        LPAD(CAST(geolocation_zip_code_prefix AS STRING), 5, '0') AS zip_code_prefix,
        geolocation_lat,
        geolocation_lng,
        LOWER(TRIM(geolocation_city))                             AS geolocation_city,
        UPPER(TRIM(geolocation_state))                            AS geolocation_state

    FROM source
    WHERE geolocation_zip_code_prefix IS NOT NULL
      AND geolocation_lat IS NOT NULL
      AND geolocation_lng IS NOT NULL
      -- Giới hạn tọa độ trong lãnh thổ Brazil, loại điểm sai
      AND geolocation_lat BETWEEN -34 AND 6
      AND geolocation_lng BETWEEN -74 AND -34

)

SELECT * FROM cleaned