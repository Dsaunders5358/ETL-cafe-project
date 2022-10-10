import pandas as pd
import psycopg2
from sqlalchemy import create_engine
hostname = '127.0.0.1'
database = 'data'
user = 'postgres'
password = 'password'



####### EXTRACT & TRANSFORM ########
def pandas_transform():
    data = pd.read_csv('initial_data.csv')
    
    data['basket_items'] = data['basket_items'].str.split(',')
    data = (data.set_index(['timestamp','store','customer_name','total_price','cash_or_card','card_number'])['basket_items'].apply(pd.Series).stack().reset_index().drop('level_6',axis=1).rename(columns={0:'Product'}))
    data['Product'] = data['Product'].str.lstrip()
    data['Product'] = data['Product'].str.split('-')

    


    data['transactions_id'] = data.groupby(['timestamp']).ngroup()
    data['store_id'] = data.groupby(['store']).ngroup()
    data['customer_id'] =  data.groupby(['customer_name']).ngroup()
    data.rename(columns={'timestamp':'time_stamp','cash_or_card':'payment_type'},inplace=True)
    data = data[['transactions_id', 'time_stamp', 'store_id','store','customer_id', 'customer_name', 'total_price', 'payment_type','card_number','Product']]

    return data
def seperate():
    data = pandas_transform()
    item = []
    for record in data['Product']:
        item.append(record)
  
    Product = []
    Price = []
    for record in item:
        

        Product.append(record[:-1])
        Price.append(record[-1])
    data['item'] = Product
    data['price'] = Price

    
    


    return data
def seperate2():
    data = seperate()
    list = []
    for record in data['item']:
        if len(record) <2:
            record.append(" ")
        list.append(record)

    Flavour = []
    Item = []

    for record in list:
        flav = record[-1]
        Flavour.append(flav)
        ite = record[0]
        Item.append(ite)

    
    data['flavour'] = Flavour
    data['item'] = Item

    data.drop(['Product','card_number'], axis = 1, inplace = True) 

    return data
def create_ID():
    data = seperate2()
    
    data['item_id'] =  data.groupby(['item']).ngroup()
    #data = data[['Transactions_ID', 'timestamp', 'Store_ID','store','Customer_ID', 'customer_name', 'total_price', 'cash_or_card','Item_ID','Item','Price']]
    data['flavour_id'] =  data.groupby(['flavour']).ngroup()
    data = data[['transactions_id', 'time_stamp', 'store_id','store','customer_id', 'customer_name', 'total_price', 'payment_type','item_id','item','flavour_id','flavour','price']]

    return data

data = create_ID()
    
def create_database_psql(name):
    
   conn = psycopg2.connect(
      database="postgres", user='postgres', password='password', host='127.0.0.1', port= '5432'
   )
   conn.autocommit = True
   cursor = conn.cursor()

   cursor.execute(f'DROP DATABASE IF EXISTS {name}')
   cursor.execute(f'CREATE DATABASE {name}')

   print("Database created successfully........")

   conn.close()
def create_table():

    conn = psycopg2.connect(
    database="data", user='postgres', password='password', host='127.0.0.1', port= '5432'
   )
    conn.autocommit = True
    cursor = conn.cursor()

    
    

    
    cursor.execute(''' CREATE TABLE IF NOT EXISTS 
                       customers(
                     
                       customer_id INT NOT NULL,
                       customer_name varchar(255) NOT NULL,
                        PRIMARY KEY (customer_id),
                        UNIQUE (customer_name)
                        ) 
                      ''')
    
    print('Customers table has been created')

    cursor.execute(''' CREATE TABLE IF NOT EXISTS
                    
                    stores(

                    store_id INT NOT NULL,
                    store_name VARCHAR(255) NOT NULL,
                    PRIMARY KEY (store_id),
                    UNIQUE (store_name)
                    )
                    ''')
    print('Store tables successfully created')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS 
                 products(

                 product_id INT NOT NULL,
                 product_name VARCHAR(255) NOT NULL,
                 price NUMERIC(10,2) NOT NULL,
                 PRIMARY KEY (product_id),
                 UNIQUE (product_name)
               )
               ''') 
    print('Product table successfully created')
    
    
    cursor.execute(''' CREATE TABLE IF NOT EXISTS 
                  flavours(
                  
                  flavour_id INT NOT NULL ,
                  flavour VARCHAR(255) NOT NULL,
                  PRIMARY KEY (flavour_id),
                  UNIQUE (flavour)
                  )
                  ''')
    print('Flavours table successfully created')
    
    cursor.execute(''' CREATE TABLE IF NOT EXISTS 
                        Sales(
                        
                        transactions_id INT NOT NULL ,
                        time_stamp timestamp,
                        store_id INT NOT NULL REFERENCES stores (store_id),
                        customer_id INT REFERENCES customers (customer_id),
                        total_price FLOAT NOT NULL,
                        PRIMARY KEY (transactions_id)
                        
                        
                        ) 
                    ''')
    print('Sales table successfully created')

    cursor.execute(''' CREATE TABLE IF NOT EXISTS

                    Orders(

                     
                    order_id SERIAL,
                    product_id INT NOT NULL REFERENCES products (product_id),
                    flavour_id INT references flavours (flavour_id),
                    transactions_id INT references Sales (transactions_id),
                    PRIMARY KEY (order_id)
                    )
                    ''')
    print('Orders table successfully created')
    
    
def populate():

    

    transactions = data['transactions_id']
    timestamp = data['time_stamp']
    store_id = data['store_id']
    store = data['store']
    cust_id = data['customer_id']
    cust  = data['customer_name']
    total_price = data['total_price']
    p_t = data['payment_type']
    item_id = data['item_id']
    item = data['item']
    flav_id = data['flavour_id']
    flav = data['flavour']
    price = data['price']


   
    #
    


    engine = create_engine("postgresql+psycopg2://{user}:{password}@{host}/{db}"
                .format(host=hostname, db=database, user=user, password=password))
    
    #1) Populate customers table
    
    for id,name in zip(cust_id.unique(),cust.unique()):
       engine.execute(f" INSERT INTO customers (customer_id,customer_name) VALUES ('{id}','{name}') ON CONFLICT (customer_name) DO NOTHING")
    print(':)')
    
    #2) Populate Products table
    
    for id,name,price in zip(item_id.unique(),item.unique(),price):
         engine.execute(f" INSERT INTO products (product_id,product_name,price) VALUES ('{id}','{name}',{price}) ")
    print(':)')
    
    #3) Populate stores table

    for id,name in zip(store_id.unique(),store.unique()):
        engine.execute(f" INSERT INTO stores (store_id,store_name) VALUES ('{id}','{name}') ON CONFLICT (store_name) DO NOTHING")
    print(':)')
    
    #4) Populate flavours table
    
    for id,name in zip(flav_id.unique(),flav.unique()):
       engine.execute(f" INSERT INTO flavours (flavour_id,flavour) VALUES ('{id}','{name}') ON CONFLICT (flavour) DO NOTHING")

       print(':)')
    
    #5) Populate Sales table

    
    for ti,ts,si,ci,tp in zip(transactions.unique(),timestamp.unique(),store_id,cust_id.unique(),total_price):
        engine.execute(f" INSERT INTO sales (transactions_id,time_stamp,store_id,customer_id,total_price) VALUES ('{ti}','{ts}','{si}','{ci}','{tp}')")
    print(':)')
    #6) Populate Orders table

    for pi,fi,ti in zip(item_id,flav_id,transactions):
            engine.execute(f"INSERT INTO orders (product_id,flavour_id,transactions_id) VALUES ('{pi}','{fi}','{ti}')")
    print(':)')
      
print('ALL ABOARD!!!!!!!!!!!!!!!!!!!!!!!!!')
  

#create_table()
populate()





















