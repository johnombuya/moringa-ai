import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0.3)

prompt = ChatPromptTemplate.from_template(
    "Draft a one-sentence administrative acknowledgement for an AfyaPlus patient about: {topic}"
)
parser = StrOutputParser()

chain = prompt | llm | parser   # the LCEL pipe

result = chain.invoke({"topic": "a delayed lab result"})
print(result)