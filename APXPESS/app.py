from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from natural_language_to_sql import NaturalLanguageToSQL

app = Flask(__name__)

# Define your database schema
DB_SCHEMA = {
    'customers': ['id', 'name', 'email', 'signup_date', 'country'],
    'orders': ['id', 'customer_id', 'order_date', 'total_amount', 'status'],
    'products': ['id', 'name', 'category', 'price', 'stock']
}

# Initialize the NL to SQL converter
nl_to_sql = NaturalLanguageToSQL(db_schema=DB_SCHEMA)

# Ensure the templates directory exists
os.makedirs('templates', exist_ok=True)

# Create the HTML template
with open('templates/index.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Assistant</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="max-w-4xl mx-auto">
            <h1 class="text-3xl font-bold text-center mb-8">SQL Assistant</h1>
            <p class="text-center text-gray-600 mb-8">Ask questions about your data in plain English</p>
            
            <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                <div class="mb-4">
                    <label for="queryInput" class="block text-sm font-medium text-gray-700 mb-2">Your Question:</label>
                    <div class="flex">
                        <input type="text" id="queryInput" 
                               class="flex-grow px-4 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                               placeholder="e.g., Show me all customers from the USA who spent more than $1000">
                        <button id="submitBtn" 
                                class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-r-md transition duration-200">
                            Ask
                        </button>
                    </div>
                </div>
                
                <div id="examples" class="text-sm text-gray-500 mb-6">
                    <p class="mb-1">Example questions:</p>
                    <ul class="list-disc pl-5">
                        <li class="example-query cursor-pointer hover:text-blue-600">Show all customers from Canada</li>
                        <li class="example-query cursor-pointer hover:text-blue-600">Find orders with total amount greater than 500</li>
                        <li class="example-query cursor-pointer hover:text-blue-600">List all products in the Electronics category with stock less than 10</li>
                    </ul>
                </div>
            </div>
            
            <div id="results" class="hidden bg-white rounded-lg shadow-md p-6">
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-2">Generated SQL Query:</h3>
                    <div id="sqlQuery" class="bg-gray-100 p-4 rounded-md font-mono text-sm overflow-x-auto"></div>
                </div>
                
                <div>
                    <h3 class="text-lg font-semibold text-gray-800 mb-2">Results:</h3>
                    <div id="resultTable" class="overflow-x-auto">
                        <!-- Results will be inserted here -->
                    </div>
                    <p id="noResults" class="hidden text-gray-500 italic py-4">No results found.</p>
                    <p id="errorMessage" class="hidden text-red-500 py-4"></p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        $(document).ready(function() {
            // Example queries
            $('.example-query').click(function() {
                $('#queryInput').val($(this).text());
                $('#submitBtn').click();
            });
            
            // Submit query
            $('#submitBtn').click(function() {
                const query = $('#queryInput').val().trim();
                if (!query) return;
                
                // Show loading state
                $('#submitBtn').text('Processing...').attr('disabled', true);
                
                // Send query to backend
                $.ajax({
                    url: '/query',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({ query: query }),
                    success: function(response) {
                        // Display results
                        $('#results').removeClass('hidden');
                        $('#sqlQuery').text(response.sql_query);
                        
                        // Reset button
                        $('#submitBtn').text('Ask').attr('disabled', false);
                        
                        // Handle error
                        if (response.error) {
                            $('#resultTable').empty();
                            $('#noResults').addClass('hidden');
                            $('#errorMessage').text(response.error).removeClass('hidden');
                            return;
                        }
                        
                        // Hide error message if previously shown
                        $('#errorMessage').addClass('hidden');
                        
                        // Check if we have results
                        if (response.results && response.results.length > 0) {
                            $('#noResults').addClass('hidden');
                            
                            // Create table
                            const table = $('<table class="min-w-full divide-y divide-gray-200"></table>');
                            
                            // Table header
                            const thead = $('<thead class="bg-gray-50"></thead>');
                            const headerRow = $('<tr></tr>');
                            
                            // Get column names from first result
                            const columns = Object.keys(response.results[0]);
                            columns.forEach(column => {
                                headerRow.append(`<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${column}</th>`);
                            });
                            
                            thead.append(headerRow);
                            table.append(thead);
                            
                            // Table body
                            const tbody = $('<tbody class="bg-white divide-y divide-gray-200"></tbody>');
                            response.results.forEach(row => {
                                const tr = $('<tr></tr>');
                                columns.forEach(column => {
                                    tr.append(`<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row[column]}</td>`);
                                });
                                tbody.append(tr);
                            });
                            
                            table.append(tbody);
                            $('#resultTable').empty().append(table);
                        } else {
                            $('#resultTable').empty();
                            $('#noResults').removeClass('hidden');
                        }
                    },
                    error: function(xhr, status, error) {
                        $('#submitBtn').text('Ask').attr('disabled', false);
                        $('#results').removeClass('hidden');
                        $('#resultTable').empty();
                        $('#noResults').addClass('hidden');
                        $('#errorMessage').text('Server error: ' + error).removeClass('hidden');
                    }
                });
            });
            
            // Allow pressing Enter to submit
            $('#queryInput').keypress(function(e) {
                if (e.which == 13) {
                    $('#submitBtn').click();
                }
            });
        });
    </script>
</body>
</html>
    ''')

# Database connection
def get_db_connection():
    # Create demo database if it doesn't exist
    if not os.path.exists('demo.db'):
        create_demo_db()
    conn = sqlite3.connect('demo.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_demo_db():
    """Create a demo database with sample data"""
    conn = sqlite3.connect('demo.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE customers
                 (id INTEGER PRIMARY KEY, name TEXT, email TEXT, signup_date TEXT, country TEXT)''')
    c.execute('''CREATE TABLE orders
                 (id INTEGER PRIMARY KEY, customer_id INTEGER, order_date TEXT, 
                  total_amount REAL, status TEXT)''')
    c.execute('''CREATE TABLE products
                 (id INTEGER PRIMARY KEY, name TEXT, category TEXT, 
                  price REAL, stock INTEGER)''')
    
    # Insert sample data
    customers = [
        (1, 'John Smith', 'john@example.com', '2022-01-15', 'USA'),
        (2, 'Emma Johnson', 'emma@example.com', '2022-02-20', 'Canada'),
        (3, 'Michael Brown', 'michael@example.com', '2022-03-10', 'USA'),
        (4, 'Sophia Lee', 'sophia@example.com', '2022-04-05', 'Canada'),
        (5, 'William Davis', 'william@example.com', '2022-05-25', 'UK')
    ]
    
    orders = [
        (1, 1, '2022-02-10', 250.99, 'Completed'),
        (2, 2, '2022-03-15', 120.50, 'Completed'),
        (3, 3, '2022-04-20', 550.75, 'Completed'),
        (4, 1, '2022-05-05', 75.25, 'Completed'),
        (5, 4, '2022-06-10', 310.20, 'Pending'),
        (6, 5, '2022-07-15', 420.80, 'Completed'),
        (7, 2, '2022-08-20', 200.00, 'Pending'),
        (8, 3, '2022-09-25', 600.50, 'Completed')
    ]
    
    products = [
        (1, 'Laptop', 'Electronics', 999.99, 15),
        (2, 'Smartphone', 'Electronics', 699.99, 25),
        (3, 'Headphones', 'Electronics', 149.99, 50),
        (4, 'T-shirt', 'Clothing', 29.99, 100),
        (5, 'Jeans', 'Clothing', 59.99, 75),
        (6, 'Coffee Table', 'Furniture', 199.99, 10),
        (7, 'Sofa', 'Furniture', 899.99, 5),
        (8, 'Blender', 'Kitchen', 79.99, 30),
        (9, 'Microwave', 'Kitchen', 149.99, 8),
        (10, 'Tablet', 'Electronics', 349.99, 0)
    ]
    
    c.executemany('INSERT INTO customers VALUES (?,?,?,?,?)', customers)
    c.executemany('INSERT INTO orders VALUES (?,?,?,?,?)', orders)
    c.executemany('INSERT INTO products VALUES (?,?,?,?,?)', products)
    
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def process_query():
    data = request.json
    natural_query = data.get('query', '')
    
    if not natural_query:
        return jsonify({'error': 'No query provided'})
    
    # Convert natural language to SQL
    sql_query = nl_to_sql.generate_sql(natural_query)
    
    # Execute the SQL query
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        
        # Convert results to a list of dictionaries
        formatted_results = [dict(row) for row in results]
        
        return jsonify({
            'natural_query': natural_query,
            'sql_query': sql_query,
            'results': formatted_results
        })
    except Exception as e:
        return jsonify({
            'natural_query': natural_query,
            'sql_query': sql_query,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)