# Library Management System

A Python-based library management system built on SQLite, providing full control over book inventory, customer records, and book issuance/returns.

## Features

- **Book Management** — Add, remove, search, and update books with automatic copy tracking
- **Customer Management** — Register and manage library customers with fee tracking
- **Issue & Return** — Borrow and return books with copy-count enforcement
- **Audit Trail** — Every issue/return is recorded with dates in an `IssuedBooks` table
- **Data Integrity** — Prevents deletion of customers with outstanding books; blocks issuing when no copies remain

## Project Structure

```
library-management-system/
├── schema.sql     # SQL table definitions (Books, Customer, IssuedBooks)
├── library.py     # Library class — the core management engine
├── demo.py        # Interactive demo demonstrating all 9 scenarios
└── README.md      # This file
```

## Requirements

- Python 3.8+
- SQLite (bundled with Python — no external dependencies)

## Installation

```bash
git clone https://github.com/Dm9582/Library_Management_System.git
cd Library_Management_System/library-management-system
```

## Usage

### Quick Start — Run the Demo

```bash
python demo.py
```

The demo walks through:

1. **Seed the library** with 5 sample books
2. **Register customers** (Alice, Bob, Carol)
3. **Issue books** and watch `remaining_copies` decrement
4. **Return books** and watch copies replenish
5. **Copy enforcement** — fails gracefully when 0 copies remain
6. **Pay fees** — mark a customer's fees as paid
7. **Search books** by title or author
8. **Delete guard** — prevents removing a customer with outstanding books
9. **Audit trail** — view all books currently on loan

### Programmatic Usage

```python
from library import Library

lib = Library("my_library.db")

# Add a book
book_id = lib.add_book("The Alchemist", "Paulo Coelho", tot_copies=3)

# Register a customer
cust_id = lib.register_customer("John Doe")

# Issue a book
lib.issue_book(book_id, cust_id)

# Return a book
lib.return_book(book_id, cust_id)

# List all books
for book in lib.list_books():
    print(dict(book))

# List all customers
for customer in lib.list_customers():
    print(dict(customer))
```

## Database Schema

### Books

| Column             | Type    | Description                        |
|--------------------|---------|------------------------------------|
| `book_id`          | INTEGER | Primary key (auto-increment)       |
| `book_name`        | TEXT    | Name of the book                   |
| `author`           | TEXT    | Author name                        |
| `tot_copies`       | INTEGER | Total copies the library owns      |
| `remaining_copies` | INTEGER | Copies currently available         |

### Customer

| Column         | Type    | Description                                            |
|----------------|---------|--------------------------------------------------------|
| `cust_id`      | INTEGER | Primary key (auto-increment)                           |
| `cust_name`    | TEXT    | Customer name                                          |
| `issued_books` | TEXT    | Comma-separated list of currently issued book IDs      |
| `fees_paid`    | TEXT    | `'Yes'` or `'No'` — whether outstanding fees are paid  |

### IssuedBooks

| Column      | Type    | Description                          |
|-------------|---------|--------------------------------------|
| `issue_id`  | INTEGER | Primary key (auto-increment)         |
| `book_id`   | INTEGER | Foreign key → `Books.book_id`        |
| `cust_id`   | INTEGER | Foreign key → `Customer.cust_id`     |
| `issue_date`| TEXT    | Date the book was issued (YYYY-MM-DD)|
| `return_date`| TEXT   | Date returned (NULL if still on loan)|

## API Reference

### `Library(db_path="library.db")`

| Method                     | Description                                         |
|----------------------------|-----------------------------------------------------|
| `add_book(name, author, copies)` | Add a book → returns `book_id`               |
| `remove_book(book_id)`     | Delete a book → returns `True`/`False`               |
| `search_books(keyword)`    | Search by title or author → list of `Row`           |
| `list_books()`             | All books → list of `Row`                            |
| `update_book_copies(id, copies)` | Update total copies → returns `True`/`False` |
| `register_customer(name)`  | Add a customer → returns `cust_id`                   |
| `remove_customer(cust_id)` | Delete customer (must have no books out)             |
| `list_customers()`         | All customers → list of `Row`                        |
| `pay_fees(cust_id)`        | Mark fees as paid → returns `True`/`False`           |
| `issue_book(book_id, cust_id)` | Issue a book → returns `True`/`False`           |
| `return_book(book_id, cust_id)` | Return a book → returns `True`/`False`        |
| `issued_books_detail(cust_id)` | List `Row`s of books issued to a customer       |
| `books_on_loan()`          | List of all `IssuedBooks` rows still on loan        |

## License

This project is provided as-is for educational purposes.