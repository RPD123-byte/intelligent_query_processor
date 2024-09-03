from agent_graph.graph import create_graph, compile_workflow
import pandas as pd
import io

# server = 'ollama'
# model = 'llama3:instruct'
# model_endpoint = None

server = 'openai'
model = 'gpt-3.5-turbo-1106'
model_endpoint = None

# server = 'vllm'
# model = 'meta-llama/Meta-Llama-3-70B-Instruct' # full HF path
# runpod_endpoint = 'https://t3o6jzhg3zqci3-8000.proxy.runpod.net/' 
# model_endpoint = runpod_endpoint + 'v1/chat/completions'
# stop = "<|end_of_text|>"

def load_collections_from_file(filename='collections.txt'):
    try:
        with open(filename, 'r') as file:
            content = file.read()

        collection_data_frames = {}
        sections = content.strip().split('\n\n')

        for section in sections:
            if section.strip() == '':
                continue
            
            lines = section.split('\n')
            if not lines[0].startswith("Collection: "):
                # print(f"Skipping malformed section:\n{section}")
                continue
            
            collection_name = lines[0].replace("Collection: ", "").strip()
            csv_data = "\n".join(lines[1:])
            
            if csv_data.strip() == '':
                # print(f"Empty CSV data for collection: {collection_name}")
                continue
            
            try:
                df = pd.read_csv(io.StringIO(csv_data))
                collection_data_frames[collection_name] = df
            except pd.errors.ParserError as e:
                # print(f"Error parsing CSV for collection '{collection_name}': {e}")
                continue

        return collection_data_frames

    except Exception as e:
        # print(f"Error loading collections from file: {e}")
        return {}

# Load the dictionary from the file
collection_data_frames = load_collections_from_file()

# Define collection_keys from the keys of the dictionary
collection_keys = list(collection_data_frames.keys())

iterations = 40
question = "What are my ventures"
print ("Creating graph and compiling workflow...")
graph = create_graph(server=server, model=model, model_endpoint=model_endpoint, question=question, collection_keys=collection_keys)
workflow = compile_workflow(graph)
print ("Graph and workflow created.")


if __name__ == "__main__":
    verbose = False

    while True:
        # query = input("Please enter your research question: ")
        # query = input("Are You Ready: ")
        query = "go"


        # if query.lower() == "exit":
        #     break

        dict_inputs = {"query_question": query}
        thread = {"configurable": {"thread_id": "4"}}
        limit = {"recursion_limit": iterations}

        # for event in workflow.stream(
        #     dict_inputs, thread, limit, stream_mode="values"
        #     ):
        #     if verbose:
        #         print("\nState Dictionary:", event)
        #     else:
        #         print("\n")

        for event in workflow.stream(
            dict_inputs, limit
            ):
            if verbose:
                print("\nState Dictionary:", event)
            else:
                print("\n")

    