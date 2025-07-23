# Factory Management System - Flask Application

## Overview

This is a comprehensive Flask-based Factory Management System designed for small to medium manufacturing companies. The application provides modular dashboards for managing various aspects of factory operations including inventory, purchase orders, sales, HR, job work, production, and reporting.

## Recent Changes (January 23, 2025)

### BOM Material Availability Checking System (Latest)
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