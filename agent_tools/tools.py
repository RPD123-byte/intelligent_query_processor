from pydantic import BaseModel, field_validator, ValidationError, ValidationInfo
from typing import List, Optional, Dict, Any
from fuzzywuzzy import process
import pandas as pd
import pickle
import json


def load_collection_data_frames(filename='collection_data_frames.pkl'):
    with open(filename, 'rb') as file:
        data_frames = pickle.load(file)
    return data_frames

collection_data_frames = load_collection_data_frames()



class SearchCriteria(BaseModel):
    collection: str
    key: Optional[str] = None
    value: Optional[str] = None
    columns: List[str] = []

    @field_validator('collection')
    def validate_collection(cls, v: str, info: ValidationInfo):
        allowed_collections = list(collection_data_frames.keys())
        if v not in allowed_collections:
            suggestions = cls.get_suggestions(v, allowed_collections)
            if suggestions:
                suggestion_str = " or ".join(f"'{s}'" for s in suggestions)
                raise ValueError(f"Invalid collection '{v}'. Did you mean {suggestion_str}?")
            else:
                raise ValueError(f"Invalid collection '{v}'. No similar collections found.")
        return v


    @field_validator('key')
    def validate_key(cls, v: str, info: ValidationInfo):
        collection = info.data.get('collection')
        allowed_keys = list(collection_data_frames[collection].columns)
        if v and v not in allowed_keys:
            suggestions = cls.get_suggestions(v, allowed_keys)
            if suggestions:
                suggestion_str = " or ".join(f"'{s}'" for s in suggestions)
                raise ValueError(f"Invalid key for collection '{collection}'. Did you mean {suggestion_str}?")
            else:
                raise ValueError(f"Invalid key for collection '{collection}'. No similar keys found.")
        return v

    @field_validator('value')
    def validate_value(cls, v: str, info: ValidationInfo):
        collection = info.data.get('collection')
        key = info.data.get('key')
        if key:
            allowed_values = collection_data_frames[collection][key].astype(str).tolist()
            if v not in allowed_values:
                suggestions = cls.get_suggestions(v, allowed_values)
                if suggestions:
                    suggestion_str = " or ".join(f"'{s}'" for s in suggestions)
                    raise ValueError(f"Value '{v}' not found in the '{key}' column of the '{collection}' collection. Did you mean {suggestion_str}?")
                else:
                    raise ValueError(f"Value '{v}' not found in the '{key}' column of the '{collection}' collection.")
        return v

    @field_validator('columns')
    def validate_columns(cls, v: List[str], info: ValidationInfo):
        collection = info.data.get('collection')
        if collection is None:
            raise ValueError("Collection cannot be None.")
        
        allowed_collections = list(collection_data_frames.keys())
        if collection not in allowed_collections:
            suggestions = cls.get_suggestions(collection, allowed_collections)
            if suggestions:
                suggestion_str = " or ".join(f"'{s}'" for s in suggestions)
                raise ValueError(f"Invalid collection '{collection}'. Did you mean {suggestion_str}?")
            else:
                raise ValueError(f"Invalid collection '{collection}'. No similar collections found.")
        
        allowed_columns = list(collection_data_frames[collection].columns)
        invalid_columns = [col for col in v if col not in allowed_columns]
        if invalid_columns:
            suggestions = [cls.get_suggestions(col, allowed_columns)[:2] for col in invalid_columns]
            invalid_columns_with_suggestions = []
            for col, s in zip(invalid_columns, suggestions):
                if s:
                    suggestion_str = " or ".join(f"'{suggestion}'" for suggestion in s)
                    invalid_columns_with_suggestions.append(f"{col} (Did you mean {suggestion_str}?)")
                else:
                    invalid_columns_with_suggestions.append(col)
            raise ValueError(f"Invalid columns for collection '{collection}': {', '.join(invalid_columns_with_suggestions)}")
        
        # Add default columns if not already present
        default_columns = DEFAULT_COLUMNS.get(collection, [])
        missing_default_columns = [col for col in default_columns if col not in v]
        v.extend(missing_default_columns)
        
        return v

    @staticmethod
    def get_suggestions(value, options):
        suggestions = process.extract(value, options, limit=2)
        return [s[0] for s in suggestions if s[1] >= 50]

class SearchQuery(BaseModel):
    criteria: List[SearchCriteria]


class ValidateSearchQueryTool:
    openai_schema = {
        "name": "ValidateSearchQueryTool",
        "description": "Validates a search query against the Pydantic schemas and saves it to criteria.txt if valid",
        "parameters": {
            "type": "object",
            "properties": {
                "search_criteria": {"type": "string", "description": "Search criteria as a JSON string containing a list of dictionaries or a dictionary with a 'search_criteria' key"}
            },
            "required": ["search_criteria"]
        }
    }

    def __init__(self, search_criteria: str):
        self.search_criteria = search_criteria

    def run(self):
        try:
            errors = []

            # Parse the JSON string to a Python object
            search_criteria_obj = json.loads(self.search_criteria)
            
            # Check if it's a dictionary with a 'search_criteria' key
            if isinstance(search_criteria_obj, dict) and 'search_criteria' in search_criteria_obj:
                search_criteria_list = search_criteria_obj['search_criteria']
            elif isinstance(search_criteria_obj, list):
                search_criteria_list = search_criteria_obj
            else:
                raise ValueError("Invalid search criteria format")

            # Validate search query
            try:
                search_query = SearchQuery(criteria=[SearchCriteria(**criteria) for criteria in search_criteria_list])
            except ValidationError as e:
                error_messages = []
                for error in e.errors():
                    error_msg = f"{'.'.join(map(str, error['loc']))}: {error['msg']}"
                    error_messages.append(error_msg)
                errors.append("Invalid search query: " + "\n".join(error_messages))
            
            # # Extract the collection names
            # collection_names = [criteria['collection'] for criteria in search_criteria_list]

            # # Function to check if collection name appears as a column in the previous collection's DataFrame
            # def check_collection_name_in_columns(search_criteria_list, collection_data_frames):
            #     for i in range(1, len(search_criteria_list)):
            #         previous_collection = search_criteria_list[i - 1]['collection']
            #         current_collection = search_criteria_list[i]['collection']
                    
            #         # Access the columns of the previous collection
            #         previous_columns = collection_data_frames[previous_collection].columns
                    
            #         # Check if the current collection name is a column in the previous collection
            #         if current_collection not in previous_columns:
            #             # Use fuzzywuzzy to find the most similar columns
            #             similar_columns = process.extract(current_collection, previous_columns, limit=2)
            #             similar_column_names = [match[0] for match in similar_columns]
                        
            #             error_message = f"'{current_collection}' does not appear as a column in '{previous_collection}'."
            #             suggestion_message = f" Did you mean: {', '.join(similar_column_names)}?"
            #             raise ValueError(error_message + suggestion_message)
                    
            #         print(f"'{current_collection}' appears as a column in '{previous_collection}'")

            # # Check collection name in columns
            # try:
            #     check_collection_name_in_columns(search_criteria_list, collection_data_frames)
            # except ValueError as e:
            #     errors.append(str(e))

            # If there are any errors, return them
            if errors:
                return {"error": "\n".join(errors)}
            
            formatted_query = json.dumps(search_criteria_list, indent=2)

            # Save the formatted query to criteria.txt
            with open("criteria.txt", "w") as file:
                file.write(formatted_query)

            return {"output": "Search criteria validated successfully and saved to criteria.txt"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {str(e)}"}
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                error_msg = f"{'.'.join(map(str, error['loc']))}: {error['msg']}"
                error_messages.append(error_msg)
            return {"error": f"Invalid search query: {len(e.errors())} validation error(s)\n" + "\n".join(error_messages)}
        except Exception as e:
            error_message = str(e)
            print(f"Error in ValidateSearchQueryTool: {error_message}")
            return {"error": error_message}
        
# # Example usage:
# search_criteria_json = '''
# [
#   {"collection": "Users", "key": "Full Name", "value": "Willie Barron", "columns": ["id", "Full Name"]},
#   {"collection": "Tasks", "columns": ["id", "Task", "Date & Time (Created)", "Task Priority Level", "Progress status"]}
# ]
# '''

# tool = ValidateSearchQueryTool(search_criteria_json)
# result = tool.run()
# print(result)
