INSERT OR IGNORE INTO products (id, sku, name, brand, category, status, currency) VALUES
    (1, 'SKU-RUN-001', 'Nike Pegasus 40 Black 42', 'Nike', 'running_shoes', 'active', 'CLP'),
    (2, 'SKU-HEAD-002', 'Sony WH-1000XM5 Black', 'Sony', 'audio', 'active', 'CLP'),
    (3, 'SKU-HOME-003', 'Stanley Quencher 1.2L Cream', 'Stanley', 'home', 'active', 'CLP');

INSERT OR IGNORE INTO channels (id, code, name, default_fee_pct, default_shipping_cost, status) VALUES
    (1, 'ml_cl', 'Mercado Libre Chile', 0.15, 3500, 'active'),
    (2, 'falabella', 'Falabella Marketplace', 0.18, 2500, 'active'),
    (3, 'ripley', 'Ripley Marketplace', 0.17, 3000, 'active');

INSERT OR IGNORE INTO listings (
    id, product_id, channel_id, channel_sku, publication_id, listing_status, inventory_qty, avg_daily_units
) VALUES
    (101, 1, 1, 'PEG40-BLK-42-ML', 'ML-9981', 'active', 18, 6.2),
    (102, 1, 2, 'PEG40-BLK-42-FAL', 'FAL-2231', 'active', 12, 3.4),
    (103, 1, 3, 'PEG40-BLK-42-RIP', 'RIP-4412', 'active', 9, 2.8),
    (201, 2, 1, 'XM5-BLK-ML', 'ML-9002', 'active', 7, 1.8),
    (202, 2, 2, 'XM5-BLK-FAL', 'FAL-9022', 'active', 5, 1.1),
    (301, 3, 1, 'STAN-12-ML', 'ML-7001', 'active', 25, 4.0),
    (302, 3, 2, 'STAN-12-FAL', 'FAL-7009', 'active', 16, 2.6);

INSERT OR IGNORE INTO costs (id, product_id, effective_from, unit_cost, handling_cost, min_margin_amount) VALUES
    (1, 1, '2026-04-01T00:00:00Z', 45000, 1500, 4000),
    (2, 2, '2026-04-01T00:00:00Z', 210000, 2500, 15000),
    (3, 3, '2026-04-01T00:00:00Z', 18000, 500, 2000);

INSERT OR IGNORE INTO prices (
    id, listing_id, captured_at, list_price, sale_price, final_price, fee_amount, shipping_subsidy_amount, source
) VALUES
    (1001, 101, '2026-04-02T10:00:00Z', 62990, 52990, 52990, 7948.5, 3500, 'seed'),
    (1002, 102, '2026-04-02T10:00:00Z', 69990, 69990, 69990, 12598.2, 2500, 'seed'),
    (1003, 103, '2026-04-02T10:00:00Z', 68990, 68990, 68990, 11728.3, 3000, 'seed'),
    (2001, 201, '2026-04-02T10:00:00Z', 299990, 269990, 269990, 40498.5, 4500, 'seed'),
    (2002, 202, '2026-04-02T10:00:00Z', 289990, 289990, 289990, 52198.2, 3500, 'seed'),
    (3001, 301, '2026-04-02T10:00:00Z', 32990, 31990, 31990, 4798.5, 3200, 'seed'),
    (3002, 302, '2026-04-02T10:00:00Z', 33990, 32990, 32990, 5938.2, 2400, 'seed');

INSERT OR IGNORE INTO promotions (
    id, listing_id, promo_type, discount_type, discount_value, funded_by, starts_at, ends_at, status
) VALUES
    (9001, 201, 'flash_sale', 'percent', 10, 'seller', '2026-04-01T00:00:00Z', '2026-04-04T23:59:59Z', 'active'),
    (9002, 301, 'price_drop', 'amount', 1000, 'seller', '2026-04-01T00:00:00Z', '2026-04-10T23:59:59Z', 'active');
