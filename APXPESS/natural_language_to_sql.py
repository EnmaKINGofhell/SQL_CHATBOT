import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Download necessary NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    print("Note: NLTK data download failed, but we'll continue")

class NaturalLanguageToSQL:
    def __init__(self, db_schema=None):
        """
        Initialize the NL to SQL converter with optional database schema
        
        Args:
            db_schema (dict): A dictionary describing the database tables and columns
                Example: {
                    'customers': ['id', 'name', 'email', 'signup_date'],
                    'orders': ['id', 'customer_id', 'order_date', 'total_amount']
                }
        """
        self.db_schema = db_schema
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            # Fallback if NLTK download failed
            self.stop_words = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
                               "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 
                               'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 
                               'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 
                               'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 
                               'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was',
                               'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 
                               'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 
                               'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 
                               'about', 'against', 'between', 'into', 'through', 'during', 'before', 
                               'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 
                               'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 
                               'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
                               'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 
                               'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 
                               'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 
                               'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 
                               'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', 
                               "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 
                               'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', 
                               "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 
                               'won', "won't", 'wouldn', "wouldn't"])
        
        # Keywords for query type detection
        self.query_keywords = {
            'select': ['show', 'find', 'get', 'list', 'display', 'what', 'who', 'give', 'select', 'query', 'search', 'fetch'],
            'insert': ['add', 'create', 'insert', 'put', 'register', 'new'],
            'update': ['update', 'change', 'modify', 'edit', 'alter'],
            'delete': ['delete', 'remove', 'drop', 'eliminate']
        }
        
        # Common SQL conditions and their natural language equivalents
        self.condition_mapping = {
            'greater than': '>',
            'more than': '>',
            'higher than': '>',
            'over': '>',
            'above': '>',
            'exceeds': '>',
            'less than': '<',
            'lower than': '<',
            'under': '<',
            'below': '<',
            'at most': '<=',
            'at least': '>=',
            'equal to': '=',
            'equals': '=',
            'is': '=',
            'not equal': '!=',
            'differs from': '!=',
            'not': '!=',
            'like': 'LIKE',
            'similar to': 'LIKE',
            'contains': 'LIKE',
            'starts with': 'LIKE',
            'begins with': 'LIKE',
            'ends with': 'LIKE'
        }
        
    def preprocess_query(self, natural_query):
        """Clean and normalize the natural language query"""
        # Convert to lowercase
        query = natural_query.lower()
        
        # Remove special characters, but keep some basic punctuation
        query = re.sub(r'[^\w\s.,?]', ' ', query)
        
        # Tokenize and remove stop words for analysis
        try:
            tokens = word_tokenize(query)
        except:
            # Fallback tokenization if NLTK fails
            tokens = query.split()
            
        filtered_tokens = [word for word in tokens if word not in self.stop_words]
        
        return query, filtered_tokens
        
    def detect_query_type(self, tokens):
        """Determine the likely SQL query type based on the natural language"""
        for query_type, keywords in self.query_keywords.items():
            if any(keyword in tokens for keyword in keywords):
                return query_type
        return 'select'  # Default to SELECT if no clear indicator
        
    def identify_entities(self, query):
        """
        Identify entities (tables, columns, values) from the query
        This is a simple implementation - a real system would use NER
        """
        entities = {
            'tables': [],
            'columns': [],
            'conditions': [],
            'values': []
        }
        
        # If no schema is provided, we'll have to make our best guess
        if not self.db_schema:
            return entities
            
        # Check each table in the schema
        for table, columns in self.db_schema.items():
            # Check if table name is in the query
            if table.lower() in query:
                if table not in entities['tables']:
                    entities['tables'].append(table)
                
            # Check for column names
            for column in columns:
                if column.lower() in query:
                    if column not in entities['columns']:
                        entities['columns'].append(column)
                    if table not in entities['tables']:
                        entities['tables'].append(table)
        
        # Extract potential numeric values
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', query)
        if numbers:
            entities['values'].extend(numbers)
            
        # Look for condition keywords
        for condition_phrase, operator in self.condition_mapping.items():
            if condition_phrase in query:
                entities['conditions'].append((condition_phrase, operator))
                
        return entities
        
    def extract_date_conditions(self, query):
        """Extract date-related conditions from query"""
        date_conditions = []
        
        # Check for date patterns (YYYY-MM-DD)
        dates = re.findall(r'\b\d{4}-\d{1,2}-\d{1,2}\b', query)
        
        # Look for date-related phrases
        date_phrases = [
            'before', 'after', 'between', 'since', 
            'from', 'to', 'earlier than', 'later than',
            'today', 'yesterday', 'last week', 'last month',
            'this year', 'previous year'
        ]
        
        for phrase in date_phrases:
            if phrase in query:
                # If we find both a date phrase and dates, pair them
                if dates:
                    for date in dates:
                        date_conditions.append((phrase, date))
                else:
                    date_conditions.append((phrase, None))
                    
        return date_conditions
    
    def rule_based_sql_generation(self, query, entities, query_type):
        """
        Generate SQL using rule-based approach
        """
        if query_type == 'select':
            # Determine what columns to select
            if entities['columns']:
                columns_str = ', '.join(entities['columns'])
            else:
                columns_str = '*'  # Select all columns if none specified
            
            # Determine which tables to query
            if entities['tables']:
                tables_str = ', '.join(entities['tables'])
                main_table = entities['tables'][0]  # Use first table as main reference
            else:
                # If no tables detected, we can't create a valid query
                return "SELECT * FROM [table_name] -- Unable to determine table"
            
            # Start building the query
            sql = f"SELECT {columns_str} FROM {tables_str}"
            
            # Add WHERE clause if we have conditions
            where_clauses = []
            
            # Handle direct column comparisons to values
            for column in entities['columns']:
                for value in entities['values']:
                    # Check if this column and value are related in the query
                    # Simple proximity check - better NLP would improve this
                    column_idx = query.find(column)
                    value_idx = query.find(value)
                    
                    if abs(column_idx - value_idx) < 50:  # If they're close together
                        # Determine the operator (default to = if unclear)
                        operator = '='
                        for condition_text, op in entities['conditions']:
                            if condition_text in query[min(column_idx, value_idx):max(column_idx, value_idx)]:
                                operator = op
                                break
                                
                        # For LIKE conditions, add wildcards
                        if operator == 'LIKE':
                            where_clauses.append(f"{column} LIKE '%{value}%'")
                        else:
                            where_clauses.append(f"{column} {operator} {value}")
            
            # Add WHERE clause if we found conditions
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
                
            return sql
            
        elif query_type == 'insert':
            # Simple INSERT statement
            if entities['tables']:
                table = entities['tables'][0]
                
                if entities['columns']:
                    columns_str = ', '.join(entities['columns'])
                    values_str = ', '.join(['?' for _ in entities['columns']])
                    return f"INSERT INTO {table} ({columns_str}) VALUES ({values_str})"
                else:
                    return f"INSERT INTO {table} VALUES (?) -- Unable to determine columns"
            else:
                return "INSERT INTO [table_name] VALUES (?) -- Unable to determine table"
                
        elif query_type == 'update':
            # Simple UPDATE statement
            if entities['tables']:
                table = entities['tables'][0]
                
                if entities['columns']:
                    sets = [f"{col} = ?" for col in entities['columns']]
                    sets_str = ', '.join(sets)
                    return f"UPDATE {table} SET {sets_str} WHERE condition"
                else:
                    return f"UPDATE {table} SET column = value WHERE condition -- Unable to determine columns"
            else:
                return "UPDATE [table_name] SET column = value WHERE condition -- Unable to determine table"
                
        elif query_type == 'delete':
            # Simple DELETE statement
            if entities['tables']:
                table = entities['tables'][0]
                return f"DELETE FROM {table} WHERE condition"
            else:
                return "DELETE FROM [table_name] WHERE condition -- Unable to determine table"
                
        return "SELECT * FROM table -- Unable to generate query"
            
    def generate_sql(self, natural_query):
        """
        Convert natural language query to SQL
        """
        # Preprocess the query
        query, tokens = self.preprocess_query(natural_query)
        
        # Detect the query type
        query_type = self.detect_query_type(tokens)
        
        # Identify entities in the query
        entities = self.identify_entities(query)
        
        # Extract any date conditions
        date_conditions = self.extract_date_conditions(query)
        
        # Generate SQL using rule-based approach
        sql_query = self.rule_based_sql_generation(query, entities, query_type)
        
        return sql_query
        
    def execute_query(self, sql_query, database_connection):
        """
        Execute the SQL query on the provided database connection
        
        Args:
            sql_query (str): The SQL query to execute
            database_connection: A database connection object (e.g., SQLAlchemy engine)
            
        Returns:
            The query results
        """
        try:
            # Connect to the database and execute the query
            cursor = database_connection.cursor()
            cursor.execute(sql_query)
            results = cursor.fetchall()
            return results
        except Exception as e:
            return f"Error executing query: {str(e)}"