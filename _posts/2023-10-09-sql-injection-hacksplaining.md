---
title: "SQL Injection Walkthrough on Hacksplaining"
date: 2023-10-09 18:00:00 -0500
categories: [Web Security, Application Security]
tags: [SQL Injection, Hacksplaining, Parameterized Queries, ORM, Input Sanitization, Least Privilege, Password Hashing, Project]
description: Walkthrough notes from the Hacksplaining SQL Injection exercise, the login bypass, why the quote character matters, and the defenses, parameterized statements, ORM, input escaping and sanitizing, principle of least privilege, password hashing, and third party authentication.
image:
  path: /assets/img/blog/sql-injection-hacksplaining/image1.png
  alt: "Hacksplaining SQL Injection exercise login screen before attempting injection."
---

These are my notes from working through the **SQL Injection** exercise on [Hacksplaining](https://www.hacksplaining.com/exercises/sql-injection). The explanatory framing below follows Hacksplaining's curriculum; the screenshots and observations are from my run of the exercise.

---

## The Exercise

Guessing the password did not work, so the next step was to try terminating the string with a quote character.

![Hacksplaining SQL Injection exercise login form.](/assets/img/blog/sql-injection-hacksplaining/image1.png)

![Submitting a password value containing a single quote.](/assets/img/blog/sql-injection-hacksplaining/image2.png)

![Server response after the quote character is included in the password field.](/assets/img/blog/sql-injection-hacksplaining/image3.png)

Then, with the password set to `' or 1=1--`, the login condition is forced to true and the application lets us in.

![Login bypassed with the ' or 1=1-- payload.](/assets/img/blog/sql-injection-hacksplaining/image4.png)

---

## Why This Works

SQL injection happens when an application builds a SQL query by concatenating user input into the query string without validation or escaping. The quote character delimits strings in SQL, so an attacker can use a quote to close the string early and append their own SQL.

A vulnerable query:

```sql
SELECT * FROM users WHERE username = 'user_input';
```

If the user supplies:

```
user_input' OR '1'='1
```

The query the database actually runs becomes:

```sql
SELECT * FROM users WHERE username = 'user_input' OR '1'='1';
```

`'1'='1'` is always true, so the `WHERE` clause matches every row. Depending on what the application does with the result, this can mean an authentication bypass, data disclosure, modification, or destruction.

---

## What an Attacker Can Do

- Extract sensitive data such as Social Security numbers or credit card details.
- Enumerate user credentials and reuse them on other sites.
- Delete data or drop tables, corrupting the database.
- Inject further malicious code that runs when other users visit the site.

SQL injection is an injection attack, and because SQL databases are everywhere, it remains one of the most common attack types on the internet.

---

## Defenses

### Parameterized statements

This is the primary defense. With parameterized statements, the SQL query and the parameters are sent to the database separately. The driver knows the parameters are data, not code, so injection payloads inside them cannot change the query structure. By contrast, building the full SQL string in application code before sending it to the driver leaves the application vulnerable to whatever the user supplies.

The rule of thumb from the exercise: if you are writing SQL by concatenating strings, stop and think about what you are doing.

### Object Relational Mapping

Many teams use an ORM such as Ruby on Rails' Active Record. ORMs generate SQL for you, and they use parameterized statements under the hood, so developers rarely have to hand-write SQL at all.

### Escaping inputs

If parameterized statements are not available, the next best option is to escape special characters in inputs. Injection often works by closing the argument string early with `'` or `"`, so doubling a quote (`''`) tells SQL to treat it as part of the string rather than the end of it. Most languages provide a standard escaping function for this.

Two caveats:

- You have to apply escaping everywhere SQL is built, every time. Missing one place is enough.
- Not every injection uses quotes. Numeric ID fields don't need quotes, so a query that accepts an integer parameter can still be vulnerable no matter how rigorously you escape quote characters.

### Sanitizing inputs

Sanitizing is a good general practice. In the exercise, the supplied password `' or 1=1--` looks obviously suspicious. Reject inputs that look hostile, while being careful not to reject legitimate users. Common cleanups on `GET` and `POST` parameters:

- Check that fields like email addresses match a regular expression.
- Ensure numeric or alphanumeric fields don't contain symbol characters.
- Reject or strip whitespace and newline characters where they don't belong.

Client-side validation in JavaScript is fine for giving the user immediate feedback, but it is not a defense. Most attacks come from scripts, not browsers.

### Principle of least privilege

Each process or component should access only the resources it needs. Applications very rarely need to change the structure of the database at runtime, so production accounts should be limited to DML statements (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) and denied DDL statements (`CREATE`, `DROP`, `ALTER`). Where database design supports it, fine-grained permissions and stored procedures can lock things down further. This becomes a second line of defense if the first one fails.

### Password hashing

The exercise's login bypass worked partly because the password was stored as plain text. Storing unencrypted passwords is a serious flaw on its own. Passwords should be stored as strong one-way hashes, ideally salted. That way, an attacker who extracts the table cannot recover the original passwords.

### Third party authentication

It is often worth outsourcing authentication entirely. OAuth providers (Google, Facebook, Twitter) let users sign in with existing accounts, which means you do not roll your own authentication and your users' passwords stay with the provider rather than with you.

---

## Takeaway

The hack itself is one quote character and a short comment. The fix is layered: parameterized statements first, then a sensible mix of escaping, sanitizing, least-privilege database accounts, password hashing, and ideally outsourced authentication. Each layer covers a different failure mode.

Sources: [Hacksplaining, SQL Injection exercise and lesson](https://www.hacksplaining.com/exercises/sql-injection).
