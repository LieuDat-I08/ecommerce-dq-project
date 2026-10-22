WITH source AS (
    SELECT * FROM {{source('raw_layer', 'orders')}}
),

renamed AS (
    SELECT
        -- Keys
        order_id,
        customer_id,

        -- Status
        order_status,
        -- Những cột đổi tên cho ngắn gọn
        order_purchase_timestamp AS purchased_at,
        order_approved_at AS approved_at,
        order_delivered_carrier_date AS shipped_at,
        order_delivered_customer_date AS delivered_at,
        order_estimated_delivery_date AS estimated_delivery_at

    FROM source
    -- Đảm bảo không lấy các dòng rác thiếu khóa chính
    WHERE order_id IS NOT NULL
)

SELECT * FROM renamed
