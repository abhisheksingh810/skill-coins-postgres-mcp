# MCP PostgreSQL Query Server

This is a Model Context Protocol (MCP) server built with FastMCP that provides tools to execute SQL queries against a PostgreSQL database and retrieve schema information.

## Features

- **SQL Query Execution**: Executes SQL queries directly against PostgreSQL database
- **Schema Information**: Provides detailed database schema information for LLM clients
- **Safe Query Execution**: Executes SQL queries safely with proper error handling
- **Comprehensive Results**: Returns SQL query, results, row count, execution time, and any errors
- **LLM Client Integration**: Designed to work with LLM clients (Claude Desktop, Copilot, etc.) for natural language to SQL conversion

## Prerequisites

- Python 3.8+
- PostgreSQL database
- LLM client (Claude Desktop, Copilot, etc.) for natural language to SQL conversion

## Installation

1. **Clone or download this project**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root with the following variables:
   ```
   # PostgreSQL Database Configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   ```

## Usage

### Running the Server

```bash
python mcp_server.py
```

The server will start and be available for MCP client connections.

### Available Tools

#### `natural_language_query`

Converts natural language queries to SQL and executes them against the PostgreSQL database.

**Input Parameters:**
- `query` (required): Natural language description of what you want to query
- `context` (optional): Additional context or information to help with SQL generation

**Output:**
- `sql_query`: Generated SQL query and context for LLM processing
- `results`: Processing instructions and schema information
- `row_count`: Number of result items
- `execution_time`: Time taken to process
- `error`: Any error message (if applicable)

**Example Queries:**
- "Show me all users who signed up in the last month"
- "What are the top 10 products by sales?"
- "Count the number of orders per customer"
- "Find customers who haven't placed an order in 30 days"
- "Get the total revenue for each month this year"

#### `execute_sql_query`

Executes SQL queries against the PostgreSQL database.

**Input Parameters:**
- `sql_query` (required): SQL query to execute
- `description` (optional): Description of what the query does

**Output:**
- `sql_query`: The executed SQL query
- `results`: Query results as a list of dictionaries
- `row_count`: Number of rows returned/affected
- `execution_time`: Time taken to execute the query
- `error`: Any error message (if applicable)

**Example Queries:**
- `SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '1 month'`
- `SELECT product_name, SUM(sales_amount) FROM sales GROUP BY product_name ORDER BY SUM(sales_amount) DESC LIMIT 10`
- `SELECT customer_id, COUNT(*) as order_count FROM orders GROUP BY customer_id`

#### `get_database_schema`

Retrieves detailed database schema information for LLM clients to use when generating SQL queries.

**Output:**
- `tables`: Detailed table and column information
- `table_count`: Total number of tables
- `schema_text`: Formatted schema information
- `status`: Success or error status

## Configuration

### Database Connection

The server connects to PostgreSQL using the following environment variables:
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

### LLM Client Integration

The server is designed to work with LLM clients like Claude Desktop, Copilot, etc. The workflow is:

1. **Natural Language Query**: Use `natural_language_query` with a natural language description
2. **Schema Retrieval**: The tool automatically gets database schema information
3. **SQL Generation**: The LLM client generates SQL based on the schema and query
4. **Query Execution**: Use `execute_sql_query` to run the generated SQL
5. **Result Processing**: The LLM client can format and present results as needed

**Alternative Workflow:**
- **Direct SQL**: Use `execute_sql_query` directly with SQL queries
- **Schema Information**: Use `get_database_schema` to get database structure for manual SQL generation

## Security Considerations

1. **Database Permissions**: Ensure the database user has appropriate permissions
2. **Query Validation**: The server includes basic SQL injection protection
3. **Schema Access**: The server retrieves schema information for LLM clients
4. **LLM Client Security**: Ensure your LLM client handles SQL generation securely

## Error Handling

The server includes comprehensive error handling for:
- Database connection failures
- Query execution errors
- Schema retrieval errors
- Missing environment variables

## Dependencies

- `fastmcp`: MCP server framework
- `psycopg2-binary`: PostgreSQL adapter
- `python-dotenv`: Environment variable management
- `pydantic`: Data validation
- `sqlalchemy`: Database toolkit (for future enhancements)

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify database credentials in `.env`
   - Ensure PostgreSQL is running
   - Check firewall settings

2. **Schema Retrieval Failed**
   - Ensure the database user has SELECT permissions on information_schema
   - Check if tables exist in the public schema

3. **LLM Client Integration**
   - Ensure your LLM client can access the MCP server
   - Verify the server is running and accessible
   - Check that the LLM client supports the required tools

## License

This project is open source and available under the MIT License. 