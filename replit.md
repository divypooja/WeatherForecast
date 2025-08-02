# Factory Management System - Flask Application

## Overview
This Flask-based Factory Management System is designed for small to medium manufacturing companies. It provides modular dashboards for managing inventory, purchase orders, sales, HR, job work, production, and reporting. The system aims to streamline operations, enhance material tracking from raw materials to finished goods, and provide real-time manufacturing intelligence. Key capabilities include comprehensive enterprise-wide batch tracking, multi-state inventory tracking, BOM-driven production planning, comprehensive quality control, detailed expense management, and a flexible reporting system with complete material traceability through all manufacturing processes. The business vision is to empower manufacturing SMEs with an affordable, comprehensive, and user-friendly solution to optimize their factory operations, reduce waste, and improve efficiency.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
The application features a responsive Bootstrap 5 interface with a dark theme. It employs a dashboard-driven navigation with modular template inheritance, consistent styling across all tables (including sticky headers and responsive scrolling), and intelligent form layouts that dynamically show/hide fields based on user selections. Visual cues like color-coded badges, progress indicators, and intuitive icons are used. A customizable dashboard allows users to reorder and toggle the visibility of modules. The Job Work form features automatic rate loading with visual feedback.

### Technical Implementations
The system is built on a Flask backend using a modular blueprint architecture. It uses SQLAlchemy ORM for database interactions, supporting both SQLite for development and PostgreSQL for production. Flask-Login manages authentication with role-based access control (Admin/Staff). Flask-WTF handles form validation and CSRF protection. Core features include:
- **Multi-State Inventory:** Tracks items in Raw Material, Work in Progress (WIP), Finished Goods, and Scrap states, with process-specific WIP tracking.
- **BOM-Driven Manufacturing:** Supports Bill of Materials for production planning, including material availability checks, automatic labor cost and scrap calculations, and BOM-driven material reservations.
- **Unified Job Work System:** A single, comprehensive form manages all job work types (in-house/outsourced, single/multi-process), integrating with GRN for material receipt and inventory updates.
- **Automated Workflows:** Features automated Purchase Order status progression, automatic inventory updates, and GRN-based material receipt.
- **Data Integrity & Automation:** Implements auto-generation for all unique codes, real-time stock validation, and mechanisms to detect and correct data inconsistencies.
- **Process Management:** Detailed tracking of manufacturing processes within BOMs, including step-by-step workflow, cost calculations, and individual process scrap tracking.
- **Comprehensive Management Modules:** Includes robust systems for Employee Management, Department Management, Supplier/Business Partner Management, and Job Work Rates.
- **Reporting & Analytics:** Features a custom report builder, real-time dashboards for manufacturing intelligence, quality control KPIs, and expense analysis.
- **Integrated Accounting System:** Implements a comprehensive Tally-like accounting system with Chart of Accounts, Journal Entry engine for automatic double-entry bookkeeping, GST-compliant invoice generation, automatic transaction recording, financial reporting (Trial Balance, P&L, Balance Sheet), Bank & Cash management, and accounting automation.

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