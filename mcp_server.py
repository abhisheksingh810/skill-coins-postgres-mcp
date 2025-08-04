import os
import json
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLQuery(BaseModel):
    """Input model for SQL query execution tool."""
    sql_query: str = Field(..., description="SQL query to execute against the PostgreSQL database")
    description: Optional[str] = Field(None, description="Optional description of what the query does")

class NaturalLanguageQuery(BaseModel):
    """Input model for natural language query tool."""
    query: str = Field(..., description="Natural language description of what you want to query from the database")
    context: Optional[str] = Field(None, description="Optional context or additional information to help with SQL generation")

class QueryResult(BaseModel):
    """Output model for query results."""
    sql_query: str
    results: List[Dict[str, Any]]
    row_count: int
    execution_time: float
    error: Optional[str] = None

class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""
    
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
        }
    
    def get_connection(self):
        """Get a database connection."""
        try:
            conn = psycopg2.connect(**self.connection_params)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def execute_query(self, sql_query: str) -> QueryResult:
        """Execute a SQL query and return results."""
        import time
        start_time = time.time()
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(sql_query)
            
            # Fetch results
            if cursor.description:  # SELECT query
                results = [dict(row) for row in cursor.fetchall()]
                row_count = len(results)
            else:  # INSERT, UPDATE, DELETE query
                results = []
                row_count = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                sql_query=sql_query,
                results=results,
                row_count=row_count,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution failed: {e}")
            return QueryResult(
                sql_query=sql_query,
                results=[],
                row_count=0,
                execution_time=execution_time,
                error=str(e)
            )
    
    def get_schema_info(self) -> str:
        """Get database schema information to help with SQL generation."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("""
                SELECT 
                    t.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable
                FROM information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name
                WHERE t.table_schema = 'public'
                ORDER BY t.table_name, c.ordinal_position
            """)
            
            schema_info = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Format schema information
            tables = {}
            for row in schema_info:
                table_name, column_name, data_type, is_nullable = row
                if table_name not in tables:
                    tables[table_name] = []
                tables[table_name].append({
                    'column': column_name,
                    'type': data_type,
                    'nullable': is_nullable
                })
            
            schema_text = "Database Schema:\n"
            for table_name, columns in tables.items():
                schema_text += f"\nTable: {table_name}\n"
                for col in columns:
                    schema_text += f"  - {col['column']} ({col['type']}, nullable: {col['nullable']})\n"
            
            return schema_text
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            return "Unable to retrieve database schema information."



# Initialize components
db_manager = DatabaseManager()

# Create FastMCP server
app = FastMCP("postgres-nl-query-server")

@app.tool()
async def execute_sql_query(input_data: SQLQuery) -> QueryResult:
    """
    Execute a SQL query against the PostgreSQL database and return the results.
    
    This tool takes a SQL query and executes it directly against the database.
    The LLM client (like Claude Desktop, Copilot, etc.) should handle the conversion
    from natural language to SQL and any result transformation.
    
    Examples:
    - "SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '1 month'"
    - "SELECT product_name, SUM(sales_amount) FROM sales GROUP BY product_name ORDER BY SUM(sales_amount) DESC LIMIT 10"
    - "SELECT customer_id, COUNT(*) as order_count FROM orders GROUP BY customer_id"
    """
    try:
        logger.info(f"Executing SQL query: {input_data.sql_query}")
        
        # Execute the query
        result = db_manager.execute_query(input_data.sql_query)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in SQL query execution tool: {e}")
        return QueryResult(
            sql_query=input_data.sql_query,
            results=[],
            row_count=0,
            execution_time=0.0,
            error=str(e)
        )

@app.tool()
async def natural_language_query(input_data: str) -> QueryResult:
    """
    Convert a natural language query to SQL and execute it against the PostgreSQL database.
    
    This tool takes a natural language description of what you want to query from the database,
    automatically retrieves the database schema, and provides both the generated SQL and the results.
    The LLM client will handle the SQL generation based on the schema information.
    
    Examples:
    - "Show me all users who signed up in the last month"
    - "What are the top 10 products by sales?"
    - "Count the number of orders per customer"
    - "Find customers who haven't placed an order in 30 days"
    - "Get the total revenue for each month this year"
    """
    try:
        logger.info(f"Processing natural language query: {input_data}")
        
        # Get database schema information
        schema_info = db_manager.get_schema_info()
        logger.info("Retrieved database schema information")
        
        # Create a comprehensive prompt for the LLM client
        prompt_context = f"""
Database Schema Information:
{schema_info}

User Query: {input_data}

Please generate a PostgreSQL SQL query based on the user's natural language request and the database schema above.
The query should be safe, efficient, and return the requested data.

Requirements:
1. Use only the tables and columns available in the schema
2. Use PostgreSQL syntax
3. Include appropriate WHERE clauses for security
4. Add LIMIT clauses for large result sets if appropriate
5. Use proper JOINs when querying multiple tables
6. Return only the SQL query, no explanations

Generated SQL Query:
"""
        
        # Return a special result that includes the prompt for the LLM client
        return QueryResult(
            sql_query=prompt_context,
            results=[{
                "message": "Please use the LLM client to generate SQL from the provided context and schema information, then call execute_sql_query with the generated SQL.",
                "schema_info": schema_info,
                "user_query": input_data,
                "next_step": "Call execute_sql_query with the generated SQL"
            }],
            row_count=1,
            execution_time=0.0,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error in natural language query tool: {e}")
        return QueryResult(
            sql_query="",
            results=[],
            row_count=0,
            execution_time=0.0,
            error=str(e)
        )

@app.tool()
async def get_database_schema() -> Dict[str, Any]:
    """
    Get the database schema information to help with SQL query generation.
    
    This tool returns detailed information about all tables, columns, and their types
    in the PostgreSQL database. The LLM client can use this information to generate
    accurate SQL queries.
    
    Returns:
    - tables: List of tables with their columns and data types
    - table_count: Total number of tables
    - schema_text: Formatted schema information for easy reading
    """
    try:
        logger.info("Retrieving database schema information")
        
        schema_info = db_manager.get_schema_info()
        
        # Get detailed table information
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get table information
        cursor.execute("""
            SELECT 
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.character_maximum_length
            FROM information_schema.tables t
            JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = 'public'
            ORDER BY t.table_name, c.ordinal_position
        """)
        
        schema_data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Format schema information
        tables = {}
        for row in schema_data:
            table_name, column_name, data_type, is_nullable, column_default, max_length = row
            if table_name not in tables:
                tables[table_name] = []
            
            column_info = {
                'column': column_name,
                'type': data_type,
                'nullable': is_nullable == 'YES',
                'default': column_default,
                'max_length': max_length
            }
            tables[table_name].append(column_info)
        
        return {
            "tables": tables,
            "table_count": len(tables),
            "schema_text": schema_info,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving database schema: {e}")
        return {
            "tables": {},
            "table_count": 0,
            "schema_text": f"Error retrieving schema: {str(e)}",
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    # Validate environment variables
    required_env_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        exit(1)
    
    print("Starting MCP Server...")
    print("Available tools:")
    print("- natural_language_query: Convert natural language to SQL and execute")
    print("- execute_sql_query: Execute SQL queries against PostgreSQL database")
    print("- get_database_schema: Get database schema information")
    
    port = int(os.getenv('PORT', '8000'))
    app.run(transport='streamable-http', port=port)

