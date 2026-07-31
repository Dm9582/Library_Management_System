"""Demo for the Library Management System
=======================================
Run:  python demo.py

This script:
  1. Creates a fresh SQLite database (demo.db).
  2. Adds sample books and customers.
  3. Issues and returns books.
  4. Prints the state of the library at each step.
  5. Cleans up (deletes demo.db) at the end.
"""

import os
import time

from library import Library


def print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def show_books(lib: Library) -> None:
    books = lib.list_books()
    if not books:
        print("  (no books in the library)")
        return
    print(f"  {'ID':<4} {'Title':<35} {'Author':<20} {'Rem/Tot':<8}")
    print(f"  {'--':<4} {'-----':<35} {'------':<20} {'-----':<8}")
    for b in books:
        print(
            f"  {b['book_id']:<4} {b['book_name'][:34]:<35} "
            f"{b['author'][:19]:<20} "
            f"{b['remaining_copies']}/{b['tot_copies']:<5}"
        )


def show_customers(lib: Library) -> None:
    customers = lib.list_customers()
    if not customers:
        print("  (no customers registered)")
        return
    print(f"  {'ID':<4} {'Name':<30} {'Issued Books':<15} {'Fees Paid':<10}")
    print(f"  {'--':<4} {'----':<30} {'------------':<15} {'---------':<10}")
    for c in customers:
        print(
            f"  {c['cust_id']:<4} {c['cust_name'][:29]:<30} "
            f"{c['issued_books']:<15} {c['fees_paid']:<10}"
        )


def show_issued(lib: Library) -> None:
    loans = lib.books_on_loan()
    if not loans:
        print("  (no books currently on loan)")
        return
    print(f"  {'Book':<30} {'Customer':<25} {'Date':<12}")
    print(f"  {'----':<30} {'--------':<25} {'----':<12}")
    for l in loans:
        print(
            f"  {l['book_name'][:29]:<30} {l['cust_name'][:24]:<25} "
            f"{l['issue_date']:<12}"
        )


def main() -> None:
    # Start fresh
    db_path = "demo.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    lib = Library(db_path)

    # --------------------------------------------------------------- #
    print_header("STEP 1 — Seed the library with books")
    # --------------------------------------------------------------- #
    books = [
        ("The Pragmatic Programmer", "Andrew Hunt & David Thomas"),
        ("Clean Code", "Robert C. Martin"),
        ("Designing Data-Intensive Applications", "Martin Kleppmann"),
        ("Structure and Interpretation of Computer Programs", "Harold Abelson"),
        ("Introduction to Algorithms", "Thomas Cormen"),
    ]
    for name, author in books:
        bids = {"tot_copies": {"the pragmatic": 3, "clean code": 2,
                    "designing data": 4, "structure and": 1, "introduction": 2}}
        copies = 2
        for key, val in bids["tot_copies"].items():
            if key in name.lower():
                copies = val
        bid = lib.add_book(name, author, copies)
        print(f"  Added book_id={bid}: {name} ({copies} copies)")

    show_books(lib)

    # --------------------------------------------------------------- #
    print_header("STEP 2 — Register customers")
    # --------------------------------------------------------------- #
    alice_id = lib.register_customer("Alice Johnson")
    bob_id = lib.register_customer("Bob Smith")
    carol_id = lib.register_customer("Carol Williams")
    print(f"  Registered cust_id={alice_id}: Alice Johnson")
    print(f"  Registered cust_id={bob_id}:   Bob Smith")
    print(f"  Registered cust_id={carol_id}: Carol Williams")

    show_customers(lib)

    # --------------------------------------------------------------- #
    print_header("STEP 3 — Issue some books")
    # --------------------------------------------------------------- #
    # Alice borrows "The Pragmatic Programmer" (book 1) and "Clean Code" (book 2)
    ok = lib.issue_book(1, alice_id)
    print(f"  Issue book 1 -> Alice: {'OK' if ok else 'FAILED'}")
    ok = lib.issue_book(2, alice_id)
    print(f"  Issue book 2 -> Alice: {'OK' if ok else 'FAILED'}")

    # Bob borrows "Designing Data-Intensive Applications" (book 3)
    ok = lib.issue_book(3, bob_id)
    print(f"  Issue book 3 -> Bob:   {'OK' if ok else 'FAILED'}")

    show_books(lib)
    show_customers(lib)
    show_issued(lib)

    # --------------------------------------------------------------- #
    print_header("STEP 4  — Alice returns Clean Code")
    # --------------------------------------------------------------- #
    ok = lib.return_book(2, alice_id)
    print(f"  Return book 2 from Alice: {'OK' if ok else 'FAILED'}")

    show_books(lib)
    show_customers(lib)

    # Alice's detailed issued list
    detail = lib.issued_books_detail(alice_id)
    print(f"\n  Alice's currently borrowed books:")
    for b in detail:
        print(f"    • {b['book_name']} by {b['author']}")

    # --------------------------------------------------------------- #
    print_header("STEP 5 — Carol tries to borrow a book with 0 remaining")
    # --------------------------------------------------------------- #
    # Book 4 has only 1 copy. Borrow it (Carol), then try again (should fail).
    ok = lib.issue_book(4, carol_id)
    print(f"  Issue book 4 -> Carol: {'OK' if ok else 'FAILED'}")
    ok2 = lib.issue_book(4, carol_id)  # second attempt — 0 remaining
    print(f"  Issue book 4 -> Carol again: {'OK' if ok2 else 'FAILED (no copies left)'}")

    show_books(lib)

    # --------------------------------------------------------------- #
    print_header("STEP 6 — Carol pays fees")
    # --------------------------------------------------------------- #
    lib.pay_fees(carol_id)
    print(f"  Carol's fees marked as paid")
    show_customers(lib)

    # --------------------------------------------------------------- #
    print_header("STEP 7 — Search books")
    # --------------------------------------------------------------- #
    results = lib.search_books("algorithms")
    print(f"  Search for 'algorithms':")
    for b in results:
        print(f"    • {b['book_name']} by {b['author']}")

    # --------------------------------------------------------------- #
    print_header("STEP 8 — Attempt to delete a customer with outstanding books")
    # --------------------------------------------------------------- #
    try:
        lib.remove_customer(alice_id)
        print("  Alice removed (unexpected — she still has a book)")
    except ValueError as e:
        print(f"  Could not remove Alice: {e}")
    print("  (This is expected — the system prevents deletion while books are out.)")

    # --------------------------------------------------------------- #
    print_header("STEP 9 — Full audit: IssuedBooks trail")
    # --------------------------------------------------------------- #
    show_issued(lib)

    # --------------------------------------------------------------- #
    print_header("All operations completed. Cleaning up...")
    # --------------------------------------------------------------- #
    lib_path = os.path.join(os.path.dirname(__file__), db_path)
    # close & remove
    del lib
    time.sleep(0.2)
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"  {db_path} removed.")

    print("\n  Demo finished successfully!\n")


if __name__ == "__main__":
    main()