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

# redis_host = os.getenv('REDIS_HOST')
# redis_port = int(os.getenv('REDIS_PORT'))


# app.config["SESSION_TYPE"] = "redis"
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_USE_SIGNER"] = True
# app.config["SESSION_REDIS"] = Redis(host=redis_host, port=redis_port)
# app.config["SECRET_KEY"] = os.urandom(24)
CORS(app)

# email = os.getenv('EMAIL', 'your-email')
# password = os.getenv('PASSWORD', 'your-password')

# openai_api_key = os.getenv('OPENAI_API_KEY', 'your-openai-api-key')

# os.environ["OPENAI_API_KEY"] = openai_api_key

# client = openai.OpenAI(api_key=openai_api_key)



# def wprint(*args, width=70, **kwargs):
#     wrapper = textwrap.TextWrapper(width=width)
#     wrapped_args = [wrapper.fill(str(arg)) for arg in args]
#     builtins.print(*wrapped_args, **kwargs)

# def get_completion(message, agent, funcs, thread, client):
#     # Create new message in the thread
#     message_response = client.beta.threads.messages.create(
#         thread_id=thread.id,
#         role="user",
#         content=message
#     )

#     # Run the thread
#     run = client.beta.threads.runs.create(
#         thread_id=thread.id,
#         assistant_id=agent.id,
#     )

#     while True:
#         # Wait until run completes
#         run = client.beta.threads.runs.retrieve(
#             thread_id=thread.id,
#             run_id=run.id
#         )

#         if run.status in ['queued', 'in_progress']:
#             time.sleep(1)
#             continue

#         if run.status == "requires_action":
#             tool_calls = run.required_action.submit_tool_outputs.tool_calls
#             tool_outputs = []
#             for tool_call in tool_calls:
#                 print(f"Debug: Calling function {tool_call.function.name}", flush=True)

#                 wprint(f'\033[31mFunction: {tool_call.function.name}\033[0m')
#                 func = next((f for f in funcs if f.__name__ == tool_call.function.name), None)
#                 if func:
#                     try:
#                         # Assuming arguments are parsed correctly
#                         func_instance = func(**eval(tool_call.function.arguments))  # Consider safer alternatives to eval
#                         output = func_instance.run()

#                         # Ensure output is a string
#                         if not isinstance(output, str):
#                             output = str(output)
#                     except Exception as e:
#                         output = f"Error: {e}"
#                 else:
#                     output = "Function not found"
#                 wprint(f"\033[33m{tool_call.function.name}: {output}\033[0m")
#                 tool_outputs.append({"tool_call_id": tool_call.id, "output": output})

#             run = client.beta.threads.runs.submit_tool_outputs(
#                 thread_id=thread.id,
#                 run_id=run.id,
#                 tool_outputs=tool_outputs
#             )
#         elif run.status == "failed":
#             raise Exception(f"Run Failed. Error: {run.last_error}")
#         else:
#             messages = client.beta.threads.messages.list(
#                 thread_id=thread.id
#             )
#             latest_message = messages.data[0].content[0].text.value
#             return latest_message


# name_dict = {'Calendar-Items': 't_01e4oic3dm0qv3ivdqeakic01',
#  'Business-Service-Categories': 't_0de898ciie5ibdv7t2fwcv71h',
#  'Workspaces': 't_0gwestodatdl08kf82rkk78sm',
#  'Learning-Pathway': 't_0km0jyr8g8ciq2rplpwofzqxp',
#  'Ticket-Order': 't_0o1w63vz063oz3l1qmw2pb7rd',
#  'Business-Types': 't_0o4e5vudg3vrysai0vhwp5cq0',
#  'R-Tag-Types': 't_17uc9wg4busm8psqfswoc04lv',
#  'Event-Types': 't_1b66dhxyqbeikhbrxzz80zk2j',
#  'Ventures': 't_1cev2vfm50bgqrpu5mapbwzs9',
#  'Notes': 't_1fa8j8qpsyo7abacb8crgrru8',
#  'PITCH-Categories': 't_1odhlh9x26hsa4hay42etpwp4',
#  'Folder-Types': 't_1pvu33tuxfifslmgu0rx6f1vu',
#  'Network-Categories': 't_1tpvl7kevjx9q4dzju4ipc2og',
#  'Stages': 't_278fmtdg3xvki7cnc57qm21ad',
#  'Documents': 't_27nks5dd1zfd2zr83zrcp2b1e',
#  'Restaurants': 't_29psvs8nx3ypzci0p7jads03a',
#  'R-Recipes': 't_2iksqwpi091j2zqkqxegvt1pv',
#  'Tasks': 't_2ilemt0nzggoqyd33a4tvdykw',
#  'Accounts': 't_2km30340l6z097079o3qrvyy0',
#  'Task-Progress-status': 't_2ntztt6q3026zuy9bmq1aoy9y',
#  'Shopping-List-Items': 't_3070hgrexxffnn86556vo5aj6',
#  'Contacts': 't_34metj279n5oazpgpec7w8mr2',
#  'Platforms': 't_37ab19s1hbnxfjyfofc4zgljy',
#  'Chats': 't_3db7sd22qoxglk1fx9k7yb5wa',
#  'Portfolio-Items': 't_3doycs9u7utg5e55sn583pi0i',
#  'Tags': 't_3o5g5bsu2xkcye8vtm2re6yf7',
#  'Enterprises': 't_3wmfhd0kdwubffsxjitsqfsvx',
#  'Vendor-Types': 't_4b90o1vsr12sjvsr5n19ln702',
#  'Media': 't_4euoafm6u51pzg2irlthiv3fl',
#  'Announcements': 't_4mc893jr58brwq3eeink8799o',
#  'User-Industry-Points': 't_4xbqn7sczyzjz6ex6wgc3npav',
#  'Skills': 't_50pw0u4um72bnhplv4zdlcuab',
#  'Memory-Media': 't_52pxknpeezm3l8j79zrp8qa9l',
#  'Event-NotesUpdates': 't_5a87tbj5prxu00gl9ndh1h707',
#  'Space-Features': 't_5d29je1nfxa41xfjwqyqokcg8',
#  'Communities': 't_5lx5693i4ihlnhqv3av3f7sej',
#  'Conversations': 't_5pj8emb33gia50r18y1n1id85',
#  'Status-Log': 't_5pvmznp47yexflf1l70yp787w',
#  'Events': 't_5y6vs81mvi78syquilzf7jfae',
#  'Venture-Media': 't_6114sdqa4it1diw94jvygowhx',
#  'Statuses': 't_66lb8dvgqm1teah5cn7giviqu',
#  'Service-Requests': 't_66w5dnzmmb1tl2o4fenwt5w8p',
#  'Venture-Team-Members': 't_67zcxzgr40zuo27kulhmuhdi7',
#  'Ticket-Options': 't_69dlc2nzu8jvsfexgen1lerg8',
#  'User-Subcategory-Points': 't_6a23683xih50h9chxkn7rgz0m',
#  'Industry-Subcategories': 't_6per6jq63458336w3erwf6uk2',
#  'Discount-Codes': 't_6sphbnvbrh5a4sldq6ayjsquu',
#  'Resources': 't_6xm9t25icmu9j9ye80m531d3q',
#  'Receipts': 't_726bmzsfkngd7vwki2f8kauqy',
#  'Discount-Types': 't_75lbsvpknypeb6e1rq5pyg63i',
#  'Contact-Types': 't_775z4kvtqofgy03dlgsb093ri',
#  'Business-Services': 't_7hyyk7ytp20bpcqr9nxkh0bnm',
#  'Rental-Rates': 't_7l8ud8cj7xkaohnx3ymati0ye',
#  'Message-Attachment-Types': 't_7rzpt3wwqixzxn86l2sejsr57',
#  'Calendar-Item-Types': 't_7vgaa22fcuqmwg85m254vcmg7',
#  'First-Contact': 't_8334d2001xffvle0asdz7xk3f',
#  'App-Photos': 't_84s1srrhi9if5gnyy8spd9rxo',
#  'R-Ingredients': 't_8cqlwze29qpt3t84lkrvsqs4d',
#  'PITCH-Subcategories': 't_8djc0qqejj7zfsuml1udta1t2',
#  'Objectives': 't_8f620pjq5ybsnvjimvqbijr16',
#  'Badge-Levels': 't_8r5ah7zwe3gncizehkhtq3mky',
#  'Company-Branches': 't_8vuhaxo9ba0cq2z0up1us3vsf',
#  'Revenues': 't_9mya3hxnpap592td3ovtr60yo',
#  'Memories': 't_9o41gzmoghsrcsbd4fd3j1j9q',
#  'Task-Requests': 't_9uqpxv6uvn6lzs5pxuck8y07w',
#  'Vendors': 't_9ykvi0nxitpcwx34mcacj9v3p',
#  'Event-Line-Items': 't_a0pl59fyk9tuv31anzsigdb5m',
#  'Note-Types': 't_a1da56bf3rx4mtmwigsy71e60',
#  'Expense-Types': 't_agno5ywvzpe516ts2xo3p5zsq',
#  'Availability-Status': 't_alh1v8k71crp0kq802u54llzc',
#  'Learning-Modules': 't_b29v4zihe3v1wbkx0qemv9ghw',
#  'R-Tags': 't_b5ldf9r90knd8ncgwq10u5sbl',
#  'A-Tags': 't_ban7278z8h3kl06zmar5jgxx8',
#  'Goal-Stage': 't_bd6lnxdo13qx66on7ywy30108',
#  'Service-Request-Responses': 't_bh8ycnnxf6l6bc0c7730cmtob',
#  'Conversation-Log': 't_btz02pd3ygp3lfeejfg8ssb46',
#  'Links': 't_bwooqzxyamlofqhftd540ghgq',
#  'Resource-Categories': 't_c5aatk6aqdyc816bqaux5rqc0',
#  'GEORGE-REWARDS': 't_c8zmf1v0byddjhw5sw95nvxtp',
#  'Projects': 't_caga69lroozt9ad0fwcawzouc',
#  'General-Ledger-Category': 't_ccd7lmzls1b1ca2zcfku5dghv',
#  'Income-Statements': 't_cek3vjz2e3bb4r9795eu3ngum',
#  'Resource-Types': 't_cf9od3bjvkhrdmxttrvrg9uve',
#  'Pathway-Stages': 't_cholvp3ocp70si4xpm4ztzbth',
#  'Goal-Checkpoints': 't_ck4bs2s3g3h8xmkus2920o60t',
#  'Event-Inquiries': 't_cm6s5xgv2cxc5y6gdhec4c7h1',
#  'Folders': 't_cmlqvy5jhwn336av7iz1adezv',
#  'Event-Status': 't_cnwwdv77dc6714h9ardn0lp2z',
#  'Messages': 't_cocryk4tc4rtiicouiddw7cll',
#  'Portfolio-Projects': 't_ctkbcpg724om7mskizcia45j4',
#  'Task-Types': 't_cz3myju92n5uj9tfr236alzv5',
#  'Goals': 't_d1z3ejlq5ajcu03syiatggmwd',
#  'Ticket-Email': 't_d51oo1vfcgd07fhq5rt4jbu1k',
#  'Industries': 't_de8wgj3p6aivaplglozs45jb7',
#  'Tag-Types': 't_dfn5g220zr76nc0nq3sosmkxq',
#  'Spaces': 't_dfq4bey5ezx97yzyk2v73vp0r',
#  'User-Types': 't_dgrhrh7qjyxdeknbtnc6wi8kw',
#  'A-Activities': 't_dkcvop4d01t2g1es03wh7bopk',
#  'Individual-Tickets': 't_dlsy1f32w3hvtl7cl6qw8hdur',
#  'Badges': 't_dw5yhzbnaqvyd5d5webq27zsc',
#  'Enterprise-Categories': 't_dy8l543yxx6qacx6d6wr1giaz',
#  'Job-Opportunities': 't_e7q5nsm6cjuqtyopdcmjqkx10',
#  'General-Ledger-Location': 't_edo77gxfh35o9tsyoq9gi34v6',
#  'App-Videos': 't_eezol54iic5ltltki34mbhyow',
#  'Message-Attachments': 't_ehhvbt2ji5k9owxusjy0s4g8c',
#  'Progress-Updates': 't_ern3ozxv56i3ruq29dmi41i8e',
#  'Priority-Level': 't_ex9234t5008gvlq7kv4jinxqc',
#  'Explore-Categories': 't_eyx8vtk78ksw51ohvh37z55kc',
#  'Expenses': 't_f52q8dr8f2pdi4wlvuruspydy',
#  'Restaurant-Menu-Items': 't_3ba53d188c5b473aa34306ce2049a54c',
#  'Restaurant-Order-Items': 't_72c75109a42b44bb9af7647f1e2fee05',
#  'Restaurant-Orders': 't_785b98664c0c4815967e7af4cbd0197d',
#  'Users': 't_97b4ac4593744e08ba67c27823ae52f7',
#  'Channel-Messages': 't_a0e210fa6e924ffb8a9030a5cdfb832e',
#  'Channels': 't_aa80afb4f1e548dcae283e4f5d27ac20',
#  'Restaurant-Tip-Percentages': 't_aefe560968fb4bfab7a9418a64e47b13',
#  'Restaurant-Menu-Categories': 't_f1891718f3fb422cbcdeabbdb41de956'}

# def fetch_adalo_collection(api_url, headers, params):
#     try:
#         # Make GET request to the Adalo API endpoint
#         response = requests.get(api_url, headers=headers, params=params)
#         response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
#         return response.json()  # Parse JSON response into a Python dictionary
#     except requests.RequestException as error:
#         print(f"Error fetching data: {error}")
#         return None

# def fetch_all_collections(name_dict):
#     data_frames = {}  # Dictionary to store title and DataFrame pairs

#     for key, value in name_dict.items():
#         # API credentials and URL
#         API_URL = f"https://api.adalo.com/v0/apps/ee7c3b25-44f3-41a5-8efb-e76ac0ad72b2/collections/{value}"
#         API_KEY = "2d5m8hgasmssfth1z1r16wo3w"

#         # Headers required for the API request
#         HEADERS = {
#             "Content-Type": "application/json",
#             "Authorization": f"Bearer {API_KEY}"
#         }

#         # Query parameters for pagination
#         PARAMS = {
#             "offset": 0,
#             "limit": 100
#         }

#         # Fetch data from the Adalo API
#         adalo_data = fetch_adalo_collection(API_URL, HEADERS, PARAMS)
#         if adalo_data is not None:
#             # Convert the 'records' list to a DataFrame
#             df = pd.DataFrame(adalo_data['records'])
#             data_frames[key] = df  # Store DataFrame in dictionary under its collection name

#     return data_frames

# def save_collection_data_frames(data_frames, filename='collection_data_frames.pkl'):
#     with open(filename, 'wb') as file:
#         pickle.dump(data_frames, file)


# collection_data_frames = fetch_all_collections(name_dict)
# save_collection_data_frames(collection_data_frames)

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


# DEFAULT_COLUMNS = {
#     'Calendar-Items': ['id', 'Name', 'Date', 'Start Date & Time', 'End Date & Time'],
#     'Business-Service-Categories': ['id', 'Name'],
#     'Workspaces': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Learning-Pathway': ['id', 'Name', 'Date', 'Notes'],
#     'Ticket-Order': ['id', 'Name', 'Date', 'Start Date & Time', 'End Date & Time'],
#     'Business-Types': ['id', 'Name'],
#     'R-Tag-Types': ['id', 'Name'],
#     'Event-Types': ['id', 'Name'],
#     'Ventures': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Notes': ['id', 'Name', 'Date', 'Notes'],
#     'PITCH-Categories': ['id', 'Name'],
#     'Folder-Types': ['id', 'Name'],
#     'Network-Categories': ['id', 'Name'],
#     'Stages': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Documents': ['id', 'Name', 'Date', 'Notes'],
#     'Restaurants': ['id', 'Name', 'Date', 'Is Complete?'],
#     'R-Recipes': ['id', 'Name', 'Date', 'Notes'],
#     'Tasks': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Accounts': ['id', 'Name'],
#     'Task-Progress-status': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Shopping-List-Items': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Contacts': ['id', 'Name'],
#     'Platforms': ['id', 'Name'],
#     'Chats': ['id', 'Name', 'Date', 'Notes'],
#     'Portfolio-Items': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Tags': ['id', 'Name'],
#     'Enterprises': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Vendor-Types': ['id', 'Name'],
#     'Media': ['id', 'Name', 'Date', 'Notes'],
#     'Announcements': ['id', 'Name', 'Date', 'Notes'],
#     'User-Industry-Points': ['id', 'Name'],
#     'Skills': ['id', 'Name'],
#     'Memory-Media': ['id', 'Name', 'Date', 'Notes'],
#     'Event-NotesUpdates': ['id', 'Name', 'Date', 'Notes'],
#     'Space-Features': ['id', 'Name'],
#     'Communities': ['id', 'Name'],
#     'Conversations': ['id', 'Name', 'Date', 'Notes'],
#     'Status-Log': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Events': ['id', 'Name', 'Date', 'Start Date & Time', 'End Date & Time'],
#     'Venture-Media': ['id', 'Name', 'Date', 'Notes'],
#     'Statuses': ['id', 'Name'],
#     'Service-Requests': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Venture-Team-Members': ['id', 'Name'],
#     'Ticket-Options': ['id', 'Name', 'Date', 'Start Date & Time', 'End Date & Time'],
#     'User-Subcategory-Points': ['id', 'Name'],
#     'Industry-Subcategories': ['id', 'Name'],
#     'Discount-Codes': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Resources': ['id', 'Name', 'Date', 'Notes'],
#     'Receipts': ['id', 'Name', 'Date', 'Notes'],
#     'Discount-Types': ['id', 'Name'],
#     'Contact-Types': ['id', 'Name'],
#     'Business-Services': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Rental-Rates': ['id', 'Name', 'Date', 'Notes'],
#     'Message-Attachment-Types': ['id', 'Name'],
#     'Calendar-Item-Types': ['id', 'Name'],
#     'First-Contact': ['id', 'Name', 'Date', 'Notes'],
#     'App-Photos': ['id', 'Name', 'Date', 'Notes'],
#     'R-Ingredients': ['id', 'Name', 'Date', 'Notes'],
#     'PITCH-Subcategories': ['id', 'Name'],
#     'Objectives': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Badge-Levels': ['id', 'Name'],
#     'Company-Branches': ['id', 'Name'],
#     'Revenues': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Memories': ['id', 'Name', 'Date', 'Notes'],
#     'Task-Requests': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Vendors': ['id', 'Name'],
#     'Event-Line-Items': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Note-Types': ['id', 'Name'],
#     'Expense-Types': ['id', 'Name'],
#     'Availability-Status': ['id', 'Name'],
#     'Learning-Modules': ['id', 'Name', 'Date', 'Is Complete?'],
#     'R-Tags': ['id', 'Name'],
#     'A-Tags': ['id', 'Name'],
#     'Goal-Stage': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Service-Request-Responses': ['id', 'Name', 'Date', 'Notes'],
#     'Conversation-Log': ['id', 'Name', 'Date', 'Notes'],
#     'Links': ['id', 'Name'],
#     'Resource-Categories': ['id', 'Name'],
#     'GEORGE-REWARDS': ['id', 'Name'],
#     'Projects': ['id', 'Name', 'Date', 'Is Complete?'],
#     'General-Ledger-Category': ['id', 'Name'],
#     'Income-Statements': ['id', 'Name', 'Date', 'Notes'],
#     'Resource-Types': ['id', 'Name'],
#     'Pathway-Stages': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Goal-Checkpoints': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Event-Inquiries': ['id', 'Name', 'Date', 'Notes'],
#     'Folders': ['id', 'Name'],
#     'Event-Status': ['id', 'Name'],
#     'Messages': ['id', 'Name', 'Date', 'Notes'],
#     'Portfolio-Projects': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Task-Types': ['id', 'Name'],
#     'Goals': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Ticket-Email': ['id', 'Name', 'Date', 'Notes'],
#     'Industries': ['id', 'Name'],
#     'Tag-Types': ['id', 'Name'],
#     'Spaces': ['id', 'Name'],
#     'User-Types': ['id', 'Name'],
#     'A-Activities': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Individual-Tickets': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Badges': ['id', 'Name'],
#     'Enterprise-Categories': ['id', 'Name'],
#     'Job-Opportunities': ['id', 'Name', 'Date', 'Is Complete?'],
#     'General-Ledger-Location': ['id', 'Name'],
#     'App-Videos': ['id', 'Name', 'Date', 'Notes'],
#     'Message-Attachments': ['id', 'Name', 'Date', 'Notes'],
#     'Progress-Updates': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Priority-Level': ['id', 'Name'],
#     'Explore-Categories': ['id', 'Name'],
#     'Expenses': ['id', 'Name', 'Date', 'Notes'],
#     'Restaurant-Menu-Items': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Restaurant-Order-Items': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Restaurant-Orders': ['id', 'Name', 'Date', 'Is Complete?'],
#     'Users': ['id', 'Name'],
#     'Channel-Messages': ['id', 'Name', 'Date', 'Notes'],
#     'Channels': ['id', 'Name'],
#     'Restaurant-Tip-Percentages': ['id', 'Name'],
#     'Restaurant-Menu-Categories': ['id', 'Name'],
# }


# class SearchCriteria(BaseModel):
#     collection: str
#     key: Optional[str] = None
#     value: Optional[str] = None
#     columns: List[str] = []

#     @field_validator('collection')
#     def validate_collection(cls, v: str, info: ValidationInfo):
#         allowed_collections = list(collection_data_frames.keys())
#         if v not in allowed_collections:
#             suggestions = cls.get_suggestions(v, allowed_collections)
#             if suggestions:
#                 suggestion_str = " or ".join(f"'{s}'" for s in suggestions)
#                 raise ValueError(f"Invalid collection '{v}'. Did you mean {suggestion_str}?")
#             else:
#                 raise ValueError(f"Invalid collection '{v}'. No similar collections found.")
#         return v

#     @field_validator('key')
#     def validate_key(cls, v: str, info: ValidationInfo):
#         collection = info.data.get('collection')
#         allowed_keys = list(collection_data_frames[collection].columns)
#         if v and v not in allowed_keys:
#             suggestions = cls.get_suggestions(v, allowed_keys)
#             if suggestions:
#                 suggestion_str = " or ".join(f"'{s}'" for s in suggestions)
#                 raise ValueError(f"Invalid key for collection '{collection}'. Did you mean {suggestion_str}?")
#             else:
#                 raise ValueError(f"Invalid key for collection '{collection}'. No similar keys found.")
#         return v

#     @field_validator('value')
#     def validate_value(cls, v: str, info: ValidationInfo):
#         collection = info.data.get('collection')
#         key = info.data.get('key')
#         if key:
#             allowed_values = collection_data_frames[collection][key].astype(str).tolist()
#             if v not in allowed_values:
#                 suggestions = cls.get_suggestions(v, allowed_values)
#                 if suggestions:
#                     suggestion_str = " or ".join(f"'{s}'" for s in suggestions)
#                     raise ValueError(f"Value '{v}' not found in the '{key}' column of the '{collection}' collection. Did you mean {suggestion_str}?")
#                 else:
#                     raise ValueError(f"Value '{v}' not found in the '{key}' column of the '{collection}' collection.")
#         return v

#     @field_validator('columns')
#     def validate_columns(cls, v: List[str], info: ValidationInfo):
#         collection = info.data.get('collection')
#         if collection is None:
#             raise ValueError("Collection cannot be None.")
        
#         allowed_collections = list(collection_data_frames.keys())
#         if collection not in allowed_collections:
#             suggestions = cls.get_suggestions(collection, allowed_collections)
#             if suggestions:
#                 suggestion_str = " or ".join(f"'{s}'" for s in suggestions)
#                 raise ValueError(f"Invalid collection '{collection}'. Did you mean {suggestion_str}?")
#             else:
#                 raise ValueError(f"Invalid collection '{collection}'. No similar collections found.")
        
#         allowed_columns = list(collection_data_frames[collection].columns)
#         invalid_columns = [col for col in v if col not in allowed_columns]
#         if invalid_columns:
#             suggestions = [cls.get_suggestions(col, allowed_columns)[:2] for col in invalid_columns]
#             invalid_columns_with_suggestions = []
#             for col, s in zip(invalid_columns, suggestions):
#                 if s:
#                     suggestion_str = " or ".join(f"'{suggestion}'" for suggestion in s)
#                     invalid_columns_with_suggestions.append(f"{col} (Did you mean {suggestion_str}?)")
#                 else:
#                     invalid_columns_with_suggestions.append(col)
#             raise ValueError(f"Invalid columns for collection '{collection}': {', '.join(invalid_columns_with_suggestions)}")
        
#         # Add default columns if not already present
#         default_columns = DEFAULT_COLUMNS.get(collection, [])
#         missing_default_columns = [col for col in default_columns if col not in v]
#         v.extend(missing_default_columns)
        
#         return v

#     @staticmethod
#     def get_suggestions(value, options):
#         suggestions = process.extract(value, options, limit=2)
#         return [s[0] for s in suggestions if s[1] >= 50]

# class SearchQuery(BaseModel):
#     criteria: List[SearchCriteria]

# class ValidateSearchQueryTool:
#     openai_schema = {
#         "name": "ValidateSearchQueryTool",
#         "description": "Validates a search query against the Pydantic schemas and saves it to criteria.txt if valid",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "search_criteria": {"type": "string", "description": "Search criteria as a Python list of dictionaries"}
#             },
#             "required": ["search_criteria"]
#         }
#     }

#     def __init__(self, search_criteria: str):
#         self.search_criteria = search_criteria

#     def run(self):
#         try:
#             search_criteria_obj = eval(self.search_criteria)
#             search_query = SearchQuery(criteria=search_criteria_obj)
#             formatted_query = "[\n"
#             for criteria in search_query.criteria:
#                 formatted_criteria = "  {"
#                 formatted_criteria += f"'collection': '{criteria.collection}'"
#                 if criteria.key:
#                     formatted_criteria += f", 'key': '{criteria.key}'"
#                 if criteria.value:
#                     formatted_criteria += f", 'value': '{criteria.value}'"
#                 formatted_criteria += f", 'columns': {criteria.columns}"
#                 formatted_criteria += "},\n"
#                 formatted_query += formatted_criteria
#             formatted_query += "]\n"

#             # Save the formatted query to criteria.txt
#             with open("criteria.txt", "w") as file:
#                 file.write(formatted_query)

#             return {"output": "Search criteria validated successfully and saved to criteria.txt"}
#         except ValidationError as e:
#             error_messages = []
#             for error in e.errors():
#                 error_msg = f"{error['loc'][0]}.{error['loc'][1]}\n {error['msg']}"
#                 error_messages.append(error_msg)
#             return {"error": f"Invalid search query: {len(e.errors())} validation error(s)\n" + "\n".join(error_messages)}
#         except Exception as e:
#             error_message = str(e)
#             print(f"Error in ValidateSearchQueryTool: {error_message}")
#             return {"error": error_message}


# search_and_retrieve_tools = [ValidateSearchQueryTool]

collection_keys = repr(collection_data_frames.keys())

# search_and_retrieve_agent = client.beta.assistants.create(
#     name='Search and Retrieve Agent',
#     instructions=f"""
#     As a search and retrieve agent, your job is to take a user question and format it into a structured search query that adheres to the provided Pydantic schemas.

#     The search query should be a Python list of dictionaries in the following format:

#     search_criteria = [
#         {{
#             "collection": "Collection name",
#             "columns": ["Column 1", "Column 2", ...]
#         }},
#         {{
#             "collection": "Collection name",
#             "key": "Key to search",
#             "value": "Value to search for",
#             "columns": ["Column 1", "Column 2", ...]
#         }},
#         ...
#     ]

#     The 'collection' field is required and should be one of the allowed collections: {collection_keys}.
    
#     The 'columns' field is required and should contain a list of columns to retrieve for the specified collection.

#     The 'key' and 'value' fields are optional and should only be included when a specific filter needs to be applied within a collection's DataFrame. If included, the 'key' field should be a valid column name in the specified collection, and the 'value' field should contain the corresponding value to search for.

#     For example, for this question:

#     "Contacts Jae Harrison, What are my ventures and what are the notes associated with those ventures and what other projects have those same notes associated with my ventures"

#     a valid search query would look like this:

#     [
#         {{'collection': 'Contacts', 'key': 'Name', 'value': 'Jae Harrison', 'columns': ['id', 'Name', 'Email']}},
#         {{'collection': 'Ventures', 'columns': ['id', 'Name']}},
#         {{'collection': 'Notes', 'columns': ['id', 'Title']}},
#         {{'collection': 'Projects', 'columns': ['id', 'Name', 'Description']}}
#     ]

#     We go in temporal order by starting with the contacts, then the ventures, then the notes associated with those ventures, and finally the projects associated with those notes as asked for in the question.

#     Once you have created the structured search query, validate it using the provided 'ValidateSearchQueryTool' function.

#     If the validation passes, print out the validated search query.

#     If the validation fails, revise the search query and ensure it follows the required format and constraints.

#     After the first successful run of the 'ValidateSearchQueryTool' function, always END THE RUN.
#     """,
#     model="gpt-3.5-turbo-1106",
#     # model="gpt-4-turbo",
#     tools=[{"type": "function", "function": ValidateSearchQueryTool.openai_schema}]
# )

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

