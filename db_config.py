import psycopg2

def get_connection():
    return psycopg2.connect(
        host="hospital-db.cxtyds3zfybx.us-east-1.rds.amazonaws.com",  # your RDS endpoint
        port=5432,
        database="HospitalDB",
        user="postgres",          # your RDS username
        password="Bittu99009900"  # replace with your actual password
    )
