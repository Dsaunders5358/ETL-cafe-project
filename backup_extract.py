from csv import DictWriter
import psycopg2
import boto3
import random

def lambda_handler(event, context):
    s3 = boto3.resource('s3')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    print(key)
    extract_transaction_data(key, bucket)

def connect_to_database():
    ssm = boto3.client('ssm')
    parameter = ssm.get_parameter(Name='redshift-cluster-master-pass', WithDecryption=True)
    PASS = parameter['Parameter']['Value'] # gets master redshift password
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

def extract_transaction_data(file_name, bucket_name):
    id = random.randint(1, 100000)
    conn = connect_to_database()
    cur = conn.cursor()
    cur.execute(create_staging_table(id))
    print("Staging Table Created")
    cur.execute(copy_data_from_s3_bucket(file_name, bucket_name, id))
    print("Data Copied to S3 Bucket")
    cur.execute(create_store_staging_table(id))
    print("Store Staging Created")
    cur.execute(insert_store_staging_data(id))
    print("Inserted Data in Store Staging Table")
    cur.execute(insert_store_data_from_staging_table(id))
    print("Inserted Data into main Stores table")
    cur.execute(create_customer_staging_table(id))
    print("Customer Staging Table Created")
    cur.execute(insert_hashed_data_to_staging(id))
    print("Hashed data added to staging")
    cur.execute(update_store_id_customer_staging(id))
    print("Store IDS added to staging")
    cur.execute(add_data_to_main_customers_table(id))
    print("Data added to main customer table")
    cur.execute(create_transaction_staging_table(id))
    print("Transaction staging table created")
    cur.execute(add_transaction_raw_to_staging(id))
    print("Raw data added to transaction staging")
    cur.execute(add_store_id_to_staging_transactions(id))
    print("Store IDS added to transaction staging")
    cur.execute(update_customer_id_to_staging_transactions(id))
    print("Customer IDS added to transaction staging")
    cur.execute(add_transactions_to_final_database(id))
    print("added transactions to final database")
    cur.execute(add_transaction_id_back_to_staging(id))
    print("transaction IDS added to transaction staging for products")
    cur.execute(create_products_staging_area(id))
    print("Created Products staging area")
    cur.execute(get_products_with_transactions_from_database(id))
    products = cur.fetchall()
    extracted_products = extract_products_into_individual_items(products)
    save_to_csv = seperate_extracted_products_for_database(extracted_products)
    product_csv_command, product_csv_id = save_to_csv_copy_to_s3(save_to_csv, id)
    cur.execute(product_csv_command)
    print("products data copied to staging table")
    cur.execute(alter_products_staging_product_id(id))
    cur.execute(alter_products_staging_flavour_id(id))
    print("Added ID columns to products staging table")
    cur.execute(add_products_from_staging_to_final(id))
    print("Added products into final Database")
    cur.execute(add_flavours_from_staging_to_final(id))
    print("Added flavours from staging into final")
    cur.execute(add_product_id_to_products_staging(id))
    cur.execute(add_flavour_id_to_products_staging(id))
    print("IDs added to staging table")
    cur.execute(add_inventory_to_baskets_final(id))
    print("All data added to database")
    cur.execute(remove_all_staging_tables(id))
    conn.commit()
    cur.close()
    conn.close()
    
    s3 = boto3.resource('s3')
    copy_source = {'Bucket': 'ads-raw-data', 'Key' : file_name}
    bucket = s3.Bucket('ads-processed-data')
    obj = bucket.Object(file_name)
    obj.copy(copy_source)
    s3.Object('ads-raw-data', file_name).delete()
    s3.Object('ads-processed-data', f'{product_csv_id}.csv').delete()
    
def save_to_csv_copy_to_s3(csv_file, id):
    random_id = str(random.randint(1,10000))
    with open(f"/tmp/{random_id}.csv", "w", newline='') as data:
        key_headers = ["transaction_id", "product_name", "price", "flavour"]
        writer = DictWriter(data, fieldnames = key_headers)
        writer.writeheader()
        writer.writerows(csv_file)
    s3 = boto3.client('s3')
    s3.upload_file(
        Filename=f"/tmp/{random_id}.csv",
        Bucket = "ads-processed-data",
        Key = f"{random_id}.csv",
    )
    sql = \
        f"""COPY products_staging{id} FROM 's3://ads-processed-data/{random_id}.csv'
        iam_role 'arn:aws:iam::936861287436:role/RedshiftS3Role'
        CSV
        IGNOREHEADER 1;"""
    return sql,random_id
    
    

def copy_data_from_s3_bucket(key, bucket, id):
    copy = \
    f""" COPY raw_staging_area{id} from 's3://{bucket}/{key}' 
    iam_role 'arn:aws:iam::936861287436:role/RedshiftS3Role'
    CSV;
    """
    return copy

def create_staging_table(id):
    raw_staging_area = \
    f""" CREATE TABLE IF NOT EXISTS raw_staging_area{id}(
        time_stamp VARCHAR(255),
        store_name VARCHAR(255),
        customer_name VARCHAR(255),
        products VARCHAR(1000),
        total_price NUMERIC (10,2),
        payment_type VARCHAR(255),
        card_number VARCHAR(255)
    )
    """
    return raw_staging_area

def create_store_staging_table(id):
    create_store_staging = \
    f"""CREATE TABLE IF NOT EXISTS stores_staging{id} (
        store_name VARCHAR(255)
        )"""
    return create_store_staging

def insert_store_staging_data(id):
    insert_store_data_into_stores_staging = \
    f"""INSERT INTO stores_staging{id} (store_name)
    (SELECT DISTINCT store_name FROM raw_staging_area{id} a
    WHERE NOT EXISTS(SELECT 0 FROM stores_staging{id} b where a.store_name = b.store_name))"""
    return insert_store_data_into_stores_staging

def insert_store_data_from_staging_table(id):
    insert_data_into_main_stores_table = \
    f"""INSERT INTO stores (store_name)
    (SELECT store_name FROM stores_staging{id} a
    WHERE NOT EXISTS(SELECT 0 FROM stores b WHERE a.store_name = b.store_name))"""
    return insert_data_into_main_stores_table

def create_customer_staging_table(id):
    create_customer_staging = \
    f"""CREATE TABLE IF NOT EXISTS customer_staging{id} (
        customer_name VARCHAR(255),
        store_name VARCHAR(255),
        store_id INT
        )
        """
    return create_customer_staging

def insert_hashed_data_to_staging(id):
    insert_hashed_name_plus_store = \
    f"""INSERT INTO customer_staging{id} (customer_name, store_name)
    (SELECT DISTINCT MD5(customer_name), store_name FROM raw_staging_area{id} a
    WHERE NOT EXISTS(SELECT 0 FROM customer_staging{id} b WHERE MD5(a.customer_name) = b.customer_name AND a.store_name = b.store_name))"""
    return insert_hashed_name_plus_store

def update_store_id_customer_staging(id):
    update_store_name_with_id_in_customers = \
    f"""UPDATE customer_staging{id} a
    SET store_id = b.store_id
    FROM stores b
    WHERE a.store_name = b.store_name"""
    return update_store_name_with_id_in_customers 

def add_data_to_main_customers_table(id):
    add_customer_data_to_final_table = \
    f"""INSERT INTO customers (customer_name, store_id)
    (SELECT customer_name, store_id FROM customer_staging{id} a
    WHERE NOT EXISTS(SELECT 0 FROM customers b WHERE a.customer_name = b.customer_name AND a.store_id = b.store_id))"""
    return add_customer_data_to_final_table

def create_transaction_staging_table(id):
    create_transaction_staging_table = \
        f"""CREATE TABLE IF NOT EXISTS transaction_staging{id} (
        time_stamp TIMESTAMP,
        store_name VARCHAR(255),
        store_id INT,
        customer_name VARCHAR(255),
        customer_id INT,
        products VARCHAR(1000),
        total_price NUMERIC(10, 2),
        payment_type VARCHAR(255),
        transaction_id INT
        )
        """
    return create_transaction_staging_table
            
def add_transaction_raw_to_staging(id):
    add_transaction_data_to_staging_table = \
        f"""INSERT INTO transaction_staging{id}(time_stamp, store_name, customer_name, products, total_price, payment_type)
        (SELECT to_timestamp(time_stamp,'DD-MM-YYYY HH24:MI:SS'), store_name, MD5(customer_name), products, total_price, payment_type FROM raw_staging_area{id})"""
    return add_transaction_data_to_staging_table

def add_store_id_to_staging_transactions(id):
    update_store_id_in_staging_table = \
        f"""UPDATE transaction_staging{id} a
        SET store_id = b.store_id
        FROM stores b
        WHERE a.store_name = b.store_name"""
    return update_store_id_in_staging_table
        
def update_customer_id_to_staging_transactions(id):
    update_customer_id_in_staging_table = \
        f"""UPDATE transaction_staging{id} a
        SET customer_id = b.customer_id
        FROM customers b
        WHERE a.customer_name = b.customer_name"""
    return update_customer_id_in_staging_table

def add_transactions_to_final_database(id):
    add_transaction_to_main_database = \
        f"""INSERT INTO transactions (time_stamp, store_id, customer_id, total_price, payment_type)
        (SELECT time_stamp, store_id, customer_id, total_price, payment_type FROM transaction_staging{id})"""
    return add_transaction_to_main_database
        
def add_transaction_id_back_to_staging(id):
    add_transaction_id_to_staging_table = \
        f"""UPDATE transaction_staging{id} a
        SET transaction_id = b.transaction_id
        FROM transactions b
        WHERE a.time_stamp = b.time_stamp AND a.store_id = b.store_id AND a.customer_id = b.customer_id AND a.total_price = b.total_price AND a.payment_type = b.payment_type"""
    return add_transaction_id_to_staging_table

def get_products_with_transactions_from_database(id):
    sql = \
        f"""SELECT products,transaction_id FROM transaction_staging{id}"""
    return sql
        
def extract_products_into_individual_items(product_list):
    basket_list = []
    id_list = []
    basket_dict = []
    for row in product_list:
        basket_list.append(row[0])
        id_list.append(row[1])
    for basket, id in zip(basket_list, id_list):
        new_list = basket.split(", ")
        for items in new_list:
            basket_dict.append({id : items})
    return basket_dict

def seperate_extracted_products_for_database(products_dict):
    dict_for_database = []
    for dict in products_dict:
        [value] = dict.items()
        new_values = value[1].split(" - ")
        if len(new_values) > 2:
            dict_for_database.append({"transaction_id": value[0], "product_name" : new_values[0], "price" : new_values[-1], "flavour" : new_values[1]})
        else:
            dict_for_database.append({"transaction_id": value[0], "product_name" : new_values[0], "price" : new_values[-1], "flavour" : None})
    return dict_for_database

def create_products_staging_area(id):
    sql = \
        f"""CREATE TABLE products_staging{id}(
            transaction_id INT,
            product_name VARCHAR(255),
            price NUMERIC (10,2),
            flavour_name VARCHAR(255)
            )"""
    return sql

def alter_products_staging_product_id(id):
    sql = \
        f"""ALTER TABLE products_staging{id}
    add column product_id INT"""
    return sql

def alter_products_staging_flavour_id(id):
    sql = \
        f"""ALTER TABLE products_staging{id}
        add column flavour_id INT"""
    return sql

def add_product_id_to_products_staging(id):
    sql = \
        f"""UPDATE products_staging{id} a
        SET product_id = b.product_id
        FROM products b
        WHERE a.product_name = b.product_name"""
    return sql

def add_flavour_id_to_products_staging(id):
    sql = \
        f"""UPDATE products_staging{id} a
        SET flavour_id = b.flavour_id
        FROM flavours b
        WHERE a.flavour_name = b.flavour_name"""
    return sql

def add_products_from_staging_to_final(id):
    sql = \
        f"""INSERT INTO products (product_name, price)
        (SELECT DISTINCT product_name, price FROM products_staging{id} a
        WHERE NOT EXISTS(SELECT 0 FROM products b WHERE a.product_name = b.product_name))"""
    return sql

def add_flavours_from_staging_to_final(id):
    sql = \
        f"""INSERT INTO flavours (flavour_name)
        (SELECT DISTINCT flavour_name FROM products_staging{id} a
        WHERE NOT EXISTS(SELECT 0 FROM flavours b WHERE a.flavour_name = b.flavour_name))"""
    return sql

def add_inventory_to_baskets_final(id):
    sql = \
        f"""INSERT INTO baskets (transaction_id, product_id, flavour_id)
        (SELECT transaction_id, product_id, flavour_id FROM products_staging{id})"""
    return sql

def remove_all_staging_tables(id):
    sql = \
        f"""DROP TABLE customer_staging{id};
        DROP TABLE products_staging{id};
        DROP TABLE raw_staging_area{id};
        DROP TABLE stores_staging{id};
        DROP TABLE transaction_staging{id};"""
    return sql