WITH sources AS(
    SELECT * from {{source('raw_layer','products')}}
),

renamed AS(
    SELECT

    --keys
    product_id,
    
    --category
    LOWER(TRIM(product_category_name)) AS product_category_name,

    --listing info
     product_name_lenght                  as product_name_length,
    product_description_lenght           as product_description_length,
    product_photos_qty,
    
    --physical attribute
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm

    FROM sources
    WHERE product_id IS NOT NULL

)

SELECT * from renamed