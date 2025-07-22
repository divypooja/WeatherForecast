# Factory Management System - Flask Application

## Overview

This is a comprehensive Flask-based Factory Management System designed for small to medium manufacturing companies. The application provides modular dashboards for managing various aspects of factory operations including inventory, purchase orders, sales, HR, job work, production, and reporting.

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