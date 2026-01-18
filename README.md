# Assets and Inventory Management System (AIMS)

A comprehensive desktop application for managing assets and inventory in an organization. Built with Python, PySide6, and SQLite.

## Features

### Master Data Management
- **Categories**: Manage asset categories
- **Sub-Categories**: Organize assets under categories
- **Branches**: Define organizational branches (Store is the main branch)
- **Items**: Add and manage inventory items with category and subcategory associations

### Transactions
- **Acquisition**: Add new assets to the Store
- **Issue/Return**: Transfer assets between Store and branches
- **Disposal**: Remove assets from inventory with proper documentation

### Reports
- **Summary**: Overall stock register with acquired, disposed, and remaining quantities
- **Branch-wise Balance**: Current assets held by each branch
- **Disposal Report**: History of disposed assets
- **Acquisition History**: Record of all acquisitions
- **Transaction History**: Log of all issue/return transactions

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup
1. Clone or download the repository
2. Navigate to the project directory
3. Create a virtual environment (optional but recommended):
   ```
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   ```
4. Install dependencies:
   ```
   pip install PySide6
   ```
5. Run the application:
   ```
   python main.py
   ```

### Standalone Executable
A pre-built executable (`AIMS.exe`) is available in the `dist/` directory for Windows users who prefer not to install Python.

## Usage

### Getting Started
1. Launch the application
2. Use the **Master Data** menu to set up categories, subcategories, branches, and items
3. The **Store** branch is automatically created as the central inventory location

### Workflow
1. **Acquire Assets**: Use Transactions > Acquisition to add items to the Store
2. **Issue Assets**: Use Transactions > Issue/Return to transfer items from Store to branches
3. **Return Assets**: Use Transactions > Issue/Return to return items from branches to Store
4. **Dispose Assets**: Use Transactions > Disposal to remove items from inventory

### Reports
Access various reports through the **Reports** menu to view summaries, balances, and histories.

## System Architecture

- **Frontend**: PySide6 (Qt-based GUI)
- **Backend**: SQLite database
- **Language**: Python 3.x

### Key Files
- `main.py`: Application entry point
- `gui.py`: Main window and dashboard
- `db.py`: Database connection and operations
- `models.py`: Data models
- `gui_*.py`: Dialog windows for various functions
- `gui_reports.py`: Report dialogs

## Database Schema

The application uses SQLite with the following main tables:
- `categories`
- `sub_categories`
- `branches`
- `items`
- `asset_batches`
- `asset_transactions`
- `asset_disposal`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues or questions, please create an issue in the repository or contact the development team.