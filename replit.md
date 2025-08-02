# Factory Management System - Flask Application

## Overview
This Flask-based Factory Management System is designed for small to medium manufacturing companies. It provides modular dashboards for managing inventory, purchase orders, sales, HR, job work, production, and reporting. The system aims to streamline operations, enhance material tracking from raw materials to finished goods, and provide real-time manufacturing intelligence. Key capabilities include comprehensive enterprise-wide batch tracking, multi-state inventory tracking, BOM-driven production planning, comprehensive quality control, detailed expense management, and a flexible reporting system with complete material traceability through all manufacturing processes. The business vision is to empower manufacturing SMEs with an affordable, comprehensive, and user-friendly solution to optimize their factory operations, reduce waste, and improve efficiency.

## Recent Changes (August 2025)
✓ Successfully migrated project from Replit Agent to standard Replit environment with PostgreSQL database
✓ Implemented comprehensive multi-level BOM functionality with nested relationships and hierarchical cost calculations
✓ Added multi-level BOM API endpoints for hierarchy visualization, cost breakdown, and production sequence optimization
✓ Enhanced BOM form with parent-child relationship fields and phantom BOM support
✓ Created admin user credentials (admin/admin123) for system access
✓ Successfully implemented comprehensive enterprise-wide batch tracking system across ALL modules
✓ Enhanced ItemBatch model with process-specific WIP tracking for cutting, bending, welding, zinc plating, painting, assembly, machining, and polishing
✓ Added batch movement methods for complete material traceability from raw materials to finished goods
✓ Integrated batch creation during GRN processing for automatic batch generation from supplier receipts
✓ Enhanced Job Work module with comprehensive batch selection and tracking API endpoints
✓ Created dedicated Batch Tracking dashboard with process-wise inventory views, quality control, and traceability reports
✓ Added comprehensive batch tracking utilities (BatchTracker, BatchValidator) for system-wide batch operations
✓ Implemented batch transfer capabilities between different manufacturing process stages
✓ Added batch tracking columns to items table (batch_required, default_batch_prefix, shelf_life_days, batch_numbering_auto)
✓ Created BatchMovementLedger and BatchConsumptionReport models for complete audit trail
✓ Updated GRN module with automatic batch creation and comprehensive batch tracking integration
✓ Updated Job Work module with batch selection functionality and API endpoints for material issuing/receiving
✓ Updated Inventory module with enhanced batch tracking dashboard and traceability views
✓ Enhanced Production module with comprehensive batch tracking for material consumption and output batch creation
✓ Added ProductionBatch model for tracking material batches consumed in production with BOM integration
✓ Integrated Production module with batch issuing, tracking, and automatic output batch generation
✓ Added Production API endpoints for batch availability, material issuing, production completion, and consumption tracking
✓ Fixed database schema issues and resolved all duplicate function conflicts
✓ Application successfully running with complete batch tracking functionality across ALL manufacturing processes including Production
✓ Added Batch Tracking navigation menu to sidebar with NEW badge for easy access
✓ Fixed batch tracking dashboard database query errors and application now running without internal server errors
✓ Enhanced inventory list templates to display batch counts and tracking links
✓ Updated GRN detail pages with "View Batches" functionality for material receipt tracking
✓ Added batch tracking buttons throughout inventory dashboard for comprehensive batch access
✓ Fixed Production module placement in navigation menu ensuring all modules are visible and accessible
✓ Completed comprehensive batch tracking template ecosystem with all missing templates created
✓ Fixed CSRF token errors throughout batch tracking module by removing unnecessary references
✓ Resolved data structure handling issues in traceability templates for batch ledger dictionary format
✓ Created missing templates: quality_control.html, process_view.html, batch_movements.html, and completed traceability templates
✓ Fixed routing conflicts and template syntax errors across batch tracking module
✓ Updated batch tracking routes to provide proper data structures for all dashboard views
✓ Fixed inventory batch-wise view database query error by using proper column references instead of property methods
✓ Implemented Multi-State Inventory Parent-Child expandable table structure matching GRN Dashboard design
✓ Successfully resolved jQuery loading conflicts by converting to vanilla JavaScript implementation
✓ Fixed API endpoints to use correct InventoryBatch model with proper field mappings (qty_raw, qty_wip, qty_finished, qty_scrap)
✓ Created sample batch data for testing Parent-Child functionality with multi-state quantity breakdown
✓ Completed production system comparison analysis - current system already implements advanced batch-wise production flow with BOM integration, multi-state tracking, and comprehensive batch traceability exceeding proposed requirements
✓ Successfully implemented complete Tally-like accounting system with all phases integrated at once
✓ Created comprehensive Chart of Accounts with 13 account groups, 17 accounts, 6 voucher types, and 6 GST tax rates
✓ Implemented Journal Entry engine for automatic double-entry bookkeeping with voucher system
✓ Added GST-compliant invoice generation with automatic tax calculations (CGST/SGST/IGST)
✓ Created automatic transaction recording service that integrates with Purchase Orders, Sales Orders, GRN, Job Work, Factory Expenses, and Salary payments
✓ Built comprehensive financial reporting system including Trial Balance, Profit & Loss Statement, Balance Sheet, Day Book, and GST reports
✓ Added Bank & Cash management with account tracking and payment voucher system
✓ Created accounting automation service that generates journal entries for all business transactions automatically
✓ Setup complete accounting dashboard with financial KPIs, monthly trends, and recent transaction tracking
✓ Integrated accounting system with existing factory operations maintaining full traceability and cost tracking
✓ Resolved all critical "Not Found" errors and template issues in financial reports system
✓ Fixed Balance Sheet accessibility with proper route mapping and professional template design
✓ Created missing Trial Balance and Profit & Loss templates with comprehensive financial analysis features
✓ Fixed accounting dashboard JavaScript errors and route conflicts ensuring stable system operation
✓ Enhanced financial reports with print-friendly layouts, date filters, and balance verification features
✓ Completed full accounting system integration - all three major financial reports (Trial Balance, P&L, Balance Sheet) now fully functional
✓ Fixed WTForms SelectField coercion issues across all accounting forms (VoucherForm, PaymentForm, ReceiptForm, ReportFilterForm)
✓ Resolved unified multi-state inventory loading issue by creating missing inventory_multi_state database view
✓ Successfully implemented SQLite-compatible database view for multi-state inventory tracking with proper field mappings
✓ Fixed inventory multi-state route functionality - now properly displaying 8 inventory items with state breakdown
✓ Enhanced payment and receipt voucher forms with proper field validation and error handling
✓ Added complete accounting reports system with all missing routes (day_book, account_ledgers, outstanding_payables, outstanding_receivables, gst_summary, gstr1_report, gstr3b_report, inventory_valuation, cogs_report)
✓ Created comprehensive accounting report templates with professional layouts and navigation
✓ Implemented receipt voucher functionality with proper form handling and journal entry creation
✓ Fixed all WTForms SelectField coercion issues across entire accounting module ensuring stable form processing
✓ Resolved all accounting template relationship errors by correcting Account model references from account_group to group
✓ Fixed account ledger templates and account list templates preventing server crashes
✓ Completed final accounting system stabilization with all internal server errors resolved

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
The application features a responsive Bootstrap 5 interface with a dark theme for professional aesthetics. It employs a dashboard-driven navigation with modular template inheritance, consistent styling across all tables (including sticky headers and responsive scrolling), and intelligent form layouts that dynamically show/hide fields based on user selections. Visual cues like color-coded badges, progress indicators, and intuitive icons are used to enhance user experience. A customizable dashboard allows users to reorder and toggle the visibility of modules. The Job Work form features automatic rate loading with visual feedback (green background) to indicate auto-populated values, eliminating the need for manual intervention.

### Technical Implementations
The system is built on a Flask backend using a modular blueprint architecture. It uses SQLAlchemy ORM for database interactions, supporting both SQLite for development and PostgreSQL for production. Flask-Login manages authentication with role-based access control (Admin/Staff). Flask-WTF handles form validation and CSRF protection. Core features include:
- **Multi-State Inventory:** Tracks items in Raw Material, Work in Progress (WIP), Finished Goods, and Scrap states, with process-specific WIP tracking.
- **BOM-Driven Manufacturing:** Supports Bill of Materials for production planning, including material availability checks, automatic labor cost and scrap calculations from process workflows, and BOM-driven material reservations.
- **Unified Job Work System:** A single, comprehensive form manages all job work types (in-house/outsourced, single/multi-process), integrating with GRN for material receipt and inventory updates.
- **Automated Workflows:** Features automated Purchase Order status progression, automatic inventory updates via daily entries for in-house jobs, and GRN-based material receipt for all incoming goods.
- **Data Integrity & Automation:** Implements auto-generation for all unique codes (PO, SO, Item, Employee, Job Work, Production), real-time stock validation, and mechanisms to detect and correct data inconsistencies.
- **Process Management:** Detailed tracking of manufacturing processes within BOMs, including step-by-step workflow, cost calculations, and individual process scrap tracking.
- **Comprehensive Management Modules:** Includes robust systems for Employee Management (with attendance, salary, and advances), Department Management, Supplier/Business Partner Management (unified system), and Job Work Rates.
- **Reporting & Analytics:** Features a custom report builder, real-time dashboards for manufacturing intelligence, quality control KPIs, and expense analysis.

### System Design Choices
- **Modular Blueprint Architecture:** Promotes code organization and scalability by separating features into distinct modules.
- **Unified Data Models:** A single `suppliers` table now manages all business partners (suppliers, customers, vendors, transporters) via a `partner_type` field, simplifying data architecture.
- **Transactional Consistency:** Critical operations like BOM creation/deletion and GRN processing include comprehensive transaction handling to ensure data integrity.
- **API-First Design:** Many features leverage dedicated API endpoints for real-time data fetching (e.g., item units, BOM materials, stock availability), supporting dynamic frontend interactions.
- **Security:** CSRF protection, input validation, environment-based configuration, and role-based access control are fundamental design choices.

## External Dependencies

### Core Flask Ecosystem
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Login**: User session management
- **Flask-WTF**: Form handling and CSRF protection
- **Werkzeug**: Security utilities and middleware

### Frontend Libraries
- **Bootstrap 5**: UI framework
- **Font Awesome**: Icon library
- **Jinja2**: Template engine
- **Chart.js**: For data visualization (e.g., monthly expense trends)

### Communication & Notification Services
- **Twilio**: For SMS and WhatsApp notifications
- **SendGrid**: For email notifications

### PDF Generation
- **WeasyPrint**: For server-side PDF generation from HTML templates

### Optimization Libraries
- **Rectpack**: Python library for 2D rectangle packing optimization (material cutting, layout optimization).

### Data Export & Integration
- **OpenPyXL (or similar)**: For Excel data export functionality.
- **Tally TDL standards**: For XML export to Tally accounting software.

### Development Utilities
- **Click**: For CLI command framework
- Environment variable management for configuration.