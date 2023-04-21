from zeno.classes.base import MetadataType, ZenoColumn, ZenoColumnType
from sliceline.slicefinder import Slicefinder
import pandas as pd
import numpy as np
import secrets
from zeno.classes.slice import FilterPredicate, FilterPredicateGroup, Slice
from pandas.api.types import is_numeric_dtype

"""
Finds the right column given the df and zenocolumn.
"""
def find_the_right_column(columns, name):
    for i in range(0, len(columns)):
        if(columns[i].__str__() == name):
            return columns[i]
    return 

def find_the_right_column_name(columns, name):
    for i in range(0, len(columns)):
        if(columns[i].name == name):
            return columns[i].__str__()
    return 



def get_column_name_with_summary(df, columns):
    column_summary_dict = dict()
    updated_df = data_clean_for_columns(df)
    all_df_column_name = updated_df.columns.values
    for column in columns:
        for df_column_name in all_df_column_name:
            if(column.__str__() == df_column_name):
                if(is_numeric_dtype(df[df_column_name])):
                    column_summary_dict[column.name] = [(str)(df[df_column_name].min()),  (str)(df[df_column_name].max())]
                else: 
                    column_summary_dict[column.name] = df[df_column_name].unique().tolist()
    return column_summary_dict
    
def data_clean_for_columns(df):
    # data cleaning
    updated_df = df.copy(deep=True)
    # updated_df = updated_df.reset_index(drop=True)
    updated_df.drop(list(df.filter(regex = 'id')), axis = 1, inplace = True)
    # updated_df.drop(list(df.filter(regex = 'label')), axis = 1, inplace = True)
    updated_df.drop(list(df.filter(regex = 'EMBEDDING')), axis = 1, inplace = True)
    updated_df.drop(list(df.filter(regex = 'POSTDISTILL')), axis = 1, inplace = True)
    updated_df.drop(list(df.filter(regex = 'OUTPUT')), axis = 1, inplace = True)    
    return updated_df



def slice_finder(df, req, zeno_options, metric_functions, columns):
    # setting up config important for the next steps
    minimum_size = int(req.minimumSize)
    #print(df.dtypes)
    #print(columns)
    #print(get_column_name_with_summary(df, columns))
    
    output_col = ZenoColumn(
        column_type=ZenoColumnType.OUTPUT,
        name=req.model,
    )
    output_hash = str(output_col)

    distill_fns = [
        c
        for c in columns
        if (
            c.column_type == ZenoColumnType.PREDISTILL
            or c.column_type == ZenoColumnType.POSTDISTILL
        )
        and c.model == req.model
    ]

    local_ops = zeno_options.copy(
        update={
            "output_column": output_hash,
            "distill_columns": dict(
                zip([c.name for c in distill_fns], [str(c) for c in distill_fns])
            ),
        }
    )

    print(local_ops)

    # data cleaning

    print(req.columnName)
    updated_df = df.copy(deep=True)


    """
    df[column]
    df[str(my_column)].to_list()
    """
    # stick with accuracy as for now. Andy, Apr 13th

    df_column_name = find_the_right_column_name(columns, req.columnName)
    updated_df = data_clean_for_columns(updated_df)

    print(updated_df.columns.values)
    print(updated_df)
    print(df_column_name)
    result = metric_functions["slice_finder_accuracy"](df, local_ops)
    all_categorical_data = updated_df.select_dtypes(include=["object", "boolean", "string"]).columns.tolist()

    filtered_all_categorical_data = []
    
    for i in range(0, len(all_categorical_data)):
        data_name = all_categorical_data[i]
        if("EMBEDDING" in data_name): 
            continue
        if("POSTDISTILL" not in data_name):
            filtered_all_categorical_data.append(data_name)

    all_categorical_data = filtered_all_categorical_data

    code_dict = dict()

    # print(list(set(updated_df["label"].values.tolist())))
    
    for row_name in all_categorical_data:
        # print(row_name)
        # print(updated_df[row_name].values.tolist())
        target_list = updated_df[row_name].tolist()
        name_list = list(set(target_list))
            
        codes, uniques = updated_df[row_name].factorize(name_list)
        code_dict[row_name] = uniques
        updated_df[row_name] = codes #pd.Categorical(updated_df[row_name]).codes

    # df_trans = pd.DataFrame(clf[0].transform(X), columns=clf[0].get_feature_names_out())

    # stick with accuracy as for now. Andy, Apr 13th
    # result = metric_functions["accuracy"](updated_df, local_ops)


    # load the correct error rate.
    print(result)
    errors = result.distill_output

    # updated_df = updated_df[all_categorical_data]

    # slice finder code logic

    slice_finder = Slicefinder(alpha=0.99, k=minimum_size, max_l=(int)(req.depth))
    slice_finder.fit(updated_df, errors)

    # print(slice_finder.top_slices_)

    # print(slice_finder.average_error_)

    """
    slice_name: str
    folder: str
    filter_predicates: FilterPredicateGroup
    """

    # construct the top_slices_ into real slice objects

    all_data_column = updated_df.columns.tolist()

    slices_of_interest = []
    for slice_name in slice_finder.top_slices_:
        slice_name_result = "slicefinder-result-"
        predicate_list = []
        for i in range(0, len(slice_name)):
            slice_predicate_half = slice_name[i]
            if(slice_predicate_half is not None):
                if(all_data_column[i] in code_dict):
                    slice_predicate_half = code_dict[all_data_column[i]][(int)(slice_predicate_half)]
                zeno_column = find_the_right_column(columns, all_data_column[i])
                join_val = "" if len(predicate_list) == 0 else "&"
                predicate_list.append(FilterPredicate(column=zeno_column, operation="==", value=slice_predicate_half, join=join_val))
                slice_name_result = slice_name_result + (str)(slice_predicate_half) + "-"
        slice_name_result = slice_name_result + (str)(secrets.token_hex(3))
        
        slices_of_interest.append(Slice(slice_name=slice_name_result, folder="",
                                        filter_predicates=
                                        FilterPredicateGroup(predicates=predicate_list, join="")))

    # print(type(result))
    # print(slices_of_interest[0])

    return {"metric": slice_finder.average_error_, "list_of_trained_elements": all_data_column,
            "slices_of_interest": slices_of_interest}
