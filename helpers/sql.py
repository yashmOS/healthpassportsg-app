import os
import logging
import sqlite3


logger = logging.getLogger(__name__)


class SQLITE:
    def __init__(self, database, traceback = False):
        self.database = os.path.abspath(database) 
        self.traceback = traceback
        
        # Create empty db file if it doesn't exist
        if not os.path.exists(self.database):
            logger.info(f"Creating new database: {self.database}")
            open(self.database, 'a').close()
        
        try:
            with sqlite3.connect(self.database) as connection:

                # Set traceback = True to display the sql query being execute
                if traceback:
                    connection.set_trace_callback(logger.info)
                
                # Test connection
                cursor = connection.cursor()
                cursor.execute("SELECT 1")  
                logger.info(f"Database connection established to {database}")

                # Initialize database with schema.sql
                try:
                    with open("static/schema.sql", "r") as file:
                        cursor.executescript(file.read())
                except FileNotFoundError:
                    logger.info("Cannot find static/schema.sql file. Skipping...")

                cursor.close()
        
        except sqlite3.Error as error:
            logger.error(f"Error connecting to {self.database}", exc_info=True)
            raise  

    def execute(self, query, *args):
        """Execute SQL query and return results for SELECT queries"""
        result = None
        
        try:
            with sqlite3.connect(self.database) as connection:  

                 # Config to get rows as dictionaries
                connection.row_factory = sqlite3.Row 
                
                # Print the sql query being executed
                if self.traceback:
                    connection.set_trace_callback(logging.info)
                
                # Execute the query
                cursor = connection.cursor()
                cursor.execute(query, args)
                
                if query.strip().upper().startswith("SELECT"):
                    result = cursor.fetchall()
                else:
                    connection.commit()
                
                cursor.close()
                
        except sqlite3.Error as error:
            logger.error(f"Error executing query: {query}", exc_info=True)
            raise  
        
        return result

