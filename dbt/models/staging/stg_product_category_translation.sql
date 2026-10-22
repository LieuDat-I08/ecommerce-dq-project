WITH sources AS(
    SELECT * from {{source('raw_layer','product_category_translation')}}
),

renamed AS(
    SELECT

    LOWER(TRIM(product_category_name)) AS product_category_name,
    LOWER(TRIM(product_category_name_english)) AS product_category_name_english

    from sources
    where product_category_name IS NOT NULL
)

SELECT * from renamed