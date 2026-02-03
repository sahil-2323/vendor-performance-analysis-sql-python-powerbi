import sqlite3
import pandas as pd
import logging
from ingestion_db import ingest_db
logging.basicConfig(
    filename='logs/get_vendor_summary.log',
    level= logging.DEBUG,
    format= "%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

def create_vendor_summary(conn):
    """this function will merge the different tables to get the overall vendor summary nad adding new columns in the resultant data"""
    vendor_sales_summary = pd.read_sql_query(""" WITH FreightSummary AS(
    select 
        VendorNumber,
        sum(Freight) as FreightCost
    from vendor_invoice
    group by VendorNumber
    ),
    
    PurchaseSummary AS(
        select 
            p.VendorNumber,
            p.VendorName,
            p.Brand,
            p.Description,
            p.PurchasePrice,
            pp.Volume,
            pp.Price as ActualPrice,
            sum(p.Quantity) as TotalPurchaseQuantity,
            sum(p.Dollars) as TotalPurchaseDollars
        from purchases p
        join purchase_prices pp
            on p.Brand = pp.Brand
        where p.PurchasePrice > 0
        group by p.VendorNumber, p.VendorName, p.Brand, p.Description,p.PurchasePrice,pp.Price, pp.Volume
    ),
        
    SalesSummary AS(
        select 
            VendorNo,
            Brand,
            sum(SalesDollars) as TotalSalesDollars,
            sum(SalesPrice) as TotalSalesPrice,
            sum(SalesQuantity) as TotalSalesQuantity,
            sum(ExciseTax) as TotalExciseTax
        from sales
        group by VendorNo, Brand
    )
    
    SELECT
        ps.VendorNumber,
        ps.VendorName,
        ps.Brand,
        ps.Description,
        ps.PurchasePrice,
        ps.ActualPrice,
        ps.Volume,
        ps.TotalPurchaseQuantity,
        ps.TotalPurchaseDollars,
        ss.TotalSalesQuantity,
        ss.TotalSalesDollars,
        ss.TotalSalesPrice,
        ss.TotalExciseTax,
        fs.FreightCost
    FROM PurchaseSummary ps
    LEFT JOIN SalesSummary ss
        ON ps.VendorNumber = ss.VendorNo
        AND ps.Brand = ss.Brand
    LEFT JOIN FreightSummary fs
        ON ps.VendorNumber = fs.VendorNumber
    ORDER BY ps.TotalPurchaseDollars DESC""", conn)

    return vendor_sales_summary

def clean_data(df):
    """this function will clean the data"""
    # changing datatype to float
    vendor_sales_summary['Volume']= vendor_sales_summary['Volume'].astype('float64')

    # filling missing value with 0
    vendor_sales_summary.fillna(0, inplace= True)

    #removing spaces from categorical columns
    vendor_sales_summary['VendorName']= vendor_sales_summary['VendorName'].str.strip()
    vendor_sales_summary['Description']= vendor_sales_summary['Description'].str.strip()

    # creating new columns for better analysis
    vendor_sales_summary['GrossProfit']= vendor_sales_summary['TotalSalesDollars'] - vendor_sales_summary['TotalPurchaseDollars']
    vendor_sales_summary['ProfitMargin']= (vendor_sales_summary['GrossProfit']/ vendor_sales_summary['TotalSalesDollars'])*100
    vendor_sales_summary['StockTurnover']= vendor_sales_summary['TotalSalesQuantity']/vendor_sales_summary['TotalPurchaseQuantity']
    vendor_sales_summary['SalesToPurchaseRatio']= vendor_sales_summary['TotalSalesDollars']/vendor_sales_summary['TotalPurchaseDollars']
    return df

if __name__=='__main__':
    # creating database connection
    conn= sqlite3.connect('inventory.db')

    logging.info('Creating Vendor Summary Table....')
    summary_df = create_vendor_summary(conn)
    logging.info(summary_df.head())

    logging.info('Cleaning Data......')
    clean_df= clean_data(summary_df)
    logging.info(clean_df.head())

    logging.info('Ingesting Data........')
    ingest_db(clean_df, 'vendor_sales_summary', conn)
    logging.info('Completed')