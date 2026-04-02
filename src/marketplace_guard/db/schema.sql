PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    currency TEXT NOT NULL DEFAULT 'CLP'
);

CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    default_fee_pct REAL NOT NULL,
    default_shipping_cost REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    channel_sku TEXT NOT NULL,
    publication_id TEXT NOT NULL,
    listing_status TEXT NOT NULL DEFAULT 'active',
    inventory_qty INTEGER NOT NULL DEFAULT 0,
    avg_daily_units REAL NOT NULL DEFAULT 0,
    UNIQUE(product_id, channel_id)
);

CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES listings(id),
    captured_at TEXT NOT NULL,
    list_price REAL NOT NULL,
    sale_price REAL,
    final_price REAL NOT NULL,
    fee_amount REAL NOT NULL,
    shipping_subsidy_amount REAL NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'mock_feed'
);

CREATE TABLE IF NOT EXISTS costs (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    effective_from TEXT NOT NULL,
    unit_cost REAL NOT NULL,
    handling_cost REAL NOT NULL DEFAULT 0,
    min_margin_amount REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS promotions (
    id INTEGER PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES listings(id),
    promo_type TEXT NOT NULL,
    discount_type TEXT NOT NULL,
    discount_value REAL NOT NULL,
    funded_by TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    product_id INTEGER NOT NULL REFERENCES products(id),
    listing_id INTEGER REFERENCES listings(id),
    title TEXT NOT NULL,
    explanation TEXT NOT NULL,
    estimated_loss REAL NOT NULL,
    impact_score REAL NOT NULL,
    priority_score REAL NOT NULL,
    estimated_loss_component REAL NOT NULL,
    negative_margin_component REAL NOT NULL,
    volume_component REAL NOT NULL,
    suggested_action TEXT NOT NULL,
    dedupe_key TEXT NOT NULL UNIQUE,
    evidence_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS action_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL REFERENCES alerts(id),
    action_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    status TEXT NOT NULL,
    approval_status TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    requested_at TEXT NOT NULL,
    executed_at TEXT,
    result_json TEXT NOT NULL
);
