from flask import Flask, request, jsonify, session
import openai
import pandas as pd
import textwrap
import builtins
import time
import json
import requests
import os
from typing import List, Tuple
from pydantic import BaseModel, field_validator, ValidationError, ValidationInfo
from typing import List, Optional
from fuzzywuzzy import process
from flask_session import Session
from redis import Redis
from flask_cors import CORS
import ast
from agent_graph.graph import create_graph, compile_workflow
from utils.helper_functions import load_config
from models.openai_models import get_open_ai
import pickle
from datetime import datetime

app = Flask(__name__)

def load_collection_data_frames(filename='collection_data_frames.pkl'):
    with open(filename, 'rb') as file:
        data_frames = pickle.load(file)
    return data_frames

collection_data_frames = load_collection_data_frames()



def search_data(search_criteria, collection_data_frames, result=None, visited=None):
    try:
        if result is None:
            result = {}
        if visited is None:
            visited = set()
        
        if not search_criteria:
            return result
        
        current_search = search_criteria[0]
        collection_name = current_search['collection']
        search_key = current_search.get('key')
        search_value = current_search.get('value')
        columns = current_search.get('columns', ['id', 'Name'])
        
        if collection_name not in collection_data_frames:
            return result
        
        collection_df = collection_data_frames[collection_name]
        
        if search_key and search_value:
            search_results = collection_df[collection_df[search_key] == search_value]
        else:
            search_results = collection_df
        
        if len(search_results) == 0:
            return result
        
        for _, row in search_results.iterrows():
            row_data = row.to_dict()
            row_id = (collection_name, row_data['id'])
            if row_id not in visited:
                visited.add(row_id)
                item_data = {col: row_data.get(col) for col in columns if col in row_data}
                
                if len(search_criteria) > 1:
                    next_searches = search_criteria[1:]
                    next_search = next_searches[0]
                    next_collection = next_search['collection']
                    next_columns = next_search.get('columns', ['id', 'Name'])
                    
                    # Check for non-plural version of the column name
                    next_collection_singular = next_collection[:-1] if next_collection.endswith('s') else next_collection
                    if next_collection_singular in row_data:
                        next_search_ids = row_data[next_collection_singular]
                    elif next_collection in row_data:
                        next_search_ids = row_data[next_collection]
                    else:
                        next_search_ids = None
                    
                    if next_search_ids is not None:
                        if isinstance(next_search_ids, list):
                            item_data[next_collection] = []
                            for search_id in next_search_ids:
                                next_search_criteria = [{'collection': next_collection, 'key': 'id', 'value': search_id, 'columns': next_columns}] + next_searches[1:]
                                next_result = search_data(next_search_criteria, collection_data_frames, {}, visited)
                                if next_result:
                                    item_data[next_collection].append(next_result[next_collection][0])
                        else:
                            next_search_criteria = [{'collection': next_collection, 'key': 'id', 'value': next_search_ids, 'columns': next_columns}] + next_searches[1:]
                            next_result = search_data(next_search_criteria, collection_data_frames, {}, visited)
                            if next_result:
                                item_data[next_collection] = next_result[next_collection][0]
                
                if collection_name not in result:
                    result[collection_name] = [item_data]
                else:
                    result[collection_name].append(item_data)
        
        return result
    except Exception as e:
        print(f"Error in search_data: {str(e)}")
        return ""

collection_keys = repr(collection_data_frames.keys())


def generate_response(context, question):
    system_instructions = """
    You are an AI assistant that provides helpful, detailed answers to user questions based on the given context.
    """

    user_prompt = f"""
    Context:
    {context}

    Question: {question}

    A:
    """

    try:
        # Get the OpenAI model
        llm = get_open_ai(temperature=0.7, model="gpt-3.5-turbo-1106")  # or "gpt-3.5-turbo-1106"

        # Create messages
        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_prompt}
        ]

        # Generate response
        response = llm.invoke(messages)

        # Extract the content from the response
        return response.content.strip()

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/ask', methods=['POST'])
def ask():
    try:
        server = 'openai'
        # model = 'gpt-3.5-turbo-1106'
        model = 'gpt-4o'
        model_endpoint = None
        iterations = 20

        start_time = time.time()
        
        data = request.json
        user_name = data.get('user_name')
        user_id = data.get('user_id')
        question = data.get('question')
        key_value_dict = data.get('key_value_dict')


        # Check if required fields are present
        if not user_name:
            return jsonify({"error": "User name is required"}), 400
        if not question:
            return jsonify({"error": "Question is required"}), 400

        collection_keys = repr(collection_data_frames.keys())

        graph = create_graph(server=server, model=model, model_endpoint=model_endpoint, question=question, collection_keys=collection_keys, user_name=user_name)
        
        workflow = compile_workflow(graph)
        
        limit = {"recursion_limit": iterations}
        dict_inputs = {"query_question": question}

        verbose = False

        for event in workflow.stream(dict_inputs, limit):
            if verbose:
                print("\nState Dictionary:", event)
            else:
                print("\n")


        with open("criteria.txt", "r") as file:
            search_criteria_str = file.read()
        
        search_criteria = ast.literal_eval(search_criteria_str)
        
        user_criteria = {'collection': 'Users', 'key': 'Full Name', 'value': user_name, 'columns': ['id', 'Full Name']}
        
        if user_criteria not in search_criteria:
            search_criteria.insert(0, user_criteria)
                    
        with open("criteria.txt", "w") as file:
            file.write("[\n")
            for i, criteria in enumerate(search_criteria):
                file.write(f"  {criteria}")
                if i < len(search_criteria) - 1:
                    file.write(",\n")
                else:
                    file.write("\n")
            file.write("]\n")

        result = search_data(search_criteria, collection_data_frames)

        context = f"Q: {question}\nConversation History: {key_value_dict}\nRelevant Info to answer Q: {result}\n"

        response = generate_response(context, question)

        elapsed_time = time.time() - start_time
        print(f"Elapsed time: {elapsed_time:.2f} seconds")

        response_data = {
            "response": response
        }

        return jsonify(response_data)
    except Exception as e:
        error_message = str(e)
        print(f"Error in /ask endpoint: {error_message}")
        return jsonify({"error": error_message}), 400

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=4000)
    app.run(debug=True, port=4000)

