# Factory Management System - Flask Application

## Overview
This Flask-based Factory Management System is designed for small to medium manufacturing companies. It provides modular dashboards for managing inventory, purchase orders, sales, HR, job work, production, and reporting. The system aims to streamline operations, enhance material tracking from raw materials to finished goods, and provide real-time manufacturing intelligence. Key capabilities include comprehensive enterprise-wide batch tracking, multi-state inventory tracking, BOM-driven production planning, comprehensive quality control, detailed expense management, and a flexible reporting system with complete material traceability through all manufacturing processes. **Latest Achievement (August 2025)**: Successfully implemented comprehensive HR accounting integration and organized file upload structure. Completed HR forms accounting automation with automatic voucher generation, double-entry bookkeeping, and advance recovery tracking. Established structured document management system with organized folders (/po/, /grn/, /jobwork/, /invoices/, /hr/employees/, etc.) and reference-number-based file naming for improved traceability and maintenance. The business vision is to empower manufacturing SMEs with an affordable, comprehensive, and user-friendly solution to optimize their factory operations, reduce waste, and improve efficiency.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
The application features a responsive Bootstrap 5 interface with a dark theme. It employs a dashboard-driven navigation with modular template inheritance, consistent styling across all tables (including sticky headers and responsive scrolling), and intelligent form layouts that dynamically show/hide fields based on user selections. Visual cues like color-coded badges, progress indicators, and intuitive icons are used. A customizable dashboard allows users to reorder and toggle the visibility of modules. The Job Work form features automatic rate loading with visual feedback.

### Technical Implementations
The system is built on a Flask backend using a modular blueprint architecture. It uses SQLAlchemy ORM for database interactions, supporting both SQLite for development and PostgreSQL for production. Flask-Login manages authentication with role-based access control (Admin/Staff). Flask-WTF handles form validation and CSRF protection. **Complete Accounting Integration (January 2025)**: All financial operations across the entire ERP system are now managed through the centralized accounting section with automatic double-entry bookkeeping. **Professional Invoice System (January 2025)**: Comprehensive Tally-style invoice creation and management system with GST compliance, automatic accounting entries, and professional print layouts. Core features include:
- **Multi-State Inventory:** Tracks items in Raw Material, Work in Progress (WIP), Finished Goods, and Scrap states, with process-specific WIP tracking.
- **BOM-Driven Manufacturing:** Supports Bill of Materials for production planning, including material availability checks, automatic labor cost and scrap calculations, and BOM-driven material reservations.
- **Unified Job Work System:** A single, comprehensive form manages all job work types (in-house/outsourced, single/multi-process), integrating with GRN for material receipt and inventory updates.
- **Automated Workflows:** Features automated Purchase Order status progression, automatic inventory updates, and GRN-based material receipt.
- **Data Integrity & Automation:** Implements auto-generation for all unique codes, real-time stock validation, mechanisms to detect and correct data inconsistencies, and comprehensive accounting automation that creates proper journal entries for all financial transactions across modules.
- **Process Management:** Detailed tracking of manufacturing processes within BOMs, including step-by-step workflow, cost calculations, and individual process scrap tracking.
- **Comprehensive Management Modules:** Includes robust systems for Employee Management, Department Management, Supplier/Business Partner Management, and Job Work Rates.
- **Reporting & Analytics:** Features a custom report builder, real-time dashboards for manufacturing intelligence, quality control KPIs, and expense analysis.
- **Integrated Accounting System:** Implements a comprehensive Tally-like accounting system with Chart of Accounts, Journal Entry engine for automatic double-entry bookkeeping, GST-compliant invoice generation, automatic transaction recording, financial reporting (Trial Balance, P&L, Balance Sheet), Bank & Cash management, and comprehensive accounting automation. **Complete ERP Integration**: All modules (PO/SO, Factory Expenses, Job Work Rates, Inventory Valuation, BOM Cost Allocation) now create automatic accounting entries through centralized AccountingAutomation service with proper double-entry bookkeeping.
- **Professional Invoice Management:** Complete invoice creation and management system with Tally-style professional layouts, dynamic item management, automatic GST calculations, invoice finalization with accounting integration, and comprehensive print templates. Supports both sales and purchase invoices with proper tax handling and party management.
- **3-Step GRN Workflow (August 2025):** Enterprise-grade procurement workflow with GRN Clearing Account (2150), GST Input Tax tracking (1180), automated voucher generation, and complete Purchase-to-Payment cycle management. Features intelligent template handling for both Job Work and Purchase Order based GRNs with proper error handling and intuitive navigation.
- **HR Accounting Integration (August 2025):** Complete integration of HR forms (salary and advance payments) with the accounting system, featuring automatic voucher generation, advance recovery tracking, and seamless double-entry bookkeeping for employee financial transactions.
- **Organized File Upload System (August 2025):** Structured document management with organized directories (/uploads/po/, /grn/, /jobwork/, /invoices/, /hr/employees/, /hr/salaries/, /hr/advances/, etc.) and reference-number-based filename generation for improved document traceability and system maintenance.

### System Design Choices
- **Modular Blueprint Architecture:** Promotes code organization and scalability by separating features into distinct modules.
- **Unified Data Models:** A single `suppliers` table manages all business partners (suppliers, customers, vendors, transporters) via a `partner_type` field.
- **Transactional Consistency:** Critical operations include comprehensive transaction handling to ensure data integrity.
- **API-First Design:** Many features leverage dedicated API endpoints for real-time data fetching, supporting dynamic frontend interactions.
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
- **Chart.js**: For data visualization

### Communication & Notification Services
- **Twilio**: For SMS and WhatsApp notifications
- **SendGrid**: For email notifications

### PDF Generation
- **WeasyPrint**: For server-side PDF generation from HTML templates

### Optimization Libraries
- **Rectpack**: Python library for 2D rectangle packing optimization.

### Data Export & Integration
- **OpenPyXL (or similar)**: For Excel data export functionality.
- **Tally TDL standards**: For XML export to Tally accounting software.