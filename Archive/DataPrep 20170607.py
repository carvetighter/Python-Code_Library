###############################################################################################
###############################################################################################
#
# This import file <DataPrep.py> contains methods to retrieve, clean, slice, sort and convert data in preperation for
# clusttering, classifying, evaluating and visualizing
#
# Requirements:
# package pandas
# package numpy
# package time
# package sklearn.feature_extraction.text
# file SqlMethods.py
#
# Methods included:
# GetData()
#	- retrieves data from a sql database and returns a dataframe
#
# CleanData()
#	- specific method to clean data for the CPBB model and returns a dataframe
#
# SliceData()
#	- specific method to slice data based on a list passed
#
# ConvertToTFIDF()
#	- trade a TFIDF matrix based on a dataframe passed, this is for a specfic column
#	- retunrs a list of different dense matrix, sparse matrix, dataframe
#
# ConvertToTFIDFSeries()
# - take a pandas data series and convert to TFIDF matrix
#
# SortDict()
#	- sorts a dictionary and returns a list, required for ConvertToTFIDF()
#
# NoSpaces()
#	- removes the spaces on the left and right of the string and any spaces that are more than one
#	- within the string
#
# Important Info:
# package pymssql will be imported with the file SqlMethods.py
###############################################################################################
###############################################################################################

# package import
from SqlMethods import SqlGenSelectStatement
import pandas, numpy, time, string
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

def GetData(m_sql_connection, m_select, m_str_from, m_str_where):
    ###############################################################################################
    ###############################################################################################
    #
    # this method gets the data from an instance of SQL Server on server GILDV319
    #
    # Requirements:
    # package pandas
	# package pymssql
	# package time
    #
    # Inputs:
    # m_sql_connection
    # Type: pymssql connection object
    # Desc: this is the connection to the sql server
    #  
    # m_sql_query
    # Type: string
    # Desc: sql query statement
    #  
    # Important Info:
    # None
    #
    # Return:
    # object
    # Type: pandas.DataFrame object
    # Desc: the raw data from the test set of data
    ###############################################################################################
    ###############################################################################################

	# connection info to the database
	string_query = SqlGenSelectStatement(m_str_select = m_select, m_str_from = m_str_from, m_str_where = m_str_where)

	# query the database
	time_qry_start = time.perf_counter()
	dataframeRaw = pandas.DataFrame(pandas.read_sql(string_query, m_sql_connection))
	time_qry = time.perf_counter() - time_qry_start

	# print query information
	print('Record count:', dataframeRaw['str_OrderNumber'].count())
	print('Query time (HH:MM:SS):', time.strftime('%H:%M:%S', time.gmtime(time_qry)))

	# return data frame
	return dataframeRaw

def CleanData(dataframeData):
    ################################################################################################
    ###############################################################################################
    #
    # this method cleans the data in the dataframe passed; looking in the columns identified to [str_ItemDescription] and the 
	# [str_NounCodeDescription] with spaces and numpy.nan types; this is broken up into two sub-methods to look at the 
	# numpy.nan potential values and the spaces
    #
    # Requirements:
    # package numpy
	# package pandas
	# method NoSpaces()
    #
    # Inputs:
    # dataframeData
	# type: pandas.DataFrame
	# desc: the dataframe which is the raw data from the database
    #  
    # Important Info:
    # None
    #
    # Return:
    # object
    # Type: pandas.DataFrame object
    # Desc: the clean data based on the cleaning criterea
    ###############################################################################################
    ###############################################################################################
	# start time
	time_clean_start = time.perf_counter()

	# lists
	list_columns_comma = ['str_ItemDescription']
	list_nan_space = [numpy.nan, 'nan', ',', ';']
	list_phrases_delete = ['Unassigned', 'Miscellaneous', 'Other', 'Others', 'MISCELLANEOUS', 'UNASSIGNED']
	list_date_columns = ['date_CreationDate']
	list_string_data = list()
	
	# convert data from dataframe to array
	list_data = [tuple(x) for x in dataframeData.values]

	# replace spaces inside each element of data
	# replaces multiple spaces with only one space
	for i in range(0, len(list_data)):
		list_string_data.append(tuple(NoSpaces(str(j)) for j in list_data[i]))

	# create new data frame
	dataframe_new = pandas.DataFrame(data = list_string_data, columns = dataframeData.columns)

	# replace commas with spaces, replace empty cells with a space, replace numpy.nan with space
	for col in list_columns_comma:
		# phrases to replace with a space
		for k in list_nan_space:
			dataframe_new[col] = dataframe_new[col].str.replace(str(k), ' ')

		# phrases to delete, replace with empty string, ''
		for k in list_phrases_delete:
			dataframe_new[col] = dataframe_new[col].str.replace(k, '')

		# take out the spaces at the ends of the segement
		dataframe_new[col] = dataframe_new[col].str.strip()

	 # ensure that the [str_ItemDescription] has something in it and is not null
	dataframe_new = dataframe_new[dataframe_new.str_ItemDescription.notnull()]

	# convert the dates to a date data type
	for col in list_date_columns:
		dataframe_new[col] = pandas.to_datetime(dataframe_new[col])

	# stop time
	time_clean_duration = time.perf_counter() - time_clean_start

	# print time information
	print('Record count:', dataframe_new['str_OrderNumber'].count())
	print('Clean time (HH:MM:SS):', time.strftime('%H:%M:%S', time.gmtime(time_clean_duration)))

	# the dataframe returned, clean data
	return dataframe_new

def SliceData(dataframeData, list_slice_criterea):
    ################################################################################################
    ###############################################################################################
    #
    # the method will slice the data to be seperate the 'Miscellaneous', 'Uassigned', 'Others'
    #
    # Requirements:
	# package pandas
    #
    # Inputs:
    # dataframeData
	# type: pandas.DataFrame
	# desc: the dataframe which is the clean data from the database
    #  
    # list_slice_criterea
	# type: list object
	# desc: the list of phrases or criterea to create a new dataframe
    #  
    # Important Info:
    # a new column is created in the data frame [str_ClassColumn01] which is the combination of the columns
	# [str_ItemDescription]
    #
    # Return:
    # object
    # Type: pandas.DataFrame object
    # Desc: the records which have the the unassigned values
    ###############################################################################################
    ###############################################################################################

	# start time
	time_slice_start = time.perf_counter()

	# for intellisense in visual studio
	dataframeData = pandas.DataFrame(dataframeData)

	# get the data frame to run the cluster algorithm on
	dataframe_cluster = pandas.DataFrame(dataframeData.loc[dataframeData['str_ItemCategory'].isin(list_slice_criterea)])

	# create new column to cluster on which combines columns [str_ItemDescription] & [str_NounCodeDescription]
	dataframe_cluster['str_ClassColumn01'] = dataframe_cluster['str_ItemDescription']

	# strip spaces off the end
	dataframe_cluster['str_ClassColumn01']  = dataframe_cluster['str_ClassColumn01'] .str.strip()

	# ensure [str_ClassColumn01] is not null
	dataframe_cluster = dataframe_cluster[dataframe_cluster.str_ClassColumn01.notnull()]

	# duration time
	time_slice_duration = time.perf_counter() - time_slice_start
	print('Record count:', dataframe_cluster['str_OrderNumber'].count())
	print('Slice time (HH:MM:SS):', time.strftime('%H:%M:%S', time.gmtime(time_slice_duration)))

	# return dataframe
	return dataframe_cluster

def ConvertToTFIDF(dataframeData):
	################################################################################################
    ###############################################################################################
    #
    # the method will take the column [str_ClassColumn01] from the dataframe and create a TFIDF matrix to cluster on
    #
    # Requirements:
	# package sklearn.feature_extranction.text
	# package pandas
	# method SortDict()
    #
    # Inputs:
    # dataframeData
	# type: pandas.DataFrame
	# desc: the dataframe which is the clean data
    #  
    # Important Info:
    # None
    #
    # Return:
    # object
    # Type: list
    # Desc: the list contains three objects:
	# list[0] -> sparse matrix of the TFIDF matrix
	# list[1] -> dense matrix of the TFIDF matrix
	# list[2] -> dataframe of the TFIDF matrix
    ###############################################################################################
    ###############################################################################################

	# start time
	time_tfidf_start = time.perf_counter()

	# for visual studio for method and type checking
	dataframeData = pandas.DataFrame(dataframeData)

	# lists
	list_return = list()
	
	# create the count vector matix from the works in [str_ClassColumn01]
	cnt_vect = CountVectorizer(min_df = 1)
	class_col_cnt_vect = cnt_vect.fit_transform(dataframeData['str_ClassColumn01'])
	
	# create the TFIDF matrix
	tfidf_trans = TfidfTransformer(smooth_idf = False)
	tfidf_sparse = tfidf_trans.fit_transform(class_col_cnt_vect)

	# create dense TFIDF matrix
	tfidf_dense = tfidf_sparse.todense()

	# get columns for the dataframe
	list_sorted_v = SortDict(cnt_vect.vocabulary_ , 1)
	list_columns_v = [i[0] for i in list_sorted_v]

	# create data frame
	dataframe_tfidf = pandas.DataFrame(data = tfidf_dense, columns = list_columns_v)
	
	# create return list
	list_return.append(tfidf_sparse)
	list_return.append(tfidf_dense)
	list_return.append(dataframe_tfidf)

	# time duration
	time_tfidf_duration = time.perf_counter() - time_tfidf_start
	print('TFIDF time (HH:MM:SS):', time.strftime('%H:%M:%S', time.gmtime(time_tfidf_duration)))

	# return list
	return list_return

def ConvertToTFIDFSeries(m_pandas_series):
	################################################################################################
    ###############################################################################################
    #
    # the method will take a pandas series 
    #
    # Requirements:
	# package sklearn.feature_extranction.text
	# package pandas
	# package time
	# method SortDict()
    #
    # Inputs:
    # dataframeData
	# type: pandas.DataFrame
	# desc: the dataframe which is the clean data
    #  
    # Important Info:
    # None
    #
    # Return:
    # object
    # Type: list
    # Desc: the list contains three objects:
	# list[0] -> sparse matrix of the TFIDF matrix
	# list[1] -> dense matrix of the TFIDF matrix
	# list[2] -> dataframe of the TFIDF matrix
    ###############################################################################################
    ###############################################################################################

	# start time
	time_tfidf_start = time.perf_counter()

	# for visual studio for method and type checking
	m_pandas_series = pandas.Series(m_pandas_series)

	# lists
	list_return = list()
	
	# create the count vector matix from the pandas series
	cnt_vect = CountVectorizer(min_df = 1)
	class_col_cnt_vect = cnt_vect.fit_transform(m_pandas_series)
	
	# create the TFIDF matrix
	tfidf_trans = TfidfTransformer(smooth_idf = False)
	tfidf_sparse = tfidf_trans.fit_transform(class_col_cnt_vect)

	# create dense TFIDF matrix
	tfidf_dense = tfidf_sparse.todense()

	# get columns for the dataframe
	list_sorted_v = SortDict(cnt_vect.vocabulary_ , 1)
	list_columns_v = [i[0] for i in list_sorted_v]

	# create data frame
	dataframe_tfidf = pandas.DataFrame(data = tfidf_dense, columns = list_columns_v) 
	
	# create return list
	list_return.append(tfidf_sparse)
	list_return.append(tfidf_dense)
	list_return.append(dataframe_tfidf)

	# time duration
	time_tfidf_duration = time.perf_counter() - time_tfidf_start
	print('TFIDF time (HH:MM:SS):', time.strftime('%H:%M:%S', time.gmtime(time_tfidf_duration)))

	# return list
	return list_return

def SortDict(dict_org, int_index = 0, bool_descending = False):
    ###############################################################################################
    ###############################################################################################
    #
    # this method sorts a dictionary ascending or descending and returns a list of tuples
    #
    # Requirements:
    # None
    #
    # Inputs:
    # dict_org
    # Type: dictionary
    # Desc: the dictionary to be sorted
    #
    # int_index
    # Type: integer
    # Desc: the index of the dictionary to sort; 0 will sort by the keys, 1 will sort by the values
    # 
    # bool_return_list
    # Type: boolean
    # Desc: flag flag to return list or dictionary, default is dictionary
    #    
    # Important Info:
    # None
    #
    # Return:
    # object
    # Type: list
    # Desc: list is returned a list of tuples is returned
    ###############################################################################################
    ###############################################################################################
    
    # create a sorted list from the dictionary
    list_sorted = sorted(dict_org.items(), key = lambda x: x[int_index], reverse = bool_descending)
       
    return list_sorted

def NoSpaceString(string_org):
    ###############################################################################################
    ###############################################################################################
    #
    # this subroutine takes a string and removes the spaces on the outside of the string (left and right) and any spaces
    # in the string that are more than one; returns the new string
    #
    # Requirements:
    # None
    #
    # Inputs:
    # string_org
    # Type: string
    # Desc: the string to take out the spaces
    #
    # Important Info:
    # None
    #
    # Return:
    # variable
    # Type: string
    # Desc: the new string with no spaces inside and outside
    ###############################################################################################
    ###############################################################################################

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# variable / object declarations
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#
	# Start
	#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#				

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# strip and split values in series
	#------------------------------------------------------------------------------------------------------------------------------------------------------#			
	
	string_org = string_org.strip()
	list_new = string_org.split(' ')

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# return value
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	# if the item in the list is more than length zero join with a space
	return ''.join(x for x in list_new if x)

def NoSpaceSeries(m_pandas_series):
    ###############################################################################################
    ###############################################################################################
    #
    # this subroutine takes a pandas series and removes the spaces on the outside of the string (left and right) and 
	# any spaces in the string that are more than one; returns the new string
    #
    # Requirements:
    # package pandas
    #
    # Inputs:
    # m_pandas_series
    # Type: pandas series
    # Desc: the pandas series which holds the data
    #
    # Important Info:
    # None
    #
    # Return:
    # object
    # Type: pandas series
    # Desc: the new pandas series in which there are no spaces
    ###############################################################################################
    ###############################################################################################

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# variable / object declarations
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	# type casting for visual studio
	m_pandas_series = pandas.Series(m_pandas_series)

	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#
	# Start
	#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#				

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# strip and split values in series
	#------------------------------------------------------------------------------------------------------------------------------------------------------#			
	
	m_pandas_series = m_pandas_series.str.strip()
	m_pandas_series = m_pandas_series.str.split(' ')

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# replacing all the symbols with a space
	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	
	for int_index in range(0, len(m_pandas_series)):
		string_new = str()
		list_value = m_pandas_series[int_index]
		string_new = ''.join(x for x in list_value if x)
		string_new.strip()
		m_pandas_series.loc[int_index] = string_new

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# return value
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	return m_pandas_series

def OneSpaceString(string_org):
    ###############################################################################################
    ###############################################################################################
    #
    # this subroutine takes a string and removes the spaces on the outside of the string (left and right) and any spaces
    # in the string that are more than one; returns the new string
    #
    # Requirements:
    # None
    #
    # Inputs:
    # string_org
    # Type: string
    # Desc: the string to take out the spaces
    #
    # Important Info:
    # None
    #
    # Return:
    # variable
    # Type: string
    # Desc: the new string with no spaces inside and outside
    ###############################################################################################
    ###############################################################################################

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# variable / object declarations
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#
	# Start
	#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#				

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# strip and split values in series
	#------------------------------------------------------------------------------------------------------------------------------------------------------#			
	
	string_org = string_org.strip()
	list_new = string_org.split(' ')

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# return value
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	# if the item in the list is more than length zero join with a space
	return ''.join(item + ' ' for item in list_new if item)

def OneSpaceSeries(m_pandas_series):
    ###############################################################################################
    ###############################################################################################
    #
    # this subroutine takes a pandas series and removes the spaces on the outside of the string (left and right) and 
	# any spaces in the string that are more than one; returns the new string
    #
    # Requirements:
    # package pandas
    #
    # Inputs:
    # m_pandas_series
    # Type: pandas series
    # Desc: the pandas series which holds the data
    #
    # Important Info:
    # None
    #
    # Return:
    # object
    # Type: pandas series
    # Desc: the new pandas series with only one space bwteen phrases
    ###############################################################################################
    ###############################################################################################

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# variable / object declarations
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	# type casting for visual studio
	m_pandas_series = pandas.Series(m_pandas_series)

	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#
	# Start
	#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#				

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# strip and split values in series
	#------------------------------------------------------------------------------------------------------------------------------------------------------#			
	
	m_pandas_series = m_pandas_series.str.strip()
	m_pandas_series = m_pandas_series.str.split(' ')

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# replacing all the symbols with a space
	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	
	for int_index in range(0, len(m_pandas_series)):
		string_new = str()
		list_value = m_pandas_series[int_index]
		try:
			string_new = ''.join(str(x) + ' ' for x in list_value if x)
		except Exception as e:
			string_error = str(e.args)
			pass
		else:
			pass
		finally:
			pass
		string_new.strip()
		m_pandas_series.loc[int_index] = string_new

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# return value
	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	m_pandas_series = m_pandas_series.str.strip()
	return m_pandas_series

def NoSymbols(m_pandas_series, bool_remove = False, m_list_symbols = []):
    ###############################################################################################
    ###############################################################################################
	#
    # this method cleans the data in a pandas series passed; it replaces most of the standard symbols with a space and
	# na or nan values with a space
    #
    # Requirements:
    # package pandas
    #
    # Inputs:
    # m_pandas_series
    # Type: pandas series
    # Desc: the data to clean
	#
	# bool_remove
    # Type: boolean
    # Desc: flag for the m_list_symbols, if true and the list is not empty remove the symbols in the list from the list of
	# symbols to remove from each element of the series; if false do nothing
	#
    # m_list_symbols
    # Type: list
    # Desc: only use these symbols in the list, if empty do not use
	#
    # Important Info:
    # None
    #
    # Return:
    # object
    # Type: pandas series
    # Desc: the clean data of the data series
    ###############################################################################################
    ###############################################################################################	

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# package import
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# variable / object declarations
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	# type casting for visual studio
	m_pandas_series = pandas.Series(m_pandas_series)

	# lists
	list_symbols = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '-', '+', '=', '~', '`', '{', '[', '}', ']', '|', ':', ';', '"', "'", '<', ',', '.', '>', '?', '/',
				 '\r', '\n']

	# variables

	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#
	# Start
	#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#				

	# ensure all elements of series is a string
	for int_index in range(0, len(m_pandas_series)):
		if type(m_pandas_series.loc[int_index]) != str:
			m_pandas_series.loc[int_index] = str(m_pandas_series.loc[int_index])

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# replacing all the symbols with a space
	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	
	if bool_remove == False and len(m_list_symbols) > 0:
		for symbol in m_list_symbols:
			m_pandas_series = m_pandas_series.str.replace(symbol, ' ')	
	elif bool_remove == False and len(m_list_symbols) == 0:
		for symbol in list_symbols:
			m_pandas_series = m_pandas_series.str.replace(symbol, ' ')	
	elif bool_remove == True:
		list_remove = [x for x in list_symbols if x not in m_list_symbols]
		for symbol in list_remove:
			m_pands_series = m_pandas_series.str.replace(symbol, ' ')
	else:
		pass

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# return value
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	m_pandas_series = m_pandas_series.str.strip()
	return m_pandas_series		

def NanToUnknown(m_pandas_series, bool_string = False):
    ###############################################################################################
    ###############################################################################################
	#
    # this method replaces all the nan values (which is a float in python / numpy)
    #
    # Requirements:
    # package pandas
    #
    # Inputs:
    # m_pandas_series
    # Type: pandas series
    # Desc: the data to clean
	#
    # bool_string
    # Type: boolean
    # Desc: flag to test series as a string or a float
	#
    # Important Info:
    # None
    #
    # Return:
    # object
    # Type: pandas series
    # Desc: the dataframe where each nan value is converted to a string 'Unknown'
    ###############################################################################################
    ###############################################################################################	

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# package import
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# variable / object declarations
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	# type casting for visual studio
	m_pandas_series = pandas.Series(m_pandas_series)

	# variables

	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#
	# Start
	#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#				

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# replacing na / nan values with space
	#------------------------------------------------------------------------------------------------------------------------------------------------------#			
	
	if m_pandas_series.hasnans == True and bool_string == False:
		series_nan = m_pandas_series.isnull()
		m_pandas_series.loc[series_nan.values] = 'Unknown'

	if bool_string == True:
		m_pandas_series.loc[m_pandas_series == 'nan'] = 'Unknown'

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# return value
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	return m_pandas_series		

def TakeOutNumbers(m_pandas_series):
    ###############################################################################################
    ###############################################################################################
	#
    # this method takes out the phrases that are only numbers in the elements of the pandas series
    #
    # Requirements:
    # package pandas
    #
    # Inputs:
    # m_pandas_series
    # Type: pandas series
    # Desc: the data to clean
	#
    # m_string_name
    # Type: string
    # Desc: the name for the series
	#
    # Important Info:
    # None
    #
    # Return:
    # object
    # Type: pandas series
    # Desc: the clean data of the data series
    ###############################################################################################
    ###############################################################################################	

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# variable / object declarations
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	# type casting for visual studio
	m_pandas_series = pandas.Series(m_pandas_series)

	# lists
	list_address_clean_no_numbers = list()
	list_value_nans = list()

	# variables

	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#
	# Start
	#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
	#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#				

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# replacing all the phrases with only numbers
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	# strip & split on space to create list of phrases
	m_pandas_series = m_pandas_series.str.strip()
	m_pandas_series = m_pandas_series.str.split(' ')

	# loop through addresses
	for int_index in range(0, len(m_pandas_series)):
		# the list of values
		list_values = list(m_pandas_series[int_index])

		# for each value if it is only a digit than take it out
		string_new = str()
		for string_value in list_values:
			for char_c in string_value:
				if char_c not in string.digits:
					string_new += char_c
			string_new += ' '
		
		string_new = string_new.strip()
		if len(string_new) == 0:
			string_new = 'Unknown'

		# replace value in series
		m_pandas_series.loc[int_index] = string_new

	#------------------------------------------------------------------------------------------------------------------------------------------------------#
	# return value
	#------------------------------------------------------------------------------------------------------------------------------------------------------#

	m_pandas_series = m_pandas_series.str.strip()
	return m_pandas_series