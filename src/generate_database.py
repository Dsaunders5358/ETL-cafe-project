import psycopg2
import boto3

ssm = boto3.client('ssm')
parameter = ssm.get_parameter(Name='redshift-cluster-master-pass', WithDecryption=True)
PASS = parameter['Parameter']['Value'] # gets master redshift password

def lambda_handler(event, context):
    apply_database_schema()
        

def connect_to_database():
    rs_port = 5439
    database_id = 'ads'
    rs_host = 'redshiftcluster-ulcxip6pepqm.clj0hthde0xh.eu-west-1.redshift.amazonaws.com'
    conn = psycopg2.connect(
        host=rs_host,
        port=rs_port,
        user='awsuser',
        password=PASS,
        database=database_id
        )
    return conn 

def apply_database_schema():
    conn = connect_to_database()
    cur = conn.cursor()
    cur.execute(\
        """CREATE TABLE IF NOT EXISTS products(
            product_id INT identity(1, 1),
            product_name VARCHAR(255) NOT NULL,
            price NUMERIC(10,2)NOT NULL,
            PRIMARY KEY (product_id),
            UNIQUE (product_name)
        )
        """)
    cur.execute(\
        """CREATE TABLE IF NOT EXISTS flavours(
            flavour_id INT identity(1, 1),
            flavour_name VARCHAR(255) NOT NULL,
            PRIMARY KEY (flavour_id),
            UNIQUE (flavour_name)
        )
        """)
    cur.execute(\
        """CREATE TABLE IF NOT EXISTS stores(
            store_id INT identity(1, 1),
            store_name VARCHAR(255) NOT NULL,
            primary key(store_id),
            UNIQUE (store_name)
        )
        """)
    cur.execute(\
        """CREATE TABLE IF NOT EXISTS customers(
            customer_id INT identity(1, 1),
            customer_name  varchar(255) NOT NULL,
            store_id INT NOT NULL references stores (store_id),
            PRIMARY KEY(customer_id),
            UNIQUE (customer_name, store_id)
        )
        """
        )
    cur.execute(\
        """CREATE TABLE IF NOT EXISTS transactions(
            transaction_id INT identity(1, 1),
            time_stamp timestamp,
            store_id INT NOT NULL references stores (store_id),
            customer_id INT NOT NULL references customers (customer_id),
            total_price DECIMAL(10, 2) NOT NULL,
            payment_type VARCHAR(255) NOT NULL,
            PRIMARY KEY (transaction_id)
            )
            """
        )
    cur.execute(\
        """CREATE TABLE IF NOT EXISTS baskets(
            transaction_id INT references transactions (transaction_id),
            product_id INT references products (product_id),
            flavour_id INT references flavours (flavour_id)
        )
        """)
    conn.commit()
    cur.close()
    conn.close()
