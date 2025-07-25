# Factory Management System - Flask Application

## Overview

This is a comprehensive Flask-based Factory Management System designed for small to medium manufacturing companies. The application provides modular dashboards for managing various aspects of factory operations including inventory, purchase orders, sales, HR, job work, production, and reporting.

## Recent Changes (January 25, 2025)

### Complete Employee Attendance Management System Implementation (Latest - January 25, 2025)
- **Comprehensive Attendance Tracking**: Created complete EmployeeAttendance model with full attendance lifecycle management including check-in/out times, status tracking, and automatic hours calculation
- **Advanced Attendance Forms**: Built AttendanceForm and BulkAttendanceForm with comprehensive validation, employee selection, date/time inputs, and status/leave type management
- **Professional Management Interface**: Complete attendance dashboard with filtering by employee, date range, and status with pagination support and comprehensive attendance statistics
- **Full CRUD Operations**: Implemented add, edit, list, detail view, and delete functionality for attendance records with proper validation and duplicate prevention
- **Bulk Attendance Processing**: Added bulk attendance feature allowing marking all active employees as present for selected date with automatic conflict detection
- **Real-time Hours Calculation**: Automatic calculation of regular hours, overtime hours, and total working time with configurable overtime thresholds
- **Status Badge System**: Visual status indicators (Present/Absent/Late/Half Day/On Leave) with color-coded badges and professional UI styling
- **HR Dashboard Integration**: Enhanced HR dashboard with today's attendance statistics (Total Marked, Present, Absent, On Leave) with real-time data
- **Employee Detail Integration**: Added attendance quick action buttons to employee detail pages for marking attendance and viewing history
- **Advanced Filtering System**: Comprehensive filtering by employee, date range, and status with preserved filter states and results counter
- **Leave Type Management**: Support for different leave types (Sick Leave, Casual Leave, Annual Leave, Emergency Leave) with conditional form display
- **Time Management Tools**: Built-in "Set Current Time" buttons for check-in/out times with JavaScript helpers for improved user experience
- **Attendance History Tracking**: Complete audit trail with record creation timestamps, marked by user tracking, and comprehensive attendance detail views
- **Navigation Integration**: Added attendance sections to HR navigation with proper routing and template structure throughout system

### Complete Salary and Advance Payment Integration with Factory Expenses (January 25, 2025)
- **Pay Period Auto-Population**: Implemented API endpoint `/api/employee/<id>/hire-date` and JavaScript functionality to automatically populate Pay Period Start with employee's hire date when creating salary records
- **Salary Payment Workflow**: Enhanced salary detail pages with "Mark as Paid" functionality that automatically creates corresponding Factory Expense records in "Salaries & Benefits" category with complete financial details
- **Advance Payment Integration**: Added advance payment processing that creates Factory Expense records when advances are marked as paid, including employee details, reason, and repayment information
- **Enhanced Employee Detail Page**: Created comprehensive employee detail template with quick action buttons for creating salary records and advances directly from employee management interface
- **Automated Expense Generation**: When salaries or advances are marked as paid, system automatically generates expense records with proper categorization, descriptions, and financial tracking
- **Workflow Streamlining**: Complete integration allows Employee Management → Salary/Advance Creation → Admin Approval → Mark as Paid → Automatic Factory Expense Record Creation workflow
- **CSRF Token Fix**: Resolved template error in expenses list page by removing undefined CSRF token references, ensuring smooth expense management functionality

### Complete OCR Receipt Processing System Implementation (January 25, 2025)
- **Smart Receipt Processing Section**: Added comprehensive OCR section to Factory Expenses form with professional "NEW" badge and success color scheme
- **Image Upload with Camera Support**: File input with camera capture capability accepting images (PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP) and PDF files
- **OCR Backend Endpoint**: Created `/process_ocr` endpoint in expenses routes for processing uploaded receipt/invoice images with proper file validation and error handling
- **Auto-Data Extraction**: System extracts key fields including Date, Amount (base/tax breakdown), Vendor, Invoice Number, Category, GST Rate, and GSTIN from receipts
- **Professional Preview Interface**: Two-column extracted data display with financial data (amounts, GST) and document data (date, category, confidence score)
- **Apply to Form Functionality**: One-click application of extracted OCR data to expense form fields with real-time total calculation and success notifications
- **Review/Edit Workflow**: Emphasized user review capability with clear warnings to verify extracted data before applying, ensuring accuracy as requested
- **Demo Mode Implementation**: Currently running in demo mode with simulated OCR results while resolving OpenCV/Tesseract dependencies
- **Error Handling & Validation**: Comprehensive file type validation, temporary file management, and graceful error handling with user-friendly messages
- **Confidence Score Display**: Visual progress bar showing OCR processing accuracy with color-coded confidence levels (green/yellow/red)
- **Enhanced User Experience**: Loading animations, clear/apply buttons, auto-dismiss notifications, and professional styling throughout OCR workflow

## Recent Changes (January 25, 2025)

### Complete Department Management System Implementation (Latest - January 25, 2025)
- **Database Architecture**: Created comprehensive Department model with name, code, description, and active status fields
- **Dynamic Employee Form Enhancement**: Updated EmployeeForm to dynamically load department choices from database instead of hardcoded options
- **Professional Management Interface**: Built complete department management dashboard with statistics, employee counts by department, and recent departments display
- **Full CRUD Operations**: Implemented add, edit, list, activate/deactivate, and soft delete functionality for departments
- **Settings Integration**: Added "Department Management" card to Settings dashboard for easy access
- **Default Department Initialization**: System automatically creates 12 manufacturing departments on first database access
- **Security & Validation**: Admin-only access with duplicate prevention, code validation (lowercase with underscores), and employee safety checks
- **UI/UX Polish**: Fixed duplicate "Item Types Management" sections in settings dashboard, maintaining clean interface
- **Blueprint Integration**: Registered department blueprint with proper URL routing and navigation integration
- **Employee Creation Bug Fix**: Resolved field name mismatches (hire_date vs joining_date) and form validation issues that prevented employee saving
- **Document Management Fix**: Fixed URL routing parameter mismatch in documents list template for download/view functionality

### Complete Job Work Rates Management System (Latest - January 25, 2025)
- **Job Work Rates Table**: Created comprehensive rates management with fields - Item Code, Item Name, Rate Job Work as requested
- **Complete CRUD Operations**: Full add, edit, list, and delete functionality for job work rates
- **Professional Dashboard**: Statistics showing total rates, items with rates, average rate, and inactive rates
- **Advanced Filtering**: Search by item name/code and filter by process type with pagination support
- **Vertical Scrolling**: Items Without Rates section with scrollable interface showing 10 items with sticky headers
- **Auto-Rate Loading**: Job Work form automatically loads rates from rates table when item/process is selected
- **Process-Specific Rates**: Support for different rates per manufacturing process (optional general rates)
- **Smart Rate Lookup**: Finds process-specific rates first, falls back to general rates for flexibility
- **Navigation Integration**: Accessible from Job Work dashboard quick actions (removed from main sidebar to avoid duplication)
- **Real-time Feedback**: Shows "Rate loaded from rates table" notification when rates auto-populate in job work form
- **Duplicate Prevention**: System prevents duplicate rates for same item/process combination
- **Total Job Cost Calculation**: Real-time calculation and display of total job cost (Quantity × Rate) in job work forms and lists
- **Work Type Classification**: Added in-house vs outsourced categorization for job work operations with visual badges and dashboard statistics

### Job Work Preview Functionality Removed (January 25, 2025)
- **Preview Button Removed**: Removed preview button from Job Work form as requested by user for simplified interface
- **Preview Modal Removed**: Deleted entire preview modal structure and associated HTML elements
- **JavaScript Cleanup**: Removed all preview-related JavaScript functions (previewJobWork, createPreviewContent, showPreviewModal, loadStockAnalysis)
- **Simplified Form Interface**: Job Work form now has clean, streamlined interface with only Cancel and Save buttons
- **Code Optimization**: Eliminated unnecessary preview-related code for better performance and maintainability

### Complete Job Work Enhancement with Process Types and Scrap Management
- **Process Type Selection**: Successfully implemented process field in JobWork forms allowing selection from 8 manufacturing processes (Zinc, Cutting, Bending, Welding, Painting, Assembly, Machining, Polishing)
- **Scrap Management Integration**: Added Expected Finished Material and Expected Scrap fields for processes where scrap is applicable, allowing better material planning and waste tracking
- **Database Schema Enhancement**: Added process, expected_finished_material, and expected_scrap columns to job_works table with proper data types and defaults
- **Form Field Resolution**: Resolved WTForms naming conflict by using 'process_type' field name internally while displaying as 'Process' to users
- **Comprehensive Form Layout**: Enhanced JobWork form with three-row layout including process selection, quantity management (sent/finished/scrap), and scheduling fields
- **Route Integration**: Updated both add and edit JobWork routes to handle all new fields (process, expected_finished_material, expected_scrap) during creation and modification
- **Preview System Enhancement**: Enhanced JobWork preview system to display process with badge styling and show expected finished material and scrap quantities
- **Template Updates**: Added all new fields to JobWork form template with proper validation, help text, and professional styling
- **Complete CRUD Operations**: All new fields fully integrated across create, read, update operations with proper form validation and database persistence

### Enhanced Job Work Forms with Real-time Inventory Checking and Universal Preview System
- **Real-time Stock Validation**: Enhanced Job Work forms with "Check Stock" button providing instant inventory availability checks before quantity operations
- **Insufficient Stock Prevention**: System prevents overselling by displaying clear warnings when requested quantity exceeds available stock with color-coded alerts (red for insufficient, yellow for low stock, green for adequate)
- **Universal Preview System**: Created comprehensive JavaScript framework for form preview functionality across all major forms (Job Work, Inventory, Production, Purchase Orders, Sales Orders)
- **API Stock Endpoint**: Added secure API endpoint `/inventory/api/item-stock/<id>` for real-time inventory data with proper authentication and error handling
- **Modal Preview Interface**: Professional preview modals show complete form data before submission with calculated totals and formatted display
- **Automatic Stock Monitoring**: Job Work forms automatically check stock when items or quantities change, providing immediate feedback to users
- **Enhanced User Experience**: Preview buttons added to Job Work, Inventory, and Production forms with "Save" option directly from preview modal
- **Form Validation Integration**: Preview system validates form data and displays warnings for missing or invalid information before allowing submission
- **Professional UI Design**: Consistent preview interface with proper Bootstrap styling, icons, and responsive layout across all form types

### Complete Rectpack Integration for Manufacturing Optimization (Latest)
- **Advanced Rectangle Packing Library**: Integrated Rectpack Python library providing comprehensive 2D rectangle packing algorithms for manufacturing optimization
- **Material Cutting Optimization**: Created complete material cutting optimization system supporting sheet metal, wood, glass, and fabric cutting with multiple algorithms (Skyline, MaxRects, Guillotine)
- **Production Layout Optimization**: Implemented inventory layout optimization for warehouse space utilization and storage arrangement
- **Multi-Algorithm Support**: Three distinct packing algorithms each optimized for different scenarios (speed vs quality vs balanced performance)
- **Manufacturing Integration**: Direct integration with Purchase Orders and BOMs for automated cutting pattern generation from production requirements
- **Professional Dashboard**: Comprehensive packing optimization dashboard with real-time statistics, quick actions, and algorithm performance comparison
- **Cost Savings Analysis**: Automatic calculation of material waste reduction, cost savings, and efficiency improvements from optimized cutting patterns
- **Visual Layout System**: Interactive cutting layout visualization with SVG-based diagrams showing part placement and rotation optimization
- **Export Capabilities**: JSON export of cutting plans for CNC programming and manufacturing execution
- **Navigation Integration**: Added Packing Optimization to main sidebar navigation and dashboard module system with proper routing and template structure

### Extended Business Partner Types with Vendor and Transporter Support (Latest)
- **Extended Partner Types**: Added "Vendor" and "Transporter" to business partner system expanding from 3 to 5 partner types (Supplier, Customer, Vendor, Transporter, Both)
- **Enhanced Form Integration**: Updated SupplierForm with new partner type choices and comprehensive dropdown options
- **Visual Differentiation**: Added color-coded badges for new partner types (Vendor: warning/orange, Transporter: secondary/gray)
- **Model Property Updates**: Extended Supplier model with new is_vendor and is_transporter properties for type checking
- **Purchase Order Integration**: Updated PO form to include vendors in supplier selection dropdown since vendors can supply materials
- **Database Schema Support**: Enhanced partner_type column to support vendor and transporter values with proper model constraints
- **Unified Business Logic**: Maintained unified business partner architecture while expanding type flexibility for diverse business relationships

### Enhanced BOM System with Unit Selection and Markup (Latest)
- **BOM Unit Selection**: Added unit field to BOMItem model allowing selection of different units (pcs, kg, g, nos, m, cm, l, ml, sqft, sqm) for each material in BOM independent of inventory item's default unit
- **Database Schema Updates**: Added unit column to bom_items table with default 'pcs' value for flexible unit specification per BOM material
- **Enhanced BOM Forms**: Updated BOMItemForm with unit selection dropdown and enhanced BOM form template with unit field integration
- **Production Route Updates**: Modified add_bom_item route to handle unit field when adding materials to BOM
- **BOM Display Enhancement**: Updated BOM templates to show selected units instead of default item units for better production planning clarity
- **Markup System Integration**: Added markup_percentage field to BOM model for profit margin calculations applied to total cost (material + labor + overhead + freight)
- **Cost Calculation Enhancement**: Enhanced total_cost_per_unit property to include markup calculations with separate markup_amount_per_unit property for detailed breakdown
- **Professional Markup Interface**: Added markup section to BOM form with percentage input and helpful description, integrated markup row in cost breakdown table
- **Database Migration**: Added markup_percentage column to boms table with proper default values for existing records
- **Comprehensive Cost Transparency**: BOM cost breakdown now shows all components including markup percentage and amount for complete cost visibility

### Dynamic Item Type Management System (Latest)
- **Custom Item Types**: Implemented complete ItemType model with dynamic management allowing users to create custom item categories beyond default Material/Product/Consumable
- **Database Architecture**: Created item_types table with foreign key relationships to items table, maintaining backward compatibility with legacy item_type string field
- **Admin Interface**: Full CRUD operations for item types with admin-only access restrictions and soft delete capabilities
- **Default Types Provided**: System initializes with 6 default types (Material, Product, Consumable, Tool, Spare Part, Packaging) with auto-creation on first use
- **Smart Form Integration**: Enhanced ItemForm with dynamic item type dropdown populated from database with direct management link
- **Professional UI**: Added item type management accessible from Settings → Item Types and directly from inventory form with gear icon
- **Usage Tracking**: System tracks which items use each type and prevents deletion of types in use
- **Status Management**: Active/inactive toggle functionality with immediate UI feedback
- **Navigation Integration**: Added Item Types section to Settings subsection in sidebar navigation

### Complete UOM Integration Across Purchase Orders and Material Inspection (Latest)
- **Purchase Order UOM Calculations**: Fixed critical UOM conversion rate calculations where Wheel revit now correctly shows ₹100/kg (calculated from ₹1/piece × 100 pieces/kg conversion factor) instead of incorrect ₹1/piece display
- **Material Inspection UOM Consistency**: Enhanced Material Inspection system to display correct purchase units (Kg) based on Purchase Order UOM instead of inventory units (Pcs), maintaining consistency throughout purchase → inspection workflow
- **Dynamic Unit Labels**: Added comprehensive unit labeling system to Material Inspection form with input group addons showing proper units (Kg, Pcs, etc.) for all quantity fields (Received, Inspected, Passed, Rejected)
- **JavaScript Integration**: Implemented dynamic unit label updates that automatically change when items are selected, ensuring all quantity inputs and summary display consistent units matching the purchase order
- **API Endpoint Fixes**: Updated Material Inspection API endpoints to return correct purchase units from PO items using simplified approach that reads UOM directly from purchase order item records
- **Template Enhancements**: Enhanced both Purchase Order and Material Inspection templates with proper unit display and JavaScript functionality for seamless UOM handling
- **Database Integration**: System now properly reads purchase units from purchase_order_items.uom field and displays them consistently across forms and API responses

### Enhanced Weight System with Gram Support
- **Dual Unit Support**: Complete weight input system supporting both kilograms and grams with intelligent conversion and display
- **Smart Unit Selector**: Added dropdown in inventory form allowing users to enter weights in preferred unit (kg or g)
- **Automatic Conversion**: System stores all weights in kg internally but displays in most appropriate unit (<1kg shows as grams, ≥1kg shows as kilograms)
- **Contextual Help Text**: Dynamic help text that adapts to both selected unit of measure AND chosen weight unit
- **Real-time Conversion**: When switching between kg/g in form, existing values convert automatically without data loss
- **Professional Display**: Enhanced inventory tables and reports with intelligent weight formatting (e.g., "15.0 g/unit", "2.500 kg/unit")
- **Form Enhancement**: Weight field with unit selector integrated seamlessly into existing layout with proper validation

### Complete Weight Tracking Implementation
- **Universal Weight Fields**: Added unit_weight and total_weight columns to all transaction and inventory tables across the entire system
- **Database Schema Enhancement**: Updated Items, PurchaseOrderItem, SalesOrderItem, BOMItem, Production, JobWork, QualityIssue, MaterialInspection, and FactoryExpense models with weight fields
- **Inventory Form Enhancement**: Added unit weight input field to inventory item form with kg unit indicator and validation
- **Comprehensive Weight Calculation**: System now tracks weight per unit and calculates total weights for all transactions and inventory movements
- **Database Migration Completed**: Successfully executed SQL migrations to add weight columns to all relevant PostgreSQL tables
- **Form Integration**: Enhanced ItemForm with unit_weight field including proper validation and help text
- **Template Updates**: Updated inventory form template with professional weight input field and proper styling
- **Route Updates**: Enhanced both add_item and edit_item routes to handle unit_weight field data
- **Complete System Coverage**: Weight tracking now available across Purchase Orders, Sales Orders, Production, Job Work, Quality Control, Material Inspection, and Factory Expenses
- **Professional UI**: Weight fields integrated with Bootstrap styling and proper unit indicators (kg) for consistency

### Comprehensive Data Backup System
- **Excel Export Functionality**: Complete data export to Excel with separate sheets for all major data types (Items, Business Partners, Purchase Orders, Sales Orders, Employees, Job Works, Productions, Factory Expenses, Quality Issues)
- **JSON Backup System**: Technical backup format preserving complete data structure for system restoration and migrations
- **Professional Backup Dashboard**: Dedicated backup interface showing database statistics and export options with real-time data counts
- **Cloud Backup Integration**: Framework for Google Drive, Dropbox, and OneDrive backup (integration placeholders for future development)
- **Automated Backup Scheduling**: Admin-only feature for scheduling daily/weekly/monthly automatic backups
- **Data Import Capability**: JSON import functionality for data restoration (admin-only with proper validation)
- **Navigation Integration**: Added "Data Backup" link to sidebar navigation with cloud download icon
- **Settings Integration**: Moved Data Backup and Dashboard Customization under Settings section for better organization
- **Loading States**: Professional loading modals and progress indicators during backup operations
- **File Download Management**: Proper file handling with timestamped filenames and appropriate MIME types

### Fully Customizable Dashboard System  
- **Dynamic Dashboard Architecture**: Completely redesigned main dashboard with user-specific customization capabilities
- **Dashboard Preference Database**: Added DashboardModule and UserDashboardPreference models for storing user dashboard layouts
- **Module Management System**: Created comprehensive module system with 9 core dashboard modules (removed Data Backup from main dashboard, moved to Settings)
- **Drag-and-Drop Interface**: Implemented sortable interface allowing users to reorder dashboard modules by dragging
- **Module Visibility Controls**: Users can show/hide any dashboard module using checkboxes with instant visual feedback
- **Responsive Module Sizing**: Three size options (Small, Medium, Large) with corresponding responsive layouts
- **Professional Customization UI**: Dedicated dashboard customization page with sortable modules, size controls, and batch operations
- **Persistent User Preferences**: All dashboard changes are saved per-user and automatically loaded on dashboard visits
- **Reset Functionality**: Users can reset dashboard to default layout while preserving other system settings
- **Navigation Integration**: Added "Customize Dashboard" links in main dashboard header and sidebar navigation
- **BOM Cost Calculation Fix**: Fixed Total BOM Cost calculation by moving from problematic Jinja2 template logic to reliable Python backend calculation
- **Auto-initialization**: New users automatically receive default dashboard layout with all modules visible in standard order
- **JavaScript Issue Resolution**: Fixed Save Preferences button functionality with proper global function declarations and modern fetch API

### Complete UI/UX Enhancement & Flickering Resolution (Latest)
- **Universal Date Filtering**: Implemented comprehensive date filtering across all major modules including Purchase Orders, Sales Orders, and Inventory
- **Advanced Filter Interface**: Professional card-based filter sections with date ranges, dropdown filters, search functionality, and clear/reset options
- **Purchase Order Filtering**: Date range (from/to), supplier selection, status filtering, PO number search with results counter
- **Sales Order Filtering**: Date range (from/to), customer selection, status filtering, SO number search with results counter  
- **Inventory Filtering**: Advanced search by name/code, item type filter, stock status filter, price range filtering with comprehensive options
- **Sidebar Navigation Consistency**: Fixed dashboard sidebar to show all menu items consistently across main dashboard and module pages
- **Complete Navigation Menu**: Unified sidebar now includes all modules (Quality Control, UOM Management, Material Inspection, Documents, Admin Approvals) on both dashboard and module pages
- **Sidebar Flickering Resolution**: Completely eliminated sidebar flickering during page loads and navigation with preload CSS classes and hardware acceleration
- **UOM Button Alignment Fix**: Corrected misaligned "Setup" buttons in UOM Management dashboard using proper Bootstrap flexbox layout
- **Professional UI Design**: Consistent filtering experience with preserved filter states, proper validation, responsive design, and stable navigation
- **Enhanced User Experience**: Smooth, professional navigation without flickering, properly aligned buttons, and easy access to all system features

### Universal Table Scrolling System Implementation
- **Comprehensive CSS Framework**: Enhanced custom.css with complete table scrolling system including horizontal and vertical scrolling for all tables
- **Automatic Table Enhancement**: JavaScript automatically wraps all tables with `.table-responsive` containers and applies proper Bootstrap classes
- **Sticky Header Support**: All table headers become sticky during vertical scrolling with proper z-index and background styling
- **Semantic Column Classes**: Automatic detection and application of semantic CSS classes based on column content (col-id, col-name, col-quantity, col-price, etc.)
- **Responsive Design**: Tables adapt to different screen sizes with configurable minimum widths and heights
- **Enhanced UX Features**: Scroll indicators, hover effects, and professional visual hierarchy for better data navigation
- **Universal Application**: All existing tables throughout the system (inventory, purchase orders, sales orders, quality control, etc.) automatically receive scrolling enhancements
- **Programmatic Control**: Added `makeTableScrollable()` utility function for custom table configurations
- **Professional Styling**: Enhanced table appearance with proper borders, spacing, and Bootstrap integration
- **Cross-Module Consistency**: Unified table experience across all modules maintaining existing functionality while adding scrolling capabilities

### Flexible Database Reset System (Latest)
- **Selective Reset Interface**: Enhanced Settings dashboard with checkbox-based reset options allowing users to choose exactly what data to preserve or delete
- **Granular Control**: Individual toggles for Purchase Orders/Sales Orders, Inventory Items, Production/Job Work, Material Inspections/Quality Issues, Factory Expenses, Employee Records/Payroll, and Uploaded Documents
- **Smart Preservation**: Always preserves user accounts, company settings, and notification configurations regardless of selection
- **Interactive UI**: "Select All" and "Clear All" buttons for quick selection, with real-time confirmation showing exactly what will be deleted
- **Custom Confirmation**: Dynamic confirmation dialog lists only selected items to be deleted, preventing accidental data loss
- **Backend Logic**: Server-side validation respects user choices and deletes only selected data types while maintaining foreign key integrity
- **Success Feedback**: Clear messaging shows exactly what was deleted after reset completion
- **Admin Security**: Reset functionality restricted to admin users only with proper authentication checks

### Complete Document Management System
- **Comprehensive Document Upload**: Added document upload functionality to Factory Expenses with file preview and validation
- **Central Document Management**: Created dedicated document management page accessible at `/documents/list` 
- **Advanced Filtering System**: Implemented filtering by transaction type, document category, file type, and filename search
- **Document Statistics**: Real-time statistics showing total documents, storage usage, file types, and transactions with documents
- **Professional Document Interface**: Clean table interface with download, view, and transaction navigation options
- **File Validation**: Support for PDF, Images (JPG, PNG), Word (DOC, DOCX), Excel (XLS, XLSX) with 10MB size limit
- **Navigation Integration**: Added Documents section to main sidebar navigation for easy access
- **Expense Document Integration**: Factory expenses now support multiple document attachments with preview functionality
- **Document Storage**: Organized file storage in uploads/[transaction_type]/[transaction_id]/ directory structure
- **Cross-Module Integration**: Documents linked to Purchase Orders, Sales Orders, Job Work, and Factory Expenses
- **Document Detail Display**: Supporting documents section in expense detail pages with download/view capabilities

### Purchase Order & Sales Order Table UI/UX Enhancement
- **Unified Column Width Optimization**: Redesigned both Purchase Order and Sales Order tables with proper minimum widths for all columns
- **Enhanced Field Sizing**: Increased GST Rate (120px), UOM (80px), Qty (100px), Rate (130px), and Amount (130px) column widths for better usability
- **Responsive Table Design**: Added horizontal scrolling with 1200px minimum table width for comprehensive data display across both forms
- **Input Field Improvements**: Applied consistent minimum width styling (80-130px) to all input fields for comfortable data entry
- **Professional Layout**: Optimized column distribution with absolute pixel-based minimum widths instead of percentage-only approach
- **Better User Experience**: Enhanced both Purchase Order and Sales Order form readability and data entry efficiency with larger, more accessible input fields
- **CSS Styling Enhancements**: Added table-specific styles for better field visibility and consistent layout across different screen sizes
- **Consistent Design Language**: Applied same design principles and field sizing to maintain consistency across Purchase and Sales modules
- **Unified Terminology**: Standardized column headers ("Item Code", "Specification") across both PO and SO forms for consistent user experience
- **Professional Visual Hierarchy**: Achieved clean, spacious layout with proper field accessibility and intuitive navigation across both modules

### Complete Employee Salary and Advance Management System
- **Comprehensive Payroll Models**: Created SalaryRecord and EmployeeAdvance models with auto-generated numbers (SAL-YYYY-0001, ADV-YYYY-0001)
- **Salary Processing**: Complete salary calculation with basic amount, overtime, bonuses, deductions, and automatic advance adjustments
- **Advance Management**: Employee advance requests with configurable repayment periods, monthly deduction calculations, and remaining balance tracking
- **Professional Forms**: Multi-section forms for salary records and advance requests with employee selection and payment method options
- **Approval Workflow**: Complete admin approval system for both salaries and advances with pending → approved → paid/active lifecycle
- **Employee Integration**: Enhanced employee detail pages with salary and advance history, total advances, and remaining balances
- **Dashboard Analytics**: Added pending salaries, pending advances, and total active advances to HR dashboard statistics
- **Navigation Enhancement**: Updated HR dashboard with dedicated salary and advance quick action buttons and comprehensive statistics
- **Financial Tracking**: Complete payroll management with gross/net calculations, tax deductions, and advance integration
- **Permission System**: Role-based access with staff able to request advances, admins able to approve and manage all records

### Enhanced BOM System with Advanced Freight Cost Units & Weight Calculation (Latest)
- **Advanced Freight Unit Types**: Enhanced freight cost system with 5 unit options (Per Piece/Unit, Per Kilogram, Per Box, Per Carton, Per Ton) for flexible real-world pricing models
- **Intelligent Weight-Based Calculations**: Implemented automatic freight cost calculation based on product total weight (e.g., ₹7.00 per kg × 2.7 kg total weight = ₹18.90 per unit)
- **Backend Weight Calculation**: Added reliable `total_weight_per_unit` property to BOM model ensuring consistent weight calculations across freight costing and display
- **Enhanced Display Logic**: Freight cost shows calculated per-unit amount with source unit type notation (e.g., "₹18.90 (₹7.00 Per Kg)")
- **Database Schema Updates**: Added `freight_unit_type` column to BOMs table with proper migration and form integration
- **Improved User Workflow**: Fixed Purchase Order creation redirect to return to PO list instead of edit page for better navigation flow

### Enhanced BOM System with Freight Cost Integration
- **Freight Cost Integration**: Added optional freight/transportation cost field to BOM calculations as requested by user
- **Comprehensive Cost Breakdown**: BOM now includes materials, labor, overhead, and freight costs with separate line items in cost breakdown table
- **Optional Cost Display**: Freight cost section marked as "Optional" with helpful text explaining it's often not paid by company
- **Database Enhancement**: Added freight_cost_per_unit column to boms table with proper default values
- **Enhanced Cost Calculation**: Updated total_cost_per_unit property to include freight costs in final product costing
- **Form Integration**: Added freight cost field to BOMForm with proper validation and user-friendly labeling
- **Template Updates**: Enhanced BOM form template with dedicated freight cost section and professional styling
- **Route Updates**: Updated both add_bom and edit_bom routes to handle freight cost field properly
- **Automatic Unit Cost Population**: Maintained existing functionality for auto-populating unit costs from inventory item prices
- **Cost Transparency**: BOM cost breakdown table now shows all cost components separately for complete transparency

### Complete Tally Integration System
- **Comprehensive XML Export System**: Created complete Tally XML export functionality for Chart of Accounts, Stock Items, and Vouchers
- **Chart of Accounts Export**: Exports all suppliers and customers as Tally ledgers with proper parent grouping (Sundry Creditors/Debtors)
- **Stock Items Export**: Exports inventory items with opening balances, unit prices, and GST classifications for seamless Tally integration
- **Voucher Export System**: Complete voucher export for Purchase Orders, Sales Orders, and Factory Expenses with date filtering and GST calculations
- **Sync Status Tracking**: Added tally_synced boolean fields to PurchaseOrder, SalesOrder, and FactoryExpense models for tracking synchronization status
- **Professional Dashboard**: Tally dashboard showing sync statistics, pending exports, and quick access to all export functions
- **Integration Guide**: Comprehensive settings page with Tally integration instructions, field mappings, and best practices
- **Navigation Integration**: Added Tally Integration module to sidebar navigation and main dashboard with exchange icon
- **XML Standards Compliance**: Generated XML follows Tally TDL (Tally Definition Language) standards for proper import compatibility
- **Database Schema Updates**: Enhanced models with Tally sync tracking capabilities across all major transaction types

### Complete Factory Expenses Management System
- **Comprehensive Expense Model**: Created complete FactoryExpense model with auto-generated expense numbers (EXP-YYYY-0001 format)
- **Expense Categories**: Seven main categories including Utilities, Maintenance, Salaries, Materials, Overhead, Transport, and Others
- **Professional Form System**: Multi-section expense form with Basic Information, Financial Details, Vendor Information, and Recurring Support
- **Approval Workflow**: Complete admin approval system with pending/approved/rejected/paid status tracking
- **Financial Tracking**: Automatic total calculation with base amount + tax amount, payment method selection
- **Vendor Integration**: Optional vendor information capture with invoice tracking and contact details
- **Recurring Expenses**: Support for monthly/quarterly/yearly recurring expenses with automated scheduling
- **Admin Dashboard**: Real-time expense analytics with monthly trends, category breakdowns, and pending approval alerts
- **Navigation Integration**: Added Factory Expenses to main sidebar and dashboard module grid
- **Professional Templates**: Complete template system including dashboard, list view, detailed view, and expense form
- **Permission System**: Role-based access with staff able to create/edit own expenses, admins can approve and manage all
- **Chart Integration**: Monthly expense trend visualization using Chart.js for data insights
- **Status Management**: Complete lifecycle management from creation → approval → payment with timeline tracking

### Complete Unified Business Partner System (Latest)
- **Eliminated Customer Model**: Completely removed separate Customer model and table from the codebase
- **Single Table Architecture**: All business partners (suppliers, customers, and hybrid partners) now use unified `suppliers` table with `partner_type` field
- **Database Migration**: Successfully migrated PostgreSQL database to use unified approach with proper foreign key constraints
- **Sales Order Integration**: Updated SalesOrder model to reference suppliers table instead of customers table
- **Unified Form System**: Enhanced SupplierForm to handle all partner types with comprehensive fields and partner type selection
- **Redirect Strategy**: Sales customer routes now intelligently redirect to unified business partner management
- **Template Updates**: Updated sales dashboard and templates to use unified approach while maintaining user-friendly "customer" terminology
- **Smart Partner Type Handling**: Business partner form automatically pre-fills partner type based on URL parameters for seamless user experience
- **Backward Compatibility**: Maintained all existing functionality while simplifying the underlying data architecture
- **Enhanced UI/UX**: Business partner list shows color-coded badges for partner types (Supplier/Customer/Both) with comprehensive information display

### Comprehensive Supplier Management Enhancement (Latest)
- **Enhanced Supplier Model**: Expanded supplier model with all comprehensive fields:
  - Basic Information: Name, Contact Person, Mobile Number, Email
  - Compliance Information: GST Number (mandatory for GST), PAN Number (optional)
  - Address Information: Full Address, City, State, Pin Code
  - Banking Information: Account Number, Bank Name, IFSC Code (all optional for payments)
  - Additional Information: Remarks, Active/Inactive Status
- **Professional Supplier Form**: Created sectioned supplier form with color-coded sections and helpful placeholders
- **Updated Routes**: Enhanced add/edit supplier routes to handle all new comprehensive fields
- **Field Validation**: Added proper validation and placeholders for all supplier fields
- **Database Migration**: Updated supplier model structure for comprehensive supplier information storage

### BOM Material Availability Checking System
- **Complete BOM Integration**: Created comprehensive BOM for Castor Wheel with 6 component materials (Metal Bracket, Wheel PU/PP, Axle/Pin, Nut/Bolt, Washer, Grease/Oil)
- **Real-time Material Validation**: Production form now checks BOM requirements against current inventory before allowing production creation
- **Visual Shortage Indicators**: Production form displays material requirements table with green/red status badges showing availability vs shortages
- **Production Prevention**: System prevents production order creation when materials are insufficient, showing detailed shortage information
- **Dynamic Calculations**: Material requirements automatically calculated based on planned production quantity
- **Enhanced User Experience**: Clear messaging shows exactly which materials are short and by how much
- **Job Work Auto-fill Removal**: Removed BOM rate auto-filling from Job Work forms - users now manually enter rates as requested

### Smart Production Form Workflow
- **Logical Field Display**: Production form now intelligently shows/hides fields based on production status
- **Planning Phase**: When creating new production orders (status = 'planned'), only shows essential planning fields:
  - Production Number, Item to Produce, Planned Quantity, Production Date, Status, Notes
- **Production Phase**: Production result fields only appear when status changes to 'in_progress' or 'completed':
  - Produced Quantity, Good Quality Quantity, Damaged/Defective Quantity
- **Dynamic Interface**: JavaScript automatically shows/hides production result section based on status selection
- **Data Integrity**: Prevents users from entering production results before production actually begins
- **Template Fix**: Resolved ProductionForm template errors by mapping correct field names (production_date vs start_date)
- **User Experience**: Clear section labeling and contextual help text guide users through the workflow

### Email and WhatsApp Communication with PDF Attachments
- **PDF Attachment Support**: Enhanced email sending functionality to automatically include PDF attachments of Purchase Orders and Job Work orders
- **WeasyPrint Integration**: Added WeasyPrint library for server-side PDF generation from HTML templates
- **Professional Send Forms**: Created dedicated send pages for both Purchase Orders and Job Work with recipient selection and custom messaging
- **Send Buttons**: Added paper plane icon buttons to Purchase Order and Job Work list pages for easy access to sending functionality
- **Automatic PDF Generation**: Purchase Orders use existing enhanced print template; Job Work orders use custom PDF template with company branding
- **Attachment Handling**: Enhanced notification service with send_email_with_attachment method supporting base64-encoded PDF attachments
- **User Experience**: Clear notifications inform users that emails will include PDF attachments while WhatsApp sends text-only summaries
- **Integration**: Seamlessly integrated with existing notification system settings and SendGrid email service

### Complete Material Inspection System Implementation (Enhanced)
- **Auto-Calculation Feature**: Enhanced Material Inspection form with automatic rejected quantity calculation (Inspected Quantity - Passed Quantity)
- **User Experience Improvements**: Made rejected quantity field read-only with real-time auto-calculation as users type
- **Form Validation Updates**: Updated form validation to make rejected quantity optional since it's automatically calculated
- **Null Safety Fixes**: Added proper handling for items with null current_stock values to prevent database errors
- **Professional Interface**: Updated help text and form layout to show auto-calculation formula clearly

### Complete Material Inspection System Implementation
- **MaterialInspection Model**: Created comprehensive inspection tracking with unique inspection numbers (INSPECT-YYYY-0001 format)
- **Database Structure**: Fixed database integrity issues and recreated material_inspections table with proper primary key
- **Inspection Workflow**: Implemented inspection-first workflow where all PO and Job Work materials must be inspected before inventory updates
- **Damage Tracking**: Only passed quantities are added to inventory; damaged/rejected quantities tracked separately
- **Template System**: Created complete inspection interface templates including dashboard, PO inspection, job inspection, and detailed views
- **Purchase Order Forms**: Simplified PO form template to resolve field mapping issues while maintaining core functionality
- **Navigation Integration**: Added Material Inspection section to main navigation with proper routing
- **Real-time Analytics**: Dashboard shows pending inspections, statistics, and inspection history

### Comprehensive Quality Control System
- **Quality Issue Tracking**: Complete quality issue management system with unique issue numbers (QI-YYYY-0001 format)
- **Issue Categorization**: Multiple issue types including Damage, Malfunction, Defect, Contamination, Dimension Error, and Material Defect
- **Severity Management**: Four-tier severity system (Low, Medium, High, Critical) with color-coded badges and prioritization
- **Production Integration**: Quality issues can be linked to specific production orders for complete traceability
- **Cost Impact Analysis**: Financial tracking of quality issues with cost impact calculations
- **Assignment System**: Issues can be assigned to team members with status tracking (Open, Investigating, Resolved, Closed)
- **Root Cause Analysis**: Structured fields for root cause analysis, corrective actions, and preventive measures
- **Quality Control Inspections**: Comprehensive inspection logging system with pass/fail quantities and rejection rate calculations
- **Production Quality Metrics**: Enhanced production model to track good vs damaged quantities separately
- **Quality Dashboard**: Real-time dashboard with KPIs, critical issues alerts, and quality trends
- **Comprehensive Reports**: Quality analytics including issue trends, problematic items, and quality scores
- **Navigation Integration**: Added Quality Control section to main navigation with shield icon

### Job Work Inventory Integration
- **Automatic Inventory Deduction**: When materials are sent to vendors, inventory is automatically deducted from stock
- **Partial Return Tracking**: Materials received back (even partially) are automatically added back to inventory
- **Inventory Validation**: System prevents sending materials when insufficient stock is available
- **Real-time Stock Updates**: Both outgoing and incoming materials update inventory levels immediately
- **Detailed Activity Logging**: All inventory movements are tracked with timestamps and quantities in job work notes
- **Smart Quantity Management**: Prevents over-receiving materials beyond what was originally sent
- **Edit Protection**: When editing job works, inventory adjustments are handled automatically if quantities change

### Admin Approval Dashboard System
- **Centralized Approval Management**: Created comprehensive Admin Approval Dashboard at `/admin/approvals`
- **Navigation Integration**: Added "Admin Approvals" link in sidebar navigation with warning icon for easy access
- **Pending Request Views**: Displays all pending Purchase Orders, Production Orders, and Sales Orders requiring approval
- **Quick Action System**: One-click approve/reject buttons with confirmation modals and optional comments
- **Activity Timeline**: Shows recent approval activity with timestamps and action details  
- **Badge Notifications**: Visual indicators showing count of pending approvals in each category
- **Role-Based Access**: Admin-only access with proper authentication checks

### BOM Integration Fix
- **Field Mapping Issue Resolved**: Fixed JavaScript field mapping bug where GST Rate field was incorrectly populated with BOM unit cost instead of actual GST rate
- **Correct Data Flow**: Established proper mapping from backend to frontend:
  - GST Rate Field ← item.gst_rate (18% for castor)
  - Rate Field ← item.bom_rate (42.94 for castor from BOM system)
  - HSN Code Field ← item.hsn_code 
  - UOM Field ← item.unit_of_measure ("nos" for castor)
- **Backend Verification**: Confirmed backend API correctly provides BOM rates (42.94) vs item unit prices (37.94)
- **Enhanced Debugging**: Added comprehensive field mapping verification to track data flow from database to form fields

## Previous Changes

- **Enhanced Purchase Order System**: Completed industrial-standard Purchase Order forms with comprehensive fields:
  - No., RM Code, Item + Description, Drawing/Spec Sheet No., HSN Code, GST Rate, UOM, Qty, Rate, Amount
  - Professional print templates with company letterhead and tax calculations
  - Enhanced PurchaseOrderItem model with all required industrial fields
- **Company Settings Module**: Implemented complete company configuration system:
  - Company name, address (2 lines), city/state/PIN, phone, GST number, ARN number
  - Settings dashboard with navigation link in sidebar
  - Company information integration in Purchase Order documents
- **Auto-Generation System**: Implemented comprehensive auto-generation for all unique codes and numbers to prevent duplicates:
  - Purchase Order Numbers: PO-YYYY-0001 format with year-based sequencing
  - Sales Order Numbers: SO-YYYY-0001 format with year-based sequencing  
  - Item Codes: ITEM-0001 format with customizable prefixes
  - Employee Codes: EMP-0001 format with sequential numbering
  - Job Work Numbers: JOB-YYYY-0001 format with year-based sequencing
  - Production Numbers: PROD-YYYY-0001 format with year-based sequencing
- **Duplicate Prevention**: Built-in validation to ensure no duplicate codes are generated across the system
- **Smart Form Pre-filling**: All forms automatically populate with next available code when creating new records
- **SMS/Email/WhatsApp Notifications Integration**: Implemented comprehensive notification system using Twilio (SMS/WhatsApp) and SendGrid (Email)
- **Settings Interface**: Added complete settings dashboard in navigation sidebar for managing notification API credentials and configurations
- **Notification Management**: Created recipient management system with configurable notification types and event preferences
- **Automated Alerts**: Integrated low stock alerts, order status updates, and production completion notifications
- **Background Scheduler**: Added automated notification scheduler for periodic checks and system health monitoring
- **Notification Logging**: Comprehensive logging system to track all notification attempts and delivery status
- **Test Notifications**: Built-in testing interface for validating notification settings and credentials

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Technology Stack
- **Backend Framework**: Flask (Python)
- **Database**: SQLAlchemy ORM with SQLite (configurable to PostgreSQL)
- **Authentication**: Flask-Login with role-based access control
- **Frontend**: Bootstrap 5 with dark theme support
- **Template Engine**: Jinja2
- **Form Handling**: Flask-WTF with WTForms validation

### Application Structure
The application follows a modular blueprint architecture with separate modules for each business domain:
- Authentication and user management
- Inventory management
- Purchase order management
- Sales order management
- HR and employee management
- Job work tracking
- Production management
- Reporting system

## Key Components

### Authentication System
- Role-based access control (Admin/Staff)
- Flask-Login session management
- Password hashing with Werkzeug security
- CLI commands for admin user creation

### Database Models
- **User**: Authentication and role management
- **Item**: Inventory items with stock tracking
- **Supplier/Customer**: Vendor and client management
- **Purchase/Sales Orders**: Transaction management
- **Employee**: HR management with salary tracking
- **JobWork**: External job work tracking
- **Production**: Manufacturing order management
- **BOM**: Bill of Materials for production

### Frontend Architecture
- Responsive Bootstrap 5 interface with dark theme
- Modular template inheritance
- Dashboard-driven navigation
- Form validation and error handling
- AJAX enhancements with custom JavaScript

### Security Features
- Environment-based configuration
- Secure session management
- CSRF protection via Flask-WTF
- Input validation and sanitization

## Data Flow

### Authentication Flow
1. User login via Flask-Login
2. Role-based route protection
3. Session management with secure cookies

### Business Process Flow
1. **Inventory Management**: Add items → Track stock → Monitor low stock alerts
2. **Purchase Process**: Create PO → Receive goods → Update inventory
3. **Sales Process**: Create SO → Process orders → Update stock levels
4. **Production Process**: Create production orders → Consume raw materials → Produce finished goods
5. **Job Work Process**: Send materials → Track progress → Receive finished items

### Dashboard System
Each module provides its own dashboard with:
- Statistical summaries
- Recent activity feeds
- Alert notifications
- Quick action buttons

## External Dependencies

### Core Flask Ecosystem
- Flask-SQLAlchemy: Database ORM
- Flask-Login: User session management
- Flask-WTF: Form handling and CSRF protection
- Werkzeug: Security utilities and middleware

### Frontend Dependencies
- Bootstrap 5: UI framework with dark theme
- Font Awesome: Icon library
- Custom CSS for factory-specific styling

### Development Tools
- Click: CLI command framework
- Environment variable configuration
- Database migration support

## Deployment Strategy

### Configuration Management
- Environment-based configuration classes
- Separate development and production settings
- Database URL configuration via environment variables
- Secret key management

### Database Strategy
- SQLite for development and small deployments
- PostgreSQL support for production scaling
- Connection pooling and health checks
- Database initialization via CLI commands

### Scalability Considerations
- Modular blueprint architecture for easy feature addition
- Configurable database backends
- Session management ready for Redis scaling
- Static asset optimization

### Security Deployment
- ProxyFix middleware for reverse proxy deployment
- Environment variable security
- Database connection security
- Session cookie security settings

The application is designed to be easily deployable on platforms like Replit, Heroku, or traditional VPS hosting with minimal configuration changes.