import pandas as pd
from sqlalchemy.dialects.mssql import (
    BIGINT,
    DATETIME2,
    SMALLDATETIME,
    UNIQUEIDENTIFIER,
)
from sqlalchemy.types import (
    CHAR,
    DECIMAL,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    SmallInteger
)

class DataUtils():
    def __init__(self, engine, org):
        self.engine = engine
        self.org = org

    def preprocess_df(self, db: str, schema: str, table_name: str, raw_df: pd.DataFrame) -> pd.DataFrame:
        try:
            sql_df = pd.read_sql(f"SELECT TOP 1 * FROM {db}.{schema}.{table_name}", con=self.engine.engine) # Retrieve a 1 row result set as template for table
            raw_df = raw_df[sql_df.columns.to_list()] #drop columns from raw_df that are not in list of columns from sql_df
            dtypes = self.get_table_dtypes(db, schema, table_name) #gets sqlalchemy dtypes and matches them to columns in raw df for use in next function
            cleaned_df = self.convert_dtypes(raw_df, dtypes) #converts all columns in raw_df to sqlalchemy dtypes
            return cleaned_df
        except Exception as e:
            print(f"unable to convert df {str(e)}")

    def get_table_dtypes(self, db: str, db_schema: str, table_name: str) -> dict:
        try:
            df = pd.read_sql(f"exec {db}.dbo.spGet_TableSchema {db_schema}, {table_name}", con=self.engine.engine)
            table_dtypes = {} #stores sqlalchemy dtypes with column names in dictionary

            for row in df.itertuples(index=False):
                match row.DATA_TYPE: 
                    case "int":
                        table_dtypes.update({row.COLUMN_NAME: Integer()})
                    case "bit":
                        table_dtypes.update({row.COLUMN_NAME: Boolean()})
                    case "bigint":
                        table_dtypes.update({row.COLUMN_NAME: BIGINT()})
                    case "date":
                        table_dtypes.update({row.COLUMN_NAME: Date()})
                    case "float":
                        table_dtypes.update({row.COLUMN_NAME: Float()})
                    case "decimal":
                        table_dtypes.update({row.COLUMN_NAME: DECIMAL()})
                    case "datetime":
                        table_dtypes.update({row.COLUMN_NAME: DateTime()})
                    case "datetime2":
                        table_dtypes.update({row.COLUMN_NAME: DATETIME2()})
                    case "smalldatetime":
                        table_dtypes.update({row.COLUMN_NAME: SMALLDATETIME()})
                    case "char":
                        table_dtypes.update({row.COLUMN_NAME: CHAR()})
                    case "text":
                        table_dtypes.update({row.COLUMN_NAME: String()})
                    case "varchar":
                        table_dtypes.update({row.COLUMN_NAME: String()})
                    case "uniqueidentifier":
                        table_dtypes.update({row.COLUMN_NAME: UNIQUEIDENTIFIER()})
            del df
            return table_dtypes
        except Exception as e:
            print(f"unable to get table column types {str(e)}")
    
    def convert_dtypes(self, df, dtypes):
        try:
            for c in dtypes:
                if type(dtypes[c]) in [
                    type(Integer()),
                    type(Float()),
                    type(BigInteger()),
                    type(DECIMAL()),
                    type(BIGINT()),
                    type(SmallInteger())
                ]:
                    df.loc[:, c] = pd.to_numeric(df.loc[:, c])
                elif type(dtypes[c]) in [
                    type(Date()),
                    type(DateTime()),
                    type(DATETIME2()),
                    type(SMALLDATETIME()),
                ]:
                    df.loc[:, c] = pd.to_datetime(df.loc[:, c], errors="coerce")
                elif type(dtypes[c]) in [type(UNIQUEIDENTIFIER())]:
                    # NOOP
                    pass
                elif type(dtypes[c] in [type(String())]):
                    col_length = max(df.loc[:, c].astype(str).apply(len))
                    if dtypes[c].length is None and col_length < 8000:
                        dtypes[c] = String(col_length)
                        print(
                            "Updated column {} from String() to String({})".format(c, col_length)
                        ) 
            return df          
        except Exception as e:
            print(f"unable to convert column types {str(e)}")

    def get_table_schema_from_db(self, db: str, schema: str, table_name: str) -> pd.DataFrame:
        raise NotImplementedError
        # Implement later when Nick Ts db mapping is complete
        # should be able to pull out data types and column names using only a table name as a reference
        # org is already available in the class object so no need to pass it in as a parameter

    def handle_nullable_ints(self, df: pd.DataFrame) -> pd.DataFrame:
        #todo: fix this it does not work currently
        # for col in df.columns.to_list():
        #     if df[col].dtype == 'int64':
        #         df[col] = df[col].astype('Int64')
        # return df.replace(r'^\s*$', np.nan, regex=True)
        raise NotImplementedError

    #at this point all column values should be the same, this only handles converting types
    def convert_df_types(self, sql_df, base_df) -> pd.DataFrame:
        #todo: this kind of works, the problem is getting a base_df that you can trust as a reference
        # additionally since this only converts pandas dtypes you will run into issues with null values in int64/float columns
        #for now this task is on the shelf, but we can revisit it later if we want
        try:
            base_copy = base_df.copy() #need copy due to reference
            for col in sql_df.columns: #https://stackoverflow.com/questions/48348176/convert-data-types-of-a-pandas-dataframe-to-match-another 
                base_copy[col]=base_copy[col].astype(sql_df[col].dtypes.name)
            return base_copy
        except Exception as e:
            print(f"unable to convert df types: {str(e)}")