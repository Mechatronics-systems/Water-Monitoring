# db.py - Updated version with advanced filtering
from sqlalchemy import create_engine, text
import pandas as pd

DB_URI = "mysql+mysqlconnector://root:22BCT0018@localhost:3306/may_2025_data"
engine = create_engine(DB_URI)

def fetch_data(table_name, 
              start_date=None, 
              end_date=None, 
              date_column='data_date',
              filter_column=None,
              filter_value=None):
    """
    Enhanced data fetching with multiple filter capabilities
    """
    base_query = f"SELECT * FROM {table_name}"
    conditions = []
    params = {}

    # Date range filtering
    if start_date and end_date:
        conditions.append(f"{date_column} BETWEEN :start_date AND :end_date")
        params.update({'start_date': start_date, 'end_date': end_date})

    # Column-value filtering
    if filter_column and filter_value is not None:
        conditions.append(f"{filter_column} = :filter_value")
        params['filter_value'] = filter_value

    # Build final query
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    # Add ordering if date column exists
    if date_column:
        base_query += f" ORDER BY {date_column}"

    try:
        return pd.read_sql(
            text(base_query), 
            engine.connect(), 
            params=params
        )
    except Exception as e:
        print(f"Database error: {str(e)}")
        return pd.DataFrame()