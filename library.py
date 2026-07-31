"""Library Management System
==========================
A minimal but functional library management system built on SQLite.

Tables (see schema.sql):
    Books       - book_id, book_name, author, tot_copies, remaining_copies
    Customer    - cust_id, cust_name, issued_books, fees_paid
    IssuedBooks - audit trail of every issue/return

The public API mirrors common library operations:
    add_book / remove_book / search_books
    register_customer / remove_customer
    issue_book / return_book
    list_books / list_customers
    pay_fees
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Generator, List, Optional, Tuple


class Library:
    """A thin wrapper around an SQLite database that manages books & customers."""

    def __init__(self, db_path: str = "library.db") -> None:
        self.db_path = db_path
        self._init_schema()

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #
    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            with self._conn() as conn:
                conn.executescript(f.read())

    # ------------------------------------------------------------------ #
    #  Book operations
    # ------------------------------------------------------------------ #
    def add_book(
        self, book_name: str, author: str, tot_copies: int
    ) -> int:
        """Add a new book to the library. Returns the new book_id."""
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO Books (book_name, author, tot_copies, remaining_copies) "
                "VALUES (?, ?, ?, ?)",
                (book_name, author, tot_copies, tot_copies),
            )
            return int(cur.lastrowid)

    def remove_book(self, book_id: int) -> bool:
        """Delete a book by id. Returns True if a row was deleted."""
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM Books WHERE book_id = ?", (book_id,))
            return cur.rowcount > 0

    def search_books(self, keyword: str) -> List[sqlite3.Row]:
        """Search books by name or author (case-insensitive partial match)."""
        pattern = f"%{keyword}%"
        with self._conn() as conn:
            return conn.execute(
                "SELECT * FROM Books WHERE book_name LIKE ? OR author LIKE ? "
                "ORDER BY book_name",
                (pattern, pattern),
            ).fetchall()

    def list_books(self) -> List[sqlite3.Row]:
        """Return all books."""
        with self._conn() as conn:
            return conn.execute(
                "SELECT * FROM Books ORDER BY book_id"
            ).fetchall()

    def update_book_copies(self, book_id: int, tot_copies: int) -> bool:
        """Update total copies (and adjust remaining). Returns True if updated."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT remaining_copies, tot_copies FROM Books WHERE book_id = ?",
                (book_id,),
            ).fetchone()
            if row is None:
                return False
            delta = tot_copies - row["tot_copies"]
            new_remaining = max(0, row["remaining_copies"] + delta)
            conn.execute(
                "UPDATE Books SET tot_copies = ?, remaining_copies = ? "
                "WHERE book_id = ?",
                (tot_copies, new_remaining, book_id),
            )
            return True

    # ------------------------------------------------------------------ #
    #  Customer operations
    # ------------------------------------------------------------------ #
    def register_customer(self, cust_name: str) -> int:
        """Register a new customer. Returns the new cust_id."""
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO Customer (cust_name) VALUES (?)", (cust_name,)
            )
            return int(cur.lastrowid)

    def remove_customer(self, cust_id: int) -> bool:
        """Delete a customer (must have no outstanding books). Returns True if deleted."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT issued_books FROM Customer WHERE cust_id = ?", (cust_id,)
            ).fetchone()
            if row is None:
                return False
            if row["issued_books"].strip():
                raise ValueError(
                    f"Customer {cust_id} still has issued books — return them first."
                )
            conn.execute("DELETE FROM Customer WHERE cust_id = ?", (cust_id,))
            return True

    def list_customers(self) -> List[sqlite3.Row]:
        """Return all customers."""
        with self._conn() as conn:
            return conn.execute(
                "SELECT * FROM Customer ORDER BY cust_id"
            ).fetchall()

    def pay_fees(self, cust_id: int) -> bool:
        """Mark a customer's fees as paid. Returns True if updated."""
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE Customer SET fees_paid = 'Yes' WHERE cust_id = ?",
                (cust_id,),
            )
            return cur.rowcount > 0

    # ------------------------------------------------------------------ #
    #  Issue / Return
    # ------------------------------------------------------------------ #
    def issue_book(self, book_id: int, cust_id: int) -> bool:
        """
        Issue a book to a customer.
        Returns True if the issue was successful, False if no copies remain
        or entities don't exist.
        """
        with self._conn() as conn:
            book = conn.execute(
                "SELECT remaining_copies FROM Books WHERE book_id = ?", (book_id,)
            ).fetchone()
            if book is None or book["remaining_copies"] <= 0:
                return False

            cust = conn.execute(
                "SELECT issued_books FROM Customer WHERE cust_id = ?", (cust_id,)
            ).fetchone()
            if cust is None:
                return False

            # Update Books
            conn.execute(
                "UPDATE Books SET remaining_copies = remaining_copies - 1 "
                "WHERE book_id = ?",
                (book_id,),
            )

            # Update Customer.issued_books
            current = cust["issued_books"].strip()
            if current:
                id_list = [int(x) for x in current.split(",") if x.strip()]
            else:
                id_list = []
            if book_id not in id_list:
                id_list.append(book_id)
            conn.execute(
                "UPDATE Customer SET issued_books = ? WHERE cust_id = ?",
                (",".join(str(x) for x in id_list), cust_id),
            )

            # Audit trail
            conn.execute(
                "INSERT INTO IssuedBooks (book_id, cust_id) VALUES (?, ?)",
                (book_id, cust_id),
            )
            return True

    def return_book(self, book_id: int, cust_id: int) -> bool:
        """
        Return a book from a customer.
        Returns True if the return was recorded, False if the book was not issued.
        """
        with self._conn() as conn:
            cust = conn.execute(
                "SELECT issued_books FROM Customer WHERE cust_id = ?", (cust_id,)
            ).fetchone()
            if cust is None:
                return False

            current = cust["issued_books"].strip()
            if not current:
                return False

            id_list = [int(x) for x in current.split(",") if x.strip()]
            if book_id not in id_list:
                return False

            id_list.remove(book_id)
            conn.execute(
                "UPDATE Customer SET issued_books = ? WHERE cust_id = ?",
                (",".join(str(x) for x in id_list), cust_id),
            )
            conn.execute(
                "UPDATE Books SET remaining_copies = remaining_copies + 1 "
                "WHERE book_id = ?",
                (book_id,),
            )
            conn.execute(
                "UPDATE IssuedBooks SET return_date = date('now') "
                "WHERE book_id = ? AND cust_id = ? AND return_date IS NULL",
                (book_id, cust_id),
            )
            return True

    # ------------------------------------------------------------------ #
    #  Reporting
    # ------------------------------------------------------------------ #
    def issued_books_detail(self, cust_id: int) -> List[sqlite3.Row]:
        """Return the full Book rows for every book currently issued to a customer."""
        with self._conn() as conn:
            cust = conn.execute(
                "SELECT issued_books FROM Customer WHERE cust_id = ?", (cust_id,)
            ).fetchone()
            if cust is None or not cust["issued_books"].strip():
                return []
            ids = tuple(int(x) for x in cust["issued_books"].split(","))
            placeholders = ",".join("?" * len(ids))
            return conn.execute(
                f"SELECT * FROM Books WHERE book_id IN ({placeholders}) "
                "ORDER BY book_id",
                ids,
            ).fetchall()

    def books_on_loan(self) -> List[sqlite3.Row]:
        """Return IssuedBooks entries that are still on loan."""
        with self._conn() as conn:
            return conn.execute(
                "SELECT ib.*, b.book_name, c.cust_name "
                "FROM IssuedBooks ib "
                "JOIN Books b ON ib.book_id = b.book_id "
                "JOIN Customer c ON ib.cust_id = c.cust_id "
                "WHERE ib.return_date IS NULL ORDER BY ib.issue_date DESC"
            ).fetchall()


if __name__ == "__main__":
    print("This is a library management module. Run demo.py for a demonstration.")