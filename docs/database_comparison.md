# Database Comparison: Healthcare Data Engineering Project

## 1. Databases Compared

1. **PostgreSQL** – A relational database (SQL)
2. **MongoDB** – A document database (NoSQL)
3. **Apache Cassandra** – Wide-column store (NoSQL)

*These three represent different approaches to storing data.*

---

## 2. Basic Comparison

### PostgreSQL
**What it is:** Traditional relational database with tables and rows

**Good for:**
- Structured data (like our CSV files)
- When relationships between data are important
- Complex queries joining multiple tables

**Not so good for:**
- Flexible/changing data structures
- Very large documents or files

**For our project:**
- Can handle patients, diagnoses, procedures tables well
- Good at JOIN queries (like finding all diagnoses for a patient)
- Might need extra work for JSON files

**Setup difficulty:** Medium (need to design tables first)

---

### MongoDB
**What it is:** Stores data as documents (like JSON)

**Good for:**
- JSON data (like our diagnoses and medications files)
- Flexible data that might change
- Quick development

**Not so good for:**
- Complex relationships between data
- Transactions across multiple documents

**For our project:**
- Perfect for JSON files without conversion
- Flexible if data structure changes
- Harder to do complex queries across collections

**Setup difficulty:** Easy (just insert documents)

---

### Apache Cassandra
**What it is:** A NoSQL database using a wide-column store model.

**Good for:**
- Very high volumes of data
- Fast distributed writes and reads
- High availability and fault tolerance

**Not so good for:**
- Complex queries and joins
- Real-time analytics involving relationships

**For our project:**
- Too advanced for current use
- Better suited for large-scale hospital systems

**Setup difficulty:** High (requires planning and setup of cluster nodes)

---

## 3. Simple Feature Comparison

| Feature                | PostgreSQL         | MongoDB           | Apache Cassandra   |
|------------------------|--------------------|-------------------|-------------------|
| Type                   | Relational (SQL)   | Document (NoSQL)  | Wide-column (NoSQL) |
| Query Language         | SQL                | MongoDB QL        | CQL (Cassandra QL) |
| Best for our CSVs      | Yes                | Yes               | No                |
| Best for our JSONs     | Partial            | Yes               | No                |
| Easy to Learn          | Yes                | Yes               | No                |
| Free to Use            | Yes                | Yes               | Yes               |

---

## 4. For Our Specific Files

### If we use PostgreSQL:
- `patients.csv` → patients table
- `procedures.csv` → procedures table
- `observations.csv` → observations table
- JSON files → Need to flatten into tables or use JSON columns

### If we use MongoDB:
- Each file → Its own collection
- Can store everything as-is
- Might need to duplicate some data

### If we use Cassandra:
- Each file would become a separate table, but schema would be wide-column
- Not ideal for relational joins or hierarchical JSON data
- Suited more for event tracking or log-based systems

---

## 5. Recommendation for This Project

**For this student project, PostgreSQL is the best fit because:**
- Our data is mostly structured (CSV format)
- We need relational joins for queries (e.g., diagnoses per patient)
- SQL is widely used and easy to learn

---

## 6. Security & Compliance Table

| Database     | Has Encryption | Has User Permissions | GDPR Ready         |
|--------------|:--------------:|:-------------------:|:------------------:|
| PostgreSQL   | Yes            | Yes                 | Can be Configured  |
| MongoDB      | Yes            | Yes                 | Can be Configured  |
| Cassandra    | Yes            | Yes                 | Can be Configured  |

---

## 7. References
- [PostgreSQL tutorial](https://www.postgresqltutorial.com/)
- [MongoDB university (free)](https://learn.mongodb.com/)
- [Cassandra docs](https://cassandra.apache.org/doc/latest/) 