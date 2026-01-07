import os
from dotenv import load_dotenv
from app import app

# Load environment variables
load_dotenv()

def main():
    # Check if we have the necessary environment variables
    database_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    print(f"Using database: {database_uri}")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5002)

if __name__ == '__main__':
    main()