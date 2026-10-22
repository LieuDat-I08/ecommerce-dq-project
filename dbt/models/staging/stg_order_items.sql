WITH source AS (

    SELECT * FROM {{ source('raw_layer', 'order_items') }}

),

renamed AS (

    SELECT
        -- Keys
        {{ dbt_utils.generate_surrogate_key(['order_id', 'order_item_id']) }} AS order_item_key,
        order_id,
        order_item_id,
        product_id,
        seller_id,

        -- Timestamps
        shipping_limit_date                  AS shipping_limit_at,

        -- Amounts
        CAST(price AS NUMERIC)               AS price,
        CAST(freight_value AS NUMERIC)       AS freight_value

    FROM source
    WHERE order_id IS NOT NULL
      AND order_item_id IS NOT NULL

)

SELECT * FROM renamed