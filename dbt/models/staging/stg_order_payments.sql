WITH sources AS(
    SELECT * FROM {{ source('raw_layer','order_payments') }}
),

renamed AS(
    SELECT
    --keys
    order_id,
    payment_sequential,

    --payment info
    LOWER(TRIM(payment_type)) AS payment_type,
    payment_installments,
    CAST(payment_value AS NUMERIC) AS payment_value,

    -- Surrogate key (khóa chính ghép từ 2 cột)
        {{ dbt_utils.generate_surrogate_key(['order_id', 'payment_sequential']) }}
                                                as payment_id,
    
    from sources
    where order_id IS NOT NULL
)

SELECT * from renamed