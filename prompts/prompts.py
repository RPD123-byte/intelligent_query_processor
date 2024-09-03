helpful_response_generator_prompt_template = """
    You are an AI assistant that provides helpful, detailed answers to user questions based on the given context.
"""

search_query_generator_prompt_template="""
    As a search and retrieve agent, your job is to take a user question and format it into a structured search query that adheres to the provided Pydantic schemas.

    The search query should be a Python list of dictionaries in the following format:

    search_criteria = [
        {{
            "collection": "Collection name",
            "columns": ["Column 1", "Column 2", ...]
        }},
        {{
            "collection": "Collection name",
            "key": "Key to search",
            "value": "Value to search for",
            "columns": ["Column 1", "Column 2", ...]
        }},
        ...
    ]

    The 'collection' field is required and should be obtained from the question.
    
    The 'columns' field is required and should contain a list of columns to retrieve for the specified collection.

    The 'key' and 'value' fields are optional and should only be included when a specific filter needs to be applied within a collection's DataFrame. If included, the 'key' field should be a valid column name in the specified collection, and the 'value' field should contain the corresponding value to search for.

    For example, for this question:

    "Contacts Jae Harrison, What are my ventures and what are the notes associated with those ventures and what other projects have those same notes associated with my ventures"

    a valid search query would look like this:

    [
        {{'collection': 'Contacts', 'key': 'Name', 'value': 'Jae Harrison', 'columns': ['id', 'Name', 'Email']}},
        {{'collection': 'Ventures', 'columns': ['id', 'Name']}},
        {{'collection': 'Notes', 'columns': ['id', 'Title']}},
        {{'collection': 'Projects', 'columns': ['id', 'Name', 'Description']}}
    ]

    We go in temporal order by starting with the contacts, then the ventures, then the notes associated with those ventures, and finally the projects associated with those notes as asked for in the question.

    These are your past runs and failures where your search criteria returned an error: {feedback}

    Based on the errors, change the search criteria to avoid those errors and provide the correct search criteria for the question.
"""

def get_search_query_generator_guided_json(collection_keys):
    return {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "collection": {
                    "type": "string",
                    "description": "The name of the collection to query",
                    "enum": collection_keys
                },
                "key": {
                    "type": "string",
                    "description": "The column name to filter by",
                    "minLength": 1
                },
                "value": {
                    "type": "string",
                    "description": "The value to filter by",
                    "minLength": 1
                },
                "columns": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": "A column to retrieve from the collection"
                    },
                    "minItems": 1
                }
            },
            "required": ["collection", "columns"],
            "anyOf": [
                {"required": ["key", "value"]},
                {"not": {"required": ["key", "value"]}}
            ]
        }
    }