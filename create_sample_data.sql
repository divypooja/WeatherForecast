-- Create sample item if not exists
INSERT OR IGNORE INTO items (code, name, unit_of_measure, current_stock) 
VALUES ('PROD-001', 'Sample Product A', 'pcs', 0);

-- Create sample productions if not exists
INSERT OR IGNORE INTO productions (
    production_number, item_id, quantity_planned, status, 
    production_date, created_by, created_at
) VALUES 
    ('PROD-2025-001', 1, 100, 'planned', DATE('now'), 1, DATETIME('now')),
    ('PROD-2025-002', 1, 50, 'in_progress', DATE('now'), 1, DATETIME('now')),
    ('PROD-2025-003', 1, 25, 'completed', DATE('now'), 1, DATETIME('now'));
