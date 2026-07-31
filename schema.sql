-- Library Management System Schema
-- ----------------------------------
-- SQLite schema for a simple library management system
-- with Books and Customer tables.

CREATE TABLE IF NOT EXISTS Books (
    book_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    book_name       TEXT    NOT NULL,
    author          TEXT    NOT NULL,
    tot_copies      INTEGER NOT NULL DEFAULT 0 CHECK (tot_copies >= 0),
    remaining_copies INTEGER NOT NULL DEFAULT 0 CHECK (remaining_copies >= 0)
        -- A CHECK ensures we never show negative copies.
        -- remaining_copies <= tot_copies should always hold.
);

CREATE TABLE IF NOT EXISTS Customer (
    cust_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    cust_name       TEXT    NOT NULL,
    issued_books    TEXT    DEFAULT ''
        -- Comma-separated list of book_ids currently issued to this customer.
        -- e.g. '3,7,12'  (empty string means none issued)
    ,
    fees_paid       TEXT    NOT NULL DEFAULT 'No'
        -- 'No' or 'Yes' — whether the customer has paid outstanding fees.
);

-- Optional: a junction table for fine-grained issuing/returning.
-- The Customer.issued_books column is a denorm view that mirrors this table
-- for quick reads, but the IssuedBooks table keeps a full audit trail.
CREATE TABLE IF NOT EXISTS IssuedBooks (
    issue_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id     INTEGER NOT NULL,
    cust_id     INTEGER NOT NULL,
    issue_date  TEXT    NOT NULL DEFAULT (date('now')),
    return_date TEXT,          -- NULL means still on loan
    FOREIGN KEY (book_id) REFERENCES Books(book_id),
    FOREIGN KEY (cust_id)  REFERENCES Customer(cust_id)
);