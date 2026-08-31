from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

def run_deep_vector_retrieval():
    print("--- Executing K-Neighbor Depth Search ---")
    loader = TextLoader("./manual_data/operational_guidelines.txt")
    chunks = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20).split_documents(loader.load())
    vector_store = Chroma.from_documents(chunks, OpenAIEmbeddings(model="text-embedding-3-small"))

    # Set search limits to return top 3 contextual matches
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    target_query = "What happens during a Mombasa triage emergency?"
    matched_documents = retriever.invoke(target_query)

    print(f"Target Query: '{target_query}'")
    print(f"Retrieved {len(matched_documents)} context candidate blocks:")

    for position, doc in enumerate(matched_documents):
        print(f"\n[Rank Position {position + 1}]")
        print(f"Snippet text: {doc.page_content}")
        print("-" * 40)

if __name__ == "__main__":
    run_deep_vector_retrieval()