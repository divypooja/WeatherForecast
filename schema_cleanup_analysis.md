# Database Schema Cleanup Analysis

## Summary of Findings

Based on comprehensive analysis of the codebase, we have identified several areas for schema optimization:

### Models Usage Analysis

**Models in Active Use (11/30):**
- CompanySettings ✓
- Supplier ✓  
- Item ✓
- SalesOrder ✓
- Employee ✓
- JobWorkRate ✓
- JobWork ✓
- JobWorkBatch ✓
- Production ✓
- BOM ✓
- BOMProcess ✓

**Potentially Unused Models (19/30):**
- ItemBatch ⚠️ (Actually used in batch tracking - analysis was incorrect)
- ItemType ⚠️
- PurchaseOrder ⚠️ (Actually used - analysis was incorrect)
- PurchaseOrderItem ⚠️
- SalesOrderItem ⚠️
- JobWorkTeamAssignment ⚠️
- JobWorkProcess ⚠️
- ProductionBatch ⚠️
- BOMItem ⚠️
- QualityIssue ⚠️
- QualityControlLog ⚠️
- NotificationSettings ⚠️
- DeliverySchedule ⚠️
- MaterialInspection ⚠️
- FactoryExpense ⚠️
- SalaryRecord ⚠️
- EmployeeAdvance ⚠️
- EmployeeAttendance ⚠️
- DailyJobWorkEntry ⚠️

## Issues Identified

### 1. SQLAlchemy Relationship Warnings
The system is showing relationship overlap warnings:
- `PurchaseOrderItem.item` conflicts with `Item.purchase_order_items`
- `SalesOrderItem.item` conflicts with `Item.sales_order_items`  
- `GRNLineItem.grn` conflicts with `GRN.line_items`

### 2. Field Name Inconsistencies
- Some models use `created_date` while others use `created_at`
- Fixed in batch tracking: `created_date` → `created_at`

### 3. Duplicate/Legacy Fields
Many models have duplicate fields for backward compatibility:
- `current_stock` vs multi-state inventory fields (`qty_raw`, `qty_wip`, etc.)
- Legacy WIP fields vs process-specific WIP fields
- Duplicate quantity/price fields in order items

## Recommended Actions

### Phase 1: Critical Fixes (Immediate)
1. **Fix SQLAlchemy Relationship Warnings**
   - Add proper `overlaps` parameters to relationships
   - Clean up conflicting backref declarations

2. **Standardize Field Names**
   - Ensure all datetime fields use `created_at`/`updated_at` pattern
   - Fix any remaining `created_date` references

### Phase 2: Schema Optimization (Using Flask-Migrate)
1. **Remove Legacy Fields**
   - `Item.current_stock` (replaced by multi-state inventory)
   - `ItemBatch.qty_wip` (replaced by process-specific WIP fields)
   - Duplicate fields in PO/SO items

2. **Consolidate Related Models**
   - Review if some models can be merged or simplified
   - Remove truly unused models after thorough verification

3. **Add Missing Indexes**
   - Add indexes on frequently queried fields
   - Add composite indexes for common query patterns

### Phase 3: Performance Optimization
1. **Database Constraints**
   - Add proper foreign key constraints
   - Add check constraints for business rules
   - Add unique constraints where needed

2. **Table Optimization**
   - Review table sizes and partition if needed
   - Optimize column types and sizes

## Migration Strategy

### Setup Flask-Migrate
```bash
# Initialize migrations
flask db init

# Create initial migration
flask db migrate -m "Initial schema baseline"

# Apply migration
flask db upgrade
```

### Incremental Changes
1. Create small, focused migrations
2. Test each migration thoroughly
3. Keep rollback scripts ready
4. Document all changes

## Files to Modify

### 1. Fix Relationship Warnings
- `models.py` - Add overlaps parameters
- Test all affected relationships

### 2. Remove Legacy Fields
- Create migration to drop unused columns
- Update all queries to use new field names
- Update forms and templates

### 3. Add Proper Constraints
- Foreign key constraints
- Check constraints for business rules
- Unique constraints for codes/numbers

## Risk Assessment

**Low Risk:**
- Adding overlaps parameters to relationships
- Standardizing field names (already partially done)

**Medium Risk:**
- Removing legacy fields (need thorough testing)
- Adding new constraints (may reveal data integrity issues)

**High Risk:**
- Dropping unused tables (need 100% verification)
- Major schema restructuring

## Next Steps

1. **Immediate**: Fix SQLAlchemy warnings and test application
2. **Short term**: Set up Flask-Migrate and create baseline migration
3. **Medium term**: Remove legacy fields in phases
4. **Long term**: Optimize schema for performance

## Notes
- The analysis incorrectly flagged some models as unused (ItemBatch, PurchaseOrder, etc.)
- Need manual verification before dropping any tables
- User specifically wants to preserve accounting section integrity
- Batch tracking is actively used and should not be modified