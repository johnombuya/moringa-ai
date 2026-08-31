import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()
store = InMemoryVectorStore(OpenAIEmbeddings())
store.add_texts(["AfyaPlus reimburses staff travel within 30 days of an approved claim."])
retriever = store.as_retriever()

# In Lab 11 your prompt answered from {context}. Here the goal is stricter:
# the model must REFUSE when the answer is not in the context.
# Write the prompt so an out-of-scope question returns a fixed refusal phrase.
prompt = ChatPromptTemplate.from_template(
    "Answer using ONLY the context. If the answer is not in it, reply exactly: "
    "Information not found.\nContext: {context}\nQuestion: {question}"
)

llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0.0)
chain = ({"context": retriever, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())
print(chain.invoke("Best tourist beaches in Mombasa?"))   # should refuse