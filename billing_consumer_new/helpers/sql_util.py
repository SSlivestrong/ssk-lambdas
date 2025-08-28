
""" This module contains the class for connecting to MySQL Database and inserting data into it """

import aiomysql
from ascendops_commonlib.ops_utils import ops_config
from billing_consumer_new.helpers.app_logger import custom_logger as logger
from ascendops_commonlib.aws_utils.secrets_manager_util import SecretsManagerUtil
from billing_consumer_new.helpers import app_config

class aio_mysql:
    def __init__(self): 
        self.secret_json = SecretsManagerUtil().get_secret(secret_name=app_config.ANALYTICS_RDS_KEY_NAME)
        self.connection_pool = None

    async def connect(self, size=4):
        try:
            self.connection_pool = await aiomysql.create_pool(
                host=self.secret_json["host"],
                user=self.secret_json["username"],
                password=self.secret_json["password"],
                db=app_config.ANALYTICS_RDS_DATABASE_SCHEMA,
                port=self.secret_json["port"],
                maxsize=size,
                pool_recycle=10800
            )
            logger.log_message(
                message="Successfully connected to SQL Database",
                level="INFO"
            )
        except Exception as xcp:
            logger.log_message(
                message=f"Error in establishing connection to RDS: {str(xcp)}",
                level="ERROR"
            )

    async def bulk_insert_data(self, table_1: str, columns_1: tuple, data_1: list, table_2: str, columns_2: tuple, data_2: list):
        """
        Inserts data into 2 tables in RDS
        Args:
            table_1 (str): The name of the MySQL table to insert data into.
            columns_1 (tuple): A tuple of column names to insert data into.
            table_2 (str): The name of the MySQL table to insert data into.
            columns_2 (tuple): A tuple of column names to insert data into.     
        """    
        try:
            query_1 = f"INSERT INTO {table_1} ({', '.join(columns_1)}) VALUES ({', '.join(['%s' for _ in range(len(columns_1))])})"
            query_2 = f"INSERT INTO {table_2} ({', '.join(columns_2)}) VALUES ({', '.join(['%s' for _ in range(len(columns_2))])})"
            for _ in range(3):
                async with self.connection_pool.acquire() as connection:
                    async with connection.cursor() as cursor:
                        try:
                            await cursor.executemany(query_1, data_1)
                            logger.log_message(
                                message=f"Inserted records to {table_1}",
                                level="INFO"
                            )
                            await cursor.executemany(query_2, data_2)
                            logger.log_message(
                                message=f"Inserted records to {table_2}",
                                level="INFO"
                            )
                            await connection.commit()
                            logger.log_message(
                                message="Commited",
                                level="INFO"
                            )
                            break
                        except Exception as xcp:
                            await connection.rollback()
                            logger.log_message(
                                message=f"RDS writes using execute started: {str(xcp)}",
                                level="ERROR"
                            )
                            for record_1 in data_1:
                                try:
                                    await cursor.execute(query_1, record_1)
                                    await connection.commit()
                                except Exception as error:
                                    await connection.rollback()
                                    logger.log_message(
                                        message=f"Error in inserting the record to {app_config.ALLOUT_BILLING_TABLE_NAME}: {str(error)}",
                                        level="ERROR"
                                    )

                            for record_2 in data_2:
                                try:
                                    await cursor.execute(query_2, record_2)
                                    await connection.commit()
                                except Exception as error:
                                    await connection.rollback()
                                    logger.log_message(
                                        message=f"Error in inserting the record to {app_config.PRODUCT_CODES_BILLING_TABLE_NAME}: {str(error)}",
                                        level="ERROR"
                                    )
        except Exception as xcp:
            logger.log_message(
                message=f"Error acquiring connection to MySQL: {str(xcp)}",
                level="ERROR"
            )
